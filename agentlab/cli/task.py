from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import List

from agentlab.cli.agent_options import (
    AGENT_CHOICES,
    add_agent_adapter_options,
    add_agent_argument,
    _agent_factory,
)
from agentlab.cli.output import _trim_cli_output
from agentlab.cli.run import _print_run_summaries
from agentlab.reference import (
    ReferenceVerification,
    ReferenceVerificationError,
)
from agentlab.task_bundle_integrity import (
    TaskBundleIntegrityError,
    check_reference_artifact_ready,
    check_task_bundle_integrity,
    load_smoke_test_ready_bundle,
    validate_task_bundle_sources,
    verify_reference_for_bundle,
)
from agentlab.tasks import TaskLoadError, discover_task_files
from agentlab.terminal import print_error
from agentlab.trial_execution import TrialExecutionConfig, execute_trials


def add_task_commands(subcommands: argparse._SubParsersAction) -> None:
    task_parser = subcommands.add_parser("task", help="Task definition commands.")
    task_subcommands = task_parser.add_subparsers(dest="task_command")

    validate_parser = task_subcommands.add_parser(
        "validate",
        help="Validate one or more task YAML files.",
    )
    validate_parser.add_argument(
        "--check-task-cards",
        action="store_true",
        help="Fail if generated task-card.md files drift from task.yaml.",
    )
    validate_parser.add_argument(
        "--require-reference-artifacts",
        action="store_true",
        help="Fail if a task bundle is missing a reference_artifact.",
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
    add_agent_argument(
        smoke_test_parser,
        default="manual",
        choices=AGENT_CHOICES,
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
    add_agent_adapter_options(
        smoke_test_parser,
        codex_timeout_default=1800,
        claude_timeout_default=1800,
    )
    smoke_test_parser.set_defaults(handler=handle_task_smoke_test)


def handle_task_validate(args: argparse.Namespace) -> int:
    result = check_task_bundle_integrity(
        args.paths,
        check_task_cards=args.check_task_cards,
        require_reference_artifacts=args.require_reference_artifacts,
    )
    if result.matched_files == 0:
        print("No task files matched.", file=sys.stderr)
        return 1

    for bundle in result.bundles:
        print(f"OK {bundle.task_file} ({bundle.task.id})")

    if result.task_card_changes:
        for path in result.task_card_changes:
            print(
                f"ERROR {path}: task-card drift; regenerate from task.yaml",
                file=sys.stderr,
            )

    if result.failures:
        for failure in result.failures:
            print(f"ERROR {failure.path}: {failure.message}", file=sys.stderr)

    if not result.ok:
        return 1

    print(f"Validated {result.matched_files} task file(s).")
    if args.check_task_cards:
        print("Task cards are up to date.")
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
    source = validate_task_bundle_sources(str(path) for path in files)
    failures: List[str] = []
    skipped = 0
    for failure in source.failures:
        failures.append(f"{failure.path}: {failure.message}")

    for bundle in source.bundles:
        readiness = check_reference_artifact_ready(bundle)
        if not readiness.ready:
            if skip_missing and bundle.task.reference_artifact is None:
                skipped += 1
                print(
                    f"SKIP {bundle.task_file} ({bundle.task.id}): "
                    "no reference_artifact"
                )
                continue
            failures.append(f"{bundle.task_file}: {readiness.message}")
            continue

        try:
            verification = verify_reference_for_bundle(
                bundle,
                workspace_root,
                write_artifacts=write_artifacts,
            )
        except (
            RuntimeError,
            TaskBundleIntegrityError,
            ReferenceVerificationError,
        ) as exc:
            failures.append(f"{bundle.task_file}: {exc}")
            continue

        status = "OK" if verification.success else "FAIL"
        message = (
            f"{status} {bundle.task_file} ({bundle.task.id}) "
            f"files_changed={len(verification.files_changed)}"
        )
        if write_artifacts:
            message += f" report={verification.report_path}"
        print(message)
        if not verification.success:
            failures.append(f"{bundle.task_file}: reference verification failed")
            _print_failed_reference_checks(verification)

    if failures:
        for failure in failures:
            print(f"ERROR {failure}", file=sys.stderr)
        return 1

    print(f"Verified {len(source.bundles) - skipped} reference artifact(s).")
    if skipped:
        print(f"Skipped {skipped} task(s) without reference_artifact.")
    return 0


def handle_task_smoke_test(args: argparse.Namespace) -> int:
    try:
        bundle = load_smoke_test_ready_bundle(args.task)
    except (TaskLoadError, TaskBundleIntegrityError) as exc:
        print_error(str(exc))
        return 1
    task = bundle.task

    print("Smoke test step 1/2: verifying reference artifact...")
    with tempfile.TemporaryDirectory(prefix="agentlab-smoke-reference-") as temp:
        try:
            verification = verify_reference_for_bundle(
                bundle,
                Path(temp),
                write_artifacts=False,
            )
        except (
            RuntimeError,
            TaskBundleIntegrityError,
            ReferenceVerificationError,
        ) as exc:
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
        evaluations = execute_trials(
            task,
            _agent_factory(args),
            TrialExecutionConfig(
                runs_dir=Path(args.runs_dir),
                trials=1,
                jobs=1,
                agent_name=args.agent,
                manual_parallel_allowed=args.no_pause,
            ),
        )
        evaluation = evaluations[0]
    except RuntimeError as exc:
        print_error(str(exc))
        return 1

    _print_run_summaries([evaluation])
    _print_smoke_test_result(evaluation)
    return 0 if evaluation.score.tests_passed else 1


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
        "If this failure is caused by setup, eval harness, operator, "
        "task-definition, or dependency problems, preserve the artifacts and "
        "exclude the trial, "
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
