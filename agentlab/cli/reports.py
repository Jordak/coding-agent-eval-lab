from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.evidence import render_capability_evidence_digest
from agentlab.evidence_sets import load_evidence_set
from agentlab.outcome_evidence import load_outcome_evidences
from agentlab.results import discover_result_files


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
    results = load_outcome_evidences(result_files)
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
