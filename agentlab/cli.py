from __future__ import annotations

import argparse
import shlex
import sys
import tempfile
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Iterable, List

from agentlab.agents.codex_cli import (
    CodexCliAdapter,
    CodexCliConfig,
    run_codex_preflight,
)
from agentlab.agents.manual import ManualAgentAdapter
from agentlab.evidence import render_evidence_appendix
from agentlab.reference import (
    ReferenceVerification,
    ReferenceVerificationError,
    verify_reference,
)
from agentlab.review import FAILURE_LABELS, load_review, resolve_run_dir, write_review
from agentlab.results import discover_result_files, load_results
from agentlab.runner import run_task
from agentlab.summary import summarize_trials
from agentlab.tasks import TaskLoadError, discover_task_files, load_task
from agentlab.terminal import ProgressBar, print_error
from agentlab.validity import (
    DEFAULT_TRIAL_VALIDITY,
    EXCLUDED_TRIAL_VALIDITY,
    EXCLUSION_REASONS,
    TRIAL_VALIDITIES,
    exclusion_reason,
    trial_validity,
)


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 2

    return args.handler(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentlab",
        description="Evaluate coding agents on reproducible software tasks.",
    )
    subcommands = parser.add_subparsers(dest="command")

    task_parser = subcommands.add_parser("task", help="Task definition commands.")
    task_subcommands = task_parser.add_subparsers(dest="task_command")

    validate_parser = task_subcommands.add_parser(
        "validate",
        help="Validate one or more task YAML files.",
    )
    validate_parser.add_argument(
        "paths",
        nargs="+",
        help=(
            "Task files, task bundle directories, or glob patterns, "
            "such as tasks/starter or tasks/starter/*/task.yaml."
        ),
    )
    validate_parser.set_defaults(handler=handle_task_validate)

    verify_reference_parser = task_subcommands.add_parser(
        "verify-reference",
        help="Apply verified reference artifacts and run task graders.",
    )
    verify_reference_parser.add_argument(
        "paths",
        nargs="+",
        help=(
            "Task files, task bundle directories, suite directories, or glob "
            "patterns to verify."
        ),
    )
    verify_reference_parser.add_argument(
        "--workspace-root",
        default=None,
        help=(
            "Optional directory for verification workspaces. Defaults to a "
            "temporary directory that is removed after verification."
        ),
    )
    verify_reference_parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip tasks that do not declare reference_artifact.",
    )
    verify_reference_parser.add_argument(
        "--no-write-artifacts",
        action="store_false",
        dest="write_artifacts",
        help=(
            "Do not write reference-report.md, reference-result.json, or "
            "reference.diff next to each task.yaml."
        ),
    )
    verify_reference_parser.set_defaults(handler=handle_task_verify_reference)

    smoke_test_parser = task_subcommands.add_parser(
        "smoke-test",
        help="Verify a task reference artifact, then run exactly one agent trial.",
    )
    smoke_test_parser.add_argument(
        "--task",
        required=True,
        help="Task YAML file or task bundle directory to smoke-test.",
    )
    smoke_test_parser.add_argument(
        "--agent",
        default="manual",
        choices=["manual", "codex"],
        help="Agent backend to use for the one-trial smoke test.",
    )
    smoke_test_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where smoke-test trial artifacts should be written.",
    )
    smoke_test_parser.add_argument(
        "--no-pause",
        action="store_true",
        help="For the manual agent, do not wait for human edits.",
    )
    smoke_test_parser.add_argument(
        "--codex-command",
        default="codex",
        help="Codex CLI executable to use when --agent codex.",
    )
    smoke_test_parser.add_argument(
        "--codex-model",
        default=None,
        help="Optional model passed to `codex exec --model`.",
    )
    smoke_test_parser.add_argument(
        "--codex-profile",
        default=None,
        help="Optional profile passed to `codex exec --profile`.",
    )
    smoke_test_parser.add_argument(
        "--codex-sandbox",
        default="workspace-write",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode passed to `codex exec --sandbox`.",
    )
    smoke_test_parser.add_argument(
        "--codex-approval",
        default="never",
        choices=["untrusted", "on-failure", "on-request", "never"],
        help="Approval policy passed to `codex exec --ask-for-approval`.",
    )
    smoke_test_parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=1800,
        help="Maximum wall time for `codex exec`.",
    )
    smoke_test_parser.set_defaults(handler=handle_task_smoke_test)

    doctor_parser = subcommands.add_parser(
        "doctor",
        help="Check local agent harness prerequisites before running trials.",
    )
    doctor_parser.add_argument(
        "--agent",
        default="codex",
        choices=["codex"],
        help="Agent harness to check.",
    )
    doctor_parser.add_argument(
        "--codex-command",
        default="codex",
        help="Codex CLI executable to use when --agent codex.",
    )
    doctor_parser.add_argument(
        "--codex-model",
        default=None,
        help="Optional model passed to `codex exec --model`.",
    )
    doctor_parser.add_argument(
        "--codex-profile",
        default=None,
        help="Optional profile passed to `codex exec --profile`.",
    )
    doctor_parser.add_argument(
        "--codex-sandbox",
        default="workspace-write",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode passed to `codex exec --sandbox`.",
    )
    doctor_parser.add_argument(
        "--codex-approval",
        default="never",
        choices=["untrusted", "on-failure", "on-request", "never"],
        help="Approval policy passed to `codex exec --ask-for-approval`.",
    )
    doctor_parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=15,
        help="Maximum wall time for each Codex preflight command.",
    )
    doctor_parser.set_defaults(handler=handle_doctor)

    run_parser = subcommands.add_parser(
        "run",
        help="Run one trial for a task through an agent harness.",
    )
    run_parser.add_argument(
        "--task",
        required=True,
        help="Task YAML file or task bundle directory to run.",
    )
    run_parser.add_argument(
        "--agent",
        default="manual",
        choices=["manual", "codex"],
        help="Agent backend to use.",
    )
    run_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts should be written.",
    )
    run_parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Number of independent trials to run for this task.",
    )
    run_parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Maximum number of trials to run concurrently.",
    )
    run_parser.add_argument(
        "--no-pause",
        action="store_true",
        help="For the manual agent, do not wait for human edits.",
    )
    run_parser.add_argument(
        "--codex-command",
        default="codex",
        help="Codex CLI executable to use when --agent codex.",
    )
    run_parser.add_argument(
        "--codex-model",
        default=None,
        help="Optional model passed to `codex exec --model`.",
    )
    run_parser.add_argument(
        "--codex-profile",
        default=None,
        help="Optional profile passed to `codex exec --profile`.",
    )
    run_parser.add_argument(
        "--codex-sandbox",
        default="workspace-write",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode passed to `codex exec --sandbox`.",
    )
    run_parser.add_argument(
        "--codex-approval",
        default="never",
        choices=["untrusted", "on-failure", "on-request", "never"],
        help="Approval policy passed to `codex exec --ask-for-approval`.",
    )
    run_parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=1800,
        help="Maximum wall time for `codex exec`.",
    )
    run_parser.set_defaults(handler=handle_run)

    runs_parser = subcommands.add_parser(
        "runs",
        help="Inspect stored trial artifacts. Legacy alias for trials.",
    )
    runs_subcommands = runs_parser.add_subparsers(dest="runs_command")

    list_parser = runs_subcommands.add_parser(
        "list",
        help="List trials that have result.json metadata.",
    )
    list_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    list_parser.set_defaults(handler=handle_runs_list)

    trials_parser = subcommands.add_parser(
        "trials",
        help="Inspect stored trial artifacts.",
    )
    trials_subcommands = trials_parser.add_subparsers(dest="trials_command")

    trials_list_parser = trials_subcommands.add_parser(
        "list",
        help="List trials that have result.json metadata.",
    )
    trials_list_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    trials_list_parser.set_defaults(handler=handle_runs_list)

    trials_summary_parser = trials_subcommands.add_parser(
        "summarize",
        help="Summarize trials by suite, task, agent harness, and model.",
    )
    trials_summary_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    trials_summary_parser.set_defaults(handler=handle_trials_summarize)

    report_parser = subcommands.add_parser(
        "report",
        help="Generate report-support artifacts from stored trial evidence.",
    )
    report_subcommands = report_parser.add_subparsers(dest="report_command")

    evidence_parser = report_subcommands.add_parser(
        "evidence-appendix",
        help="Generate a Markdown evidence appendix from stored trial results.",
    )
    evidence_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    evidence_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown file to write. Defaults to stdout.",
    )
    evidence_parser.set_defaults(handler=handle_report_evidence_appendix)

    review_parser = subcommands.add_parser(
        "review",
        help="Attach a human review label and note to a trial.",
    )
    review_parser.add_argument(
        "--run",
        "--trial",
        required=True,
        dest="run",
        help="Trial directory to review, or 'latest'.",
    )
    review_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored when --run latest is used.",
    )
    review_parser.add_argument(
        "--label",
        required=True,
        choices=FAILURE_LABELS,
        help="Primary failure/success label.",
    )
    review_parser.add_argument(
        "--secondary",
        action="append",
        default=[],
        choices=FAILURE_LABELS,
        help="Optional secondary label. Can be repeated.",
    )
    review_parser.add_argument(
        "--note",
        required=True,
        help="Short human review note.",
    )
    review_parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Evidence such as a failing command, diff hunk, or transcript excerpt.",
    )
    review_parser.add_argument(
        "--validity",
        default=None,
        choices=TRIAL_VALIDITIES,
        help="Whether this trial should count in fair capability summaries.",
    )
    review_parser.add_argument(
        "--exclude",
        action="store_true",
        help="Mark this trial as excluded from fair capability summaries.",
    )
    review_parser.add_argument(
        "--exclusion-reason",
        default=None,
        choices=EXCLUSION_REASONS,
        help="Reason an excluded trial should not count in fair summaries.",
    )
    review_parser.set_defaults(handler=handle_review)

    return parser


