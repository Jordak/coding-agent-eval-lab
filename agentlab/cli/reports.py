from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.comparison import (
    ComparisonEvidenceSource,
    render_comparison_evidence_digest,
)
from agentlab.evidence import render_capability_evidence_digest
from agentlab.evidence_sets import load_evidence_set
from agentlab.results import discover_result_files, load_results


def add_report_commands(subcommands: argparse._SubParsersAction) -> None:
    report_parser = subcommands.add_parser(
        "report",
        help="Generate report-support artifacts from stored trial evidence.",
    )
    report_subcommands = report_parser.add_subparsers(dest="report_command")

    evidence_parser = report_subcommands.add_parser(
        "capability-evidence-digest",
        aliases=["evidence-appendix"],
        help="Generate a capability evidence digest from stored trial results.",
    )
    evidence_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    evidence_parser.add_argument(
        "--evidence-set",
        default=None,
        help=(
            "JSON file selecting the trial result files to include in the "
            "capability evidence digest."
        ),
    )
    evidence_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown file to write. Defaults to stdout.",
    )
    evidence_parser.set_defaults(handler=handle_report_capability_evidence_digest)

    comparison_parser = report_subcommands.add_parser(
        "comparison-evidence-digest",
        help=(
            "Generate a comparison evidence digest from multiple evidence-set "
            "manifests."
        ),
    )
    comparison_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    comparison_parser.add_argument(
        "--evidence-set",
        action="append",
        default=[],
        help=(
            "JSON file selecting trial result files to include. Provide this "
            "option two or more times."
        ),
    )
    comparison_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown file to write. Defaults to stdout.",
    )
    comparison_parser.set_defaults(handler=handle_report_comparison_evidence_digest)


def handle_report_capability_evidence_digest(args: argparse.Namespace) -> int:
    selection_context = None
    if args.evidence_set:
        try:
            evidence_set = load_evidence_set(
                Path(args.evidence_set),
                Path(args.runs_dir),
            )
        except (OSError, ValueError) as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        result_files = evidence_set.result_files
        selection_context = evidence_set.digest_context()
    else:
        result_files = discover_result_files(Path(args.runs_dir))
    results = load_results(result_files)
    if not results:
        print("No result.json files found.", file=sys.stderr)
        return 1

    digest = render_capability_evidence_digest(results, selection_context)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(digest, encoding="utf-8")
        print(f"Capability evidence digest: {output_path}")
        return 0

    print(digest)
    return 0


def handle_report_comparison_evidence_digest(args: argparse.Namespace) -> int:
    if len(args.evidence_set) < 2:
        print(
            "ERROR comparison evidence digest requires at least two "
            "--evidence-set values",
            file=sys.stderr,
        )
        return 1

    sources: list[ComparisonEvidenceSource] = []
    for evidence_set_path in args.evidence_set:
        try:
            evidence_set = load_evidence_set(
                Path(evidence_set_path),
                Path(args.runs_dir),
            )
        except (OSError, ValueError) as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        results = load_results(evidence_set.result_files)
        if not results:
            print(
                f"ERROR no agent-trial result files found for {evidence_set_path}",
                file=sys.stderr,
            )
            return 1
        sources.append(
            ComparisonEvidenceSource.from_evidence_set(evidence_set, results)
        )

    digest = render_comparison_evidence_digest(sources)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(digest, encoding="utf-8")
        print(f"Comparison evidence digest: {output_path}")
        return 0

    print(digest)
    return 0
