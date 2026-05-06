from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

from agentlab.agents.manual import ManualAgentAdapter
from agentlab.review import FAILURE_LABELS, resolve_run_dir, write_review
from agentlab.results import discover_result_files, load_results
from agentlab.runner import run_task
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
        help="Task file paths or glob patterns, such as tasks/starter/*.yaml.",
    )
    validate_parser.set_defaults(handler=handle_task_validate)

    run_parser = subcommands.add_parser("run", help="Run one task through an agent.")
    run_parser.add_argument("--task", required=True, help="Task YAML file to run.")
    run_parser.add_argument(
        "--agent",
        default="manual",
        choices=["manual"],
        help="Agent backend to use.",
    )
    run_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where run artifacts should be written.",
    )
    run_parser.add_argument(
        "--no-pause",
        action="store_true",
        help="For the manual agent, do not wait for human edits.",
    )
    run_parser.set_defaults(handler=handle_run)

    runs_parser = subcommands.add_parser("runs", help="Inspect stored run artifacts.")
    runs_subcommands = runs_parser.add_subparsers(dest="runs_command")

    list_parser = runs_subcommands.add_parser(
        "list",
        help="List runs that have result.json metadata.",
    )
    list_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where run artifacts are stored.",
    )
    list_parser.set_defaults(handler=handle_runs_list)

    review_parser = subcommands.add_parser(
        "review",
        help="Attach a human review label and note to a run.",
    )
    review_parser.add_argument(
        "--run",
        required=True,
        help="Run directory to review, or 'latest'.",
    )
    review_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where run artifacts are stored when --run latest is used.",
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


def handle_run(args: argparse.Namespace) -> int:
    try:
        task = load_task(args.task)
        agent = ManualAgentAdapter(pause=not args.no_pause)
        evaluation = run_task(task, agent, Path(args.runs_dir))
    except (RuntimeError, TaskLoadError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print(f"Run: {evaluation.run_dir}")
    print(f"Report: {evaluation.report_path}")
    print(f"Result: {evaluation.result_path}")
    print(f"Status: {'passed' if evaluation.score.tests_passed else 'failed'}")
    return 0


def handle_runs_list(args: argparse.Namespace) -> int:
    result_files = discover_result_files(Path(args.runs_dir))
    results = load_results(result_files)
    if not results:
        print("No result.json files found.")
        return 0

    rows = [
        [
            result.get("run_id", ""),
            result.get("status", ""),
            _review_label(result),
            result.get("agent_name", ""),
            result.get("task_id", ""),
            str(len(result.get("files_changed", []))),
        ]
        for result in results
    ]
    _print_table(["run_id", "status", "review", "agent", "task", "files"], rows)
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