def handle_task_validate(args: argparse.Namespace) -> int:
    files = discover_task_files(args.paths)
    if not files:
        print("No task files matched.", file=sys.stderr)
        return 1

    failures: List[str] = []
    for path in files:
        try:
            task = load_task(path)
        except TaskLoadError as exc:
            failures.append(f"{path}: {exc}")
            continue

        print(f"OK {Path(path)} ({task.id})")

    if failures:
        for failure in failures:
            print(f"ERROR {failure}", file=sys.stderr)
        return 1

    print(f"Validated {len(files)} task file(s).")
    return 0


def handle_task_verify_reference(args: argparse.Namespace) -> int:
    files = discover_task_files(args.paths)
    if not files:
        print("No task files matched.", file=sys.stderr)
        return 1

    if args.workspace_root:
        workspace_root = Path(args.workspace_root)
        workspace_root.mkdir(parents=True, exist_ok=True)
        return _verify_reference_files(
            files,
            workspace_root,
            args.skip_missing,
            args.write_artifacts,
        )

    with tempfile.TemporaryDirectory(prefix="agentlab-reference-") as temp:
        return _verify_reference_files(
            files,
            Path(temp),
            args.skip_missing,
            args.write_artifacts,
        )


def _verify_reference_files(
    files: List[Path],
    workspace_root: Path,
    skip_missing: bool,
    write_artifacts: bool,
) -> int:
    failures: List[str] = []
    skipped = 0
    for path in files:
        try:
            task = load_task(path)
            if task.reference_artifact is None and skip_missing:
                skipped += 1
                print(f"SKIP {Path(path)} ({task.id}): no reference_artifact")
                continue
            verification = verify_reference(
                task,
                workspace_root,
                write_artifacts=write_artifacts,
            )
        except (RuntimeError, TaskLoadError, ReferenceVerificationError) as exc:
            failures.append(f"{path}: {exc}")
            continue

        status = "OK" if verification.success else "FAIL"
        message = (
            f"{status} {Path(path)} ({task.id}) "
            f"files_changed={len(verification.files_changed)}"
        )
        if write_artifacts:
            message += f" report={verification.report_path}"
        print(message)
        if not verification.success:
            failures.append(f"{path}: reference verification failed")
            _print_failed_reference_checks(verification)

    if failures:
        for failure in failures:
            print(f"ERROR {failure}", file=sys.stderr)
        return 1

    print(f"Verified {len(files) - skipped} reference artifact(s).")
    if skipped:
        print(f"Skipped {skipped} task(s) without reference_artifact.")
    return 0


