from __future__ import annotations

import argparse
from pathlib import Path

from agentlab.cli.agent_options import (
    AGENT_CHOICES,
    add_agent_adapter_options,
    add_agent_argument,
    _agent_factory,
)
from agentlab.tasks import TaskLoadError, load_task
from agentlab.terminal import print_error
from agentlab.trial_execution import TrialExecutionConfig, execute_trials


def add_run_command(subcommands: argparse._SubParsersAction) -> None:
    run_parser = subcommands.add_parser(
        "run",
        help="Run one trial for a task through an agent harness.",
    )
    run_parser.add_argument(
        "--task",
        required=True,
        help="Task YAML file or task bundle directory to run.",
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
        task = load_task(args.task)
        evaluations = execute_trials(
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
    except (RuntimeError, TaskLoadError) as exc:
        print_error(str(exc))
        return 1

    passed = sum(1 for evaluation in evaluations if evaluation.score.tests_passed)
    _print_run_summaries(evaluations)
    _print_aggregate_summary(evaluations, passed)
    return 0 if passed == len(evaluations) else 1


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
