from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.cli.output import _print_table
from agentlab.outcome_evidence import result_files_changed_count
from agentlab.results import discover_result_files, load_results
from agentlab.review import load_review
from agentlab.summary import summarize_trials
from agentlab.trial_archive import archive_excluded_trials
from agentlab.validity import EXCLUSION_REASONS, exclusion_reason, trial_validity


def add_trial_commands(subcommands: argparse._SubParsersAction) -> None:
    runs_parser = subcommands.add_parser(
        "runs",
        help="Inspect stored trial artifacts. Legacy alias for trials.",
    )
    runs_subcommands = runs_parser.add_subparsers(dest="runs_command")

    list_parser = runs_subcommands.add_parser(
        "list",
        help="List trials that have result.json metadata.",
    )
    add_runs_dir_argument(list_parser)
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
    add_runs_dir_argument(trials_list_parser)
    trials_list_parser.set_defaults(handler=handle_runs_list)

    trials_summary_parser = trials_subcommands.add_parser(
        "summarize",
        help="Summarize trials by suite, task, agent harness, and model.",
    )
    add_runs_dir_argument(trials_summary_parser)
    trials_summary_parser.set_defaults(handler=handle_trials_summarize)

    trials_archive_parser = trials_subcommands.add_parser(
        "archive-excluded",
        help="Archive reviewed excluded trial artifacts without deleting evidence.",
    )
    trials_archive_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where active trial artifacts are stored.",
    )
    trials_archive_parser.add_argument(
        "--archive-dir",
        default=None,
        help="Archive root. Defaults to <runs-dir>/_archive.",
    )
    trials_archive_parser.add_argument(
        "--exclusion-reason",
        action="append",
        default=[],
        choices=EXCLUSION_REASONS,
        help="Only archive trials with this exclusion reason. Can be repeated.",
    )
    trials_archive_parser.add_argument(
        "--apply",
        action="store_true",
        help="Move matched trials. Without this flag, only print a dry run.",
    )
    trials_archive_parser.set_defaults(handler=handle_trials_archive_excluded)


def add_runs_dir_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )


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
            str(result_files_changed_count(result)),
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
                summary.reasoning_effort or "unknown",
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
                _format_review_labels(summary.secondary_review_labels),
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
            "effort",
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
            "primary_reviews",
            "secondary_reviews",
            "exclusions",
        ],
        rows,
    )
    return 0


def handle_trials_archive_excluded(args: argparse.Namespace) -> int:
    try:
        result = archive_excluded_trials(
            Path(args.runs_dir),
            archive_dir=Path(args.archive_dir) if args.archive_dir else None,
            exclusion_reasons=args.exclusion_reason,
            apply=args.apply,
        )
    except OSError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    action = "Would archive" if result.dry_run else "Archived"
    if not result.candidates:
        print("No reviewed excluded trials matched.")
        return 0

    for candidate in result.candidates:
        print(
            f"{action}: {candidate.trial_id} "
            f"({candidate.exclusion_reason}) -> {candidate.archived_run_dir}"
        )
    if result.dry_run:
        print("Dry run only. Re-run with --apply to move artifacts.")
    elif result.manifest_path:
        print(f"Archive manifest: {result.manifest_path}")
    return 0


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


def _format_review_labels(labels: object) -> str:
    if not isinstance(labels, dict) or not labels:
        return ""
    return ",".join(f"{label}:{count}" for label, count in labels.items())