def handle_task_smoke_test(args: argparse.Namespace) -> int:
    try:
        task = load_task(args.task)
    except TaskLoadError as exc:
        print_error(str(exc))
        return 1

    print("Smoke test step 1/2: verifying reference artifact...")
    with tempfile.TemporaryDirectory(prefix="agentlab-smoke-reference-") as temp:
        try:
            verification = verify_reference(
                task,
                Path(temp),
                write_artifacts=False,
            )
        except (RuntimeError, ReferenceVerificationError) as exc:
            print_error(f"reference verification failed: {exc}")
            return 1

    if not verification.success:
        print_error("reference verification failed")
        _print_failed_reference_checks(verification)
        return 1

    print(
        "Reference OK: "
        f"{task.id} files_changed={len(verification.files_changed)} "
        f"lines_added={verification.lines_added} "
        f"lines_deleted={verification.lines_deleted}"
    )
    print("Smoke test step 2/2: running exactly one trial with one job...")

    try:
        agent = _build_agent(args)
        evaluation = run_task(task, agent, Path(args.runs_dir))
    except RuntimeError as exc:
        print_error(str(exc))
        return 1

    _print_run_summaries([evaluation])
    _print_smoke_test_result(evaluation)
    return 0 if evaluation.score.tests_passed else 1


