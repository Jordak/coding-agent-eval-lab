from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.review import FAILURE_LABELS, load_review, resolve_run_dir, write_review
from agentlab.validity import (
    DEFAULT_TRIAL_VALIDITY,
    EXCLUDED_TRIAL_VALIDITY,
    EXCLUSION_REASONS,
    TRIAL_VALIDITIES,
)


def add_review_command(subcommands: argparse._SubParsersAction) -> None:
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

    review = load_review(run_dir)
    print(f"Review: {review_path}")
    trial_validity = review.trial_validity if review is not None else validity
    print(f"Validity: {trial_validity}")
    if trial_validity == EXCLUDED_TRIAL_VALIDITY:
        exclusion_reason = review.exclusion_reason if review is not None else "unknown"
        print(f"Exclusion: {exclusion_reason or 'unknown'}")
    return 0
