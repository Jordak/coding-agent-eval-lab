from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.evidence.review_artifacts import resolve_run_dir
from agentlab.evidence.review_proposals import (
    DEFAULT_REVIEWER_IDENTITY,
    DeterministicReviewProposer,
    ReviewProposalArtifactError,
    clear_review_proposal,
    create_review_proposal,
    generate_review_proposal_for_run,
    generate_review_proposals_for_results,
    write_review_proposal,
)
from agentlab.evidence.sets import load_evidence_set
from agentlab.evidence.taxonomy import FAILURE_LABELS
from agentlab.evidence.validity import (
    DEFAULT_TRIAL_VALIDITY,
    EXCLUDED_TRIAL_VALIDITY,
    EXCLUSION_REASONS,
    TRIAL_VALIDITIES,
)


def add_review_proposal_commands(subcommands: argparse._SubParsersAction) -> None:
    proposals_parser = subcommands.add_parser(
        "review-proposals",
        help="Create, inspect, or clear draft review proposal artifacts.",
    )
    proposal_subcommands = proposals_parser.add_subparsers(
        dest="review_proposals_command"
    )

    run_parser = proposal_subcommands.add_parser(
        "run",
        help="Generate a heuristic review proposal for one trial directory.",
    )
    run_parser.add_argument(
        "--run",
        "--trial",
        required=True,
        dest="run",
        help="Trial directory to propose a review for, or 'latest'.",
    )
    run_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored when --run latest is used.",
    )
    run_parser.add_argument(
        "--reviewer",
        default=DEFAULT_REVIEWER_IDENTITY,
        help="Identity to persist as the proposing reviewer.",
    )
    run_parser.set_defaults(handler=handle_review_proposals_run)

    evidence_set_parser = proposal_subcommands.add_parser(
        "evidence-set",
        help="Generate heuristic review proposals for every trial in an evidence set.",
    )
    evidence_set_parser.add_argument(
        "--evidence-set",
        required=True,
        help="JSON evidence set selecting trial result files to propose reviews for.",
    )
    evidence_set_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    evidence_set_parser.add_argument(
        "--reviewer",
        default=DEFAULT_REVIEWER_IDENTITY,
        help="Identity to persist as the proposing reviewer.",
    )
    evidence_set_parser.set_defaults(handler=handle_review_proposals_evidence_set)

    write_parser = proposal_subcommands.add_parser(
        "write",
        help="Write an explicit draft review proposal without applying it.",
    )
    write_parser.add_argument(
        "--run",
        "--trial",
        required=True,
        dest="run",
        help="Trial directory to write a draft proposal for, or 'latest'.",
    )
    write_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored when --run latest is used.",
    )
    write_parser.add_argument(
        "--label",
        required=True,
        choices=FAILURE_LABELS,
        help="Proposed primary failure/success label.",
    )
    write_parser.add_argument(
        "--secondary",
        action="append",
        default=[],
        choices=FAILURE_LABELS,
        help="Optional proposed secondary label. Can be repeated.",
    )
    write_parser.add_argument(
        "--note",
        required=True,
        help="Proposed human review note.",
    )
    write_parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Evidence such as a failing command, diff hunk, or transcript excerpt.",
    )
    write_parser.add_argument(
        "--validity",
        default=None,
        choices=TRIAL_VALIDITIES,
        help="Whether this trial is proposed to count in fair capability summaries.",
    )
    write_parser.add_argument(
        "--exclude",
        action="store_true",
        help="Propose excluding this trial from fair capability summaries.",
    )
    write_parser.add_argument(
        "--exclusion-reason",
        default=None,
        choices=EXCLUSION_REASONS,
        help="Reason an excluded trial is proposed not to count in fair summaries.",
    )
    write_parser.add_argument(
        "--confidence",
        required=True,
        type=float,
        help="Proposal confidence from 0 to 1.",
    )
    write_parser.add_argument(
        "--reviewer",
        default=DEFAULT_REVIEWER_IDENTITY,
        help="Identity to persist as the proposing reviewer.",
    )
    write_parser.set_defaults(handler=handle_review_proposals_write)

    clear_parser = proposal_subcommands.add_parser(
        "clear",
        help="Remove a draft review proposal after it is applied or abandoned.",
    )
    clear_parser.add_argument(
        "--run",
        "--trial",
        required=True,
        dest="run",
        help="Trial directory to clear a draft proposal from, or 'latest'.",
    )
    clear_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored when --run latest is used.",
    )
    clear_parser.set_defaults(handler=handle_review_proposals_clear)


def handle_review_proposals_run(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run_dir(Path(args.runs_dir), args.run)
        proposer = DeterministicReviewProposer(reviewer_identity=args.reviewer)
        proposal_path, proposal = generate_review_proposal_for_run(run_dir, proposer)
    except (OSError, ValueError, FileNotFoundError, ReviewProposalArtifactError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print(f"Heuristic review proposal: {proposal_path}")
    print(f"Proposed label: {proposal.proposed_primary_label}")
    print(f"Validity: {proposal.proposed_trial_validity}")
    if proposal.proposed_exclusion_reason:
        print(f"Exclusion: {proposal.proposed_exclusion_reason}")
    return 0


def handle_review_proposals_evidence_set(args: argparse.Namespace) -> int:
    try:
        evidence_set = load_evidence_set(
            Path(args.evidence_set),
            Path(args.runs_dir),
        )
        proposer = DeterministicReviewProposer(reviewer_identity=args.reviewer)
        generated = generate_review_proposals_for_results(
            evidence_set.result_files,
            proposer,
        )
    except (OSError, ValueError, FileNotFoundError, ReviewProposalArtifactError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    for proposal_path, proposal in generated:
        print(
            "Heuristic review proposal: "
            f"{proposal_path} ({proposal.proposed_primary_label}, "
            f"{proposal.proposed_trial_validity})"
        )
    print(f"Generated heuristic review proposals: {len(generated)}")
    return 0


def handle_review_proposals_write(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run_dir(Path(args.runs_dir), args.run)
        validity = args.validity or DEFAULT_TRIAL_VALIDITY
        if args.exclude:
            if args.validity == DEFAULT_TRIAL_VALIDITY:
                raise ValueError("--exclude conflicts with --validity valid")
            validity = EXCLUDED_TRIAL_VALIDITY
        proposal = create_review_proposal(
            proposed_primary_label=args.label,
            proposed_note=args.note,
            proposed_secondary_labels=args.secondary,
            evidence=args.evidence,
            proposed_trial_validity=validity,
            proposed_exclusion_reason=args.exclusion_reason,
            confidence=args.confidence,
            reviewer_identity=args.reviewer,
        )
        proposal_path = write_review_proposal(run_dir, proposal)
    except (OSError, ValueError, FileNotFoundError, ReviewProposalArtifactError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print(f"Review proposal: {proposal_path}")
    print(f"Proposed label: {proposal.proposed_primary_label}")
    print(f"Validity: {proposal.proposed_trial_validity}")
    if proposal.proposed_exclusion_reason:
        print(f"Exclusion: {proposal.proposed_exclusion_reason}")
    return 0


def handle_review_proposals_clear(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run_dir(Path(args.runs_dir), args.run)
        proposal_path = clear_review_proposal(run_dir)
    except (OSError, ValueError, FileNotFoundError, ReviewProposalArtifactError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    if proposal_path is None:
        print(f"No review proposal found for: {run_dir}")
    else:
        print(f"Cleared review proposal: {proposal_path}")
    return 0