def handle_doctor(args: argparse.Namespace) -> int:
    if args.agent == "codex":
        result = run_codex_preflight(
            CodexCliConfig(
                command=args.codex_command,
                model=args.codex_model,
                profile=args.codex_profile,
                sandbox=args.codex_sandbox,
                approval_policy=args.codex_approval,
                timeout_seconds=args.codex_timeout_seconds,
                show_progress=False,
            ),
            timeout_seconds=args.codex_timeout_seconds,
        )
    else:
        print_error(f"unknown agent: {args.agent}")
        return 1

    _print_preflight_result(result)
    return 0 if result.passed else 1


def handle_run(args: argparse.Namespace) -> int:
    try:
        task = load_task(args.task)
        if args.trials < 1:
            raise RuntimeError("--trials must be at least 1")
        if args.jobs < 1:
            raise RuntimeError("--jobs must be at least 1")
        if args.agent == "manual" and not args.no_pause and args.jobs > 1:
            raise RuntimeError("parallel manual trials require --no-pause")
        evaluations = _run_trials(task, args)
    except (RuntimeError, TaskLoadError) as exc:
        print_error(str(exc))
        return 1

    passed = sum(1 for evaluation in evaluations if evaluation.score.tests_passed)
    _print_run_summaries(evaluations)
    _print_aggregate_summary(evaluations, passed)
    return 0 if passed == len(evaluations) else 1


def _run_trials(task: object, args: argparse.Namespace) -> list[object]:
    runs_dir = Path(args.runs_dir)
    jobs = min(args.jobs, args.trials)
    if jobs == 1:
        evaluations = []
        for trial_index in range(args.trials):
            if args.trials > 1:
                print(f"Starting trial {trial_index + 1}/{args.trials}...")
            evaluations.append(
                _run_single_trial(
                    task=task,
                    args=args,
                    runs_dir=runs_dir,
                    show_agent_progress=True,
                )
            )
        return evaluations

    print(f"Starting {args.trials} trials with {jobs} jobs...")
    indexed_evaluations = []
    failures = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        future_indexes = {}
        for trial_index in range(args.trials):
            future = executor.submit(
                _run_single_trial,
                task,
                args,
                runs_dir,
                False,
            )
            future_indexes[future] = trial_index

        progress = ProgressBar("Trials")
        pending = set(future_indexes)
        while pending:
            done, pending = wait(
                pending,
                timeout=progress.interval_seconds,
                return_when=FIRST_COMPLETED,
            )
            if not done:
                progress.update(f"waiting for {len(pending)} trial(s)")
                continue

            for future in done:
                trial_index = future_indexes[future]
                trial_label = f"trial {trial_index + 1}/{args.trials}"
                try:
                    evaluation = future.result()
                except Exception as exc:
                    failures.append(f"{trial_label}: {exc}")
                    continue

                indexed_evaluations.append((trial_index, evaluation))
        progress.finish("all trials finished")

    if failures:
        raise RuntimeError(
            "parallel trial failure(s): "
            + "; ".join(str(failure) for failure in failures)
        )

    return [
        evaluation
        for _trial_index, evaluation in sorted(
            indexed_evaluations,
            key=lambda indexed: indexed[0],
        )
    ]


