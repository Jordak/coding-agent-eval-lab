from __future__ import annotations

import argparse
from pathlib import Path

from agentlab.cli.agent_options import (
    AGENT_CHOICES,
    add_agent_adapter_options,
    add_agent_argument,
    _agent_factory,
)
from agentlab.tasks import EvalTask, TaskLoadError, discover_task_bundles, load_task
from agentlab.terminal import print_error
from agentlab.execution.trials import TrialExecutionConfig, execute_trials


def add_run_command(subcommands: argparse._SubParsersAction) -> None:
    run_parser = subcommands.add_parser(
        "run",
        help="Run task trials through an agent harness.",
    )
    task_selection = run_parser.add_mutually_exclusive_group(required=True)
    task_selection.add_argument(
        "--task",
        help="Task YAML file or task bundle directory to run.",
    )
    task_selection.add_argument(
        "--suite",
        help="Suite directory containing task bundles to run sequentially.",
    )
    add_agent_argument(
        run_parser,
        default="manual",
        choices=AGENT_CHOICES,
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
    add_agent_adapter_options(
        run_parser,
        codex_timeout_default=1800,
        claude_timeout_default=1800,
    )
    run_parser.set_defaults(handler=handle_run)


def handle_run(args: argparse.Namespace) -> int:
    try:
        if getattr(args, "suite", None):
            return _handle_suite_run(args)

        task = load_task(args.task)
        evaluations = _execute_task_run(args, task)
    except (RuntimeError, TaskLoadError) as exc:
        print_error(str(exc))
        return 1

    passed = sum(1 for evaluation in evaluations if evaluation.score.tests_passed)
    _print_run_summaries(evaluations)
    _print_aggregate_summary(evaluations, passed)
    return 0 if passed == len(evaluations) else 1


def _handle_suite_run(args: argparse.Namespace) -> int:
    bundles = discover_task_bundles([args.suite])
    if not bundles:
        print_error("No task files matched.")
        return 1

    all_evaluations: list[object] = []
    task_errors: list[str] = []
    for index, bundle in enumerate(bundles, start=1):
        task = bundle.task
        print(f"Running task {index}/{len(bundles)}: {task.id}")
        try:
            evaluations = _execute_task_run(args, task)
        except RuntimeError as exc:
            task_errors.append(f"{task.id}: {exc}")
            print_error(f"{task.id}: {exc}")
            continue

        passed = sum(1 for evaluation in evaluations if evaluation.score.tests_passed)
        _print_run_summaries(evaluations)
        _print_aggregate_summary(evaluations, passed)
        all_evaluations.extend(evaluations)

    if task_errors:
        print("Suite errors:")
        for task_error in task_errors:
            print(f"- {task_error}")

    passed = sum(1 for evaluation in all_evaluations if evaluation.score.tests_passed)
    total = len(all_evaluations)
    print(
        "Suite summary: "
        f"{passed}/{total} passed across {len(bundles)} task(s)"
    )
    return 0 if not task_errors and passed == total else 1


def _execute_task_run(args: argparse.Namespace, task: EvalTask) -> list[object]:
    return execute_trials(
        task,
        _agent_factory(args),
        TrialExecutionConfig(
            runs_dir=Path(args.runs_dir),
            trials=args.trials,
            jobs=args.jobs,
            agent_name=args.agent,
            manual_parallel_allowed=args.no_pause,
        ),
    )


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
