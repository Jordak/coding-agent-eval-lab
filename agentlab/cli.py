from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List

from agentlab.agents.codex_cli import CodexCliAdapter, CodexCliConfig
from agentlab.agents.manual import ManualAgentAdapter
from agentlab.reference import (
    ReferenceVerification,
    ReferenceVerificationError,
    verify_reference,
)
from agentlab.review import FAILURE_LABELS, resolve_run_dir, write_review
from agentlab.results import discover_result_files, load_results
from agentlab.runner import run_task
from agentlab.summary import summarize_trials
from agentlab.tasks import TaskLoadError, discover_task_files, load_task


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
    verify_reference_parser.set_defaults(handler=handle_task_verify_reference)

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
        return _verify_reference_files(files, workspace_root, args.skip_missing)

    with tempfile.TemporaryDirectory(prefix="agentlab-reference-") as temp:
        return _verify_reference_files(files, Path(temp), args.skip_missing)


def _verify_reference_files(
    files: List[Path],
    workspace_root: Path,
    skip_missing: bool,
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
            verification = verify_reference(task, workspace_root)
        except (RuntimeError, TaskLoadError, ReferenceVerificationError) as exc:
            failures.append(f"{path}: {exc}")
            continue

        status = "OK" if verification.success else "FAIL"
        print(
            f"{status} {Path(path)} ({task.id}) "
            f"files_changed={len(verification.files_changed)}"
        )
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


def handle_run(args: argparse.Namespace) -> int:
    try:
        task = load_task(args.task)
        if args.trials < 1:
            raise RuntimeError("--trials must be at least 1")
        evaluations = []
        for trial_index in range(args.trials):
            agent = _build_agent(args)
            if args.trials > 1:
                print(f"Starting trial {trial_index + 1}/{args.trials}...")
            evaluations.append(run_task(task, agent, Path(args.runs_dir)))
    except (RuntimeError, TaskLoadError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    for evaluation in evaluations:
        print(f"Run: {evaluation.run_dir}")
        print(f"Trial: {evaluation.run_dir.name}")
        print(f"Report: {evaluation.report_path}")
        print(f"Result: {evaluation.result_path}")
        print(f"Status: {'passed' if evaluation.score.tests_passed else 'failed'}")

    passed = sum(1 for evaluation in evaluations if evaluation.score.tests_passed)
    if len(evaluations) > 1:
        print(
            "Summary: "
            f"{passed}/{len(evaluations)} passed; "
            f"pass@{len(evaluations)}={1.0 if passed else 0.0:.2f}; "
            f"pass^{len(evaluations)}={1.0 if passed == len(evaluations) else 0.0:.2f}"
        )
    return 0 if passed == len(evaluations) else 1


def _build_agent(args: argparse.Namespace) -> object:
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
            _review_label(result),
            result.get("agent_name", ""),
            result.get("task_id", ""),
            str(len(result.get("files_changed", []))),
        ]
        for result in results
    ]
    _print_table(
        ["trial_id", "suite", "type", "status", "review", "agent", "task", "files"],
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
                str(summary.trials),
                str(summary.passes),
                _format_rate(summary.pass_rate),
                _format_rate(summary.pass_at_k),
                _format_rate(summary.pass_caret_k),
                str(summary.median_duration_ms),
                str(summary.median_files_changed),
                _format_review_labels(summary.review_labels),
            ]
        )
    _print_table(
        [
            "suite",
            "type",
            "task",
            "agent",
            "model",
            "trials",
            "passes",
            "pass_rate",
            "pass@k",
            "pass^k",
            "med_ms",
            "med_files",
            "reviews",
        ],
        rows,
    )
    return 0


def handle_review(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run_dir(Path(args.runs_dir), args.run)
        review_path = write_review(
            run_dir,
            primary_label=args.label,
            note=args.note,
            secondary_labels=args.secondary,
            evidence=args.evidence,
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print(f"Review: {review_path}")
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
    run_dir = result.get("run_dir")
    if not run_dir:
        return ""
    from agentlab.review import load_review

    review = load_review(Path(str(run_dir)))
    if not review:
        return ""
    return str(review.get("primary_label", ""))


def _format_rate(value: float) -> str:
    return f"{value:.2f}"


def _trim_cli_output(output: str, max_chars: int = 1000) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[-max_chars:]


def _format_review_labels(labels: object) -> str:
    if not isinstance(labels, dict) or not labels:
        return ""
    return ",".join(f"{label}:{count}" for label, count in labels.items())