def _run_single_trial(
    task: object,
    args: argparse.Namespace,
    runs_dir: Path,
    show_agent_progress: bool,
) -> object:
    agent = _build_agent(args, show_progress=show_agent_progress)
    return run_task(task, agent, runs_dir)


def _print_run_summaries(evaluations: list[object]) -> None:
    failed = [
        evaluation
        for evaluation in evaluations
        if not evaluation.score.tests_passed or evaluation.agent_run.error
    ]
    if not failed:
        return

    print("Failed trials:")
    for evaluation in failed:
        if evaluation.agent_run.error:
            print_error(
                f"{evaluation.agent_run.agent_name}: {evaluation.agent_run.error}"
            )
        print(f"- {evaluation.run_dir.name}: failed")
        print(f"  Report: {evaluation.report_path}")
        print(f"  Result: {evaluation.result_path}")


def _print_aggregate_summary(evaluations: list[object], passed: int) -> None:
    total = len(evaluations)
    print(
        "Summary: "
        f"{passed}/{total} passed; "
        f"pass@{total}={1.0 if passed else 0.0:.2f}; "
        f"pass^{total}={1.0 if passed == total else 0.0:.2f}"
    )


def _print_smoke_test_result(evaluation: object) -> None:
    status = "passed" if evaluation.score.tests_passed else "failed"
    print(f"Smoke test trial: {evaluation.run_dir.name}")
    print(f"Status: {status}")
    print(f"Report: {evaluation.report_path}")
    print(f"Result: {evaluation.result_path}")
    print(f"Diff: {evaluation.agent_run.diff_path}")
    print("")
    if evaluation.score.tests_passed:
        print("Next step: inspect the report and diff before repeated trials.")
        return
    print(
        "If this failure is caused by setup, harness, operator, task-definition, "
        "or dependency problems, preserve the artifacts and exclude the trial, "
        "for example:"
    )
    print(
        "python3 -m agentlab review "
        f"--trial {evaluation.run_dir} "
        "--label dependency_issue "
        "--note \"Smoke test failed before measuring agent capability.\" "
        "--exclude "
        "--exclusion-reason setup_error"
    )


def _print_preflight_result(result: object) -> None:
    print(f"Doctor: {result.agent_name}")
    for check in result.checks:
        if check.passed:
            print(f"OK {check.name}: {check.message}")
            continue

        print_error(f"{check.name}: {check.message}")
        if check.command:
            print(f"  Command: {shlex.join(check.command)}", file=sys.stderr)
        output = _trim_cli_output(check.stderr or check.stdout)
        if output:
            print(output, file=sys.stderr)

    if result.passed:
        print("Preflight passed.")
    else:
        print("Preflight failed.", file=sys.stderr)


def _build_agent(args: argparse.Namespace, show_progress: bool = True) -> object:
    if args.agent == "manual":
        return ManualAgentAdapter(pause=not args.no_pause)
    if args.agent == "codex":
        return CodexCliAdapter(
            CodexCliConfig(
                command=args.codex_command,
                model=args.codex_model,
                profile=args.codex_profile,
                sandbox=args.codex_sandbox,
                approval_policy=args.codex_approval,
                timeout_seconds=args.codex_timeout_seconds,
                show_progress=show_progress,
            )
        )
    raise RuntimeError(f"unknown agent: {args.agent}")


def handle_runs_list(args: argparse.Namespace) -> int:
    result_files = discover_result_files(Path(args.runs_dir))
    results = load_results(result_files)
    if not results:
        print("No result.json files found.")
        return 0

    rows = [
        [
            result.get("trial_id", result.get("run_id", "")),
            result.get("eval_suite", ""),
            result.get("eval_type", ""),
            result.get("status", ""),
            trial_validity(result),
            _review_label(result),
            exclusion_reason(result),
            result.get("agent_name", ""),
            result.get("task_id", ""),
            str(len(result.get("files_changed", []))),
            str(result.get("lines_added", 0)),
            str(result.get("lines_deleted", 0)),
            _format_optional(result.get("input_tokens")),
            _format_optional(result.get("output_tokens")),
            _format_optional(result.get("reasoning_output_tokens")),
            _format_optional(result.get("cost_usd")),
        ]
        for result in results
    ]
    _print_table(
        [
            "trial_id",
            "suite",
            "type",
            "status",
            "validity",
            "review",
            "exclusion",
            "agent",
            "task",
            "files",
            "added",
            "deleted",
            "in_tok",
            "out_tok",
            "reason_tok",
            "cost",
        ],
        rows,
    )
    return 0


def handle_trials_summarize(args: argparse.Namespace) -> int:
    result_files = discover_result_files(Path(args.runs_dir))
    results = load_results(result_files)
    if not results:
        print("No result.json files found.")
        return 0

    rows = []
    for summary in summarize_trials(results):
        rows.append(
            [
                summary.eval_suite,
                summary.eval_type,
                summary.task_id,
                summary.agent_name,
                summary.model_name,
                str(summary.total_trials),
                str(summary.trials),
                str(summary.excluded_trials),
                str(summary.passes),
                _format_rate(summary.pass_rate),
                _format_rate(summary.pass_at_k),
                _format_rate(summary.pass_caret_k),
                str(summary.median_duration_ms),
                str(summary.median_files_changed),
                str(summary.median_lines_added),
                str(summary.median_lines_deleted),
                _format_review_labels(summary.review_labels),
                _format_review_labels(summary.exclusion_reasons),
            ]
        )
    _print_table(
        [
            "suite",
            "type",
            "task",
            "agent",
            "model",
            "total",
            "fair",
            "excluded",
            "passes",
            "pass_rate",
            "pass@k",
            "pass^k",
            "med_ms",
            "med_files",
            "med_added",
            "med_deleted",
            "reviews",
            "exclusions",
        ],
        rows,
    )
    return 0


def handle_report_evidence_appendix(args: argparse.Namespace) -> int:
    result_files = discover_result_files(Path(args.runs_dir))
    results = load_results(result_files)
    if not results:
        print("No result.json files found.", file=sys.stderr)
        return 1

    appendix = render_evidence_appendix(results)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(appendix, encoding="utf-8")
        print(f"Evidence appendix: {output_path}")
        return 0

    print(appendix)
    return 0


def handle_review(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run_dir(Path(args.runs_dir), args.run)
        validity = args.validity or DEFAULT_TRIAL_VALIDITY
        if args.exclude:
            if args.validity == DEFAULT_TRIAL_VALIDITY:
                raise ValueError("--exclude conflicts with --validity valid")
            validity = EXCLUDED_TRIAL_VALIDITY
        review_path = write_review(
            run_dir,
            primary_label=args.label,
            note=args.note,
            secondary_labels=args.secondary,
            evidence=args.evidence,
            trial_validity=validity,
            exclusion_reason=args.exclusion_reason,
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    review = load_review(run_dir) or {}
    print(f"Review: {review_path}")
    print(f"Validity: {review.get('trial_validity', validity)}")
    if review.get("trial_validity") == EXCLUDED_TRIAL_VALIDITY:
        print(f"Exclusion: {review.get('exclusion_reason', 'unknown')}")
    return 0


def _print_table(headers: List[str], rows: List[List[str]]) -> None:
    widths = [
        max(len(str(row[column])) for row in [headers] + rows)
        for column in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)))


def _print_failed_reference_checks(verification: ReferenceVerification) -> None:
    checks = verification.setup_checks + verification.baseline_checks
    checks += [verification.artifact_check] + verification.target_checks
    for check in checks:
        if check.passed:
            continue
        output = _trim_cli_output(check.stderr or check.stdout)
        print(f"  failed: {check.command} ({check.returncode})", file=sys.stderr)
        if output:
            print(output, file=sys.stderr)
    for note in verification.notes:
        print(f"  note: {note}", file=sys.stderr)


def _review_label(result: object) -> str:
    if not isinstance(result, dict):
        return ""
    review = result.get("review")
    if isinstance(review, dict):
        return str(review.get("primary_label", ""))
    run_dir = result.get("run_dir")
    if not run_dir:
        return ""
    review = load_review(Path(str(run_dir)))
    if not review:
        return ""
    return str(review.get("primary_label", ""))


def _format_rate(value: float) -> str:
    return f"{value:.2f}"


def _format_optional(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _trim_cli_output(output: str, max_chars: int = 1000) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[-max_chars:]


def _format_review_labels(labels: object) -> str:
    if not isinstance(labels, dict) or not labels:
        return ""
    return ",".join(f"{label}:{count}" for label, count in labels.items())
