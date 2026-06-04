from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.evidence.portability import check_evidence_set_portability
from agentlab.evidence.sets import load_evidence_set
from agentlab.evidence.outcome import load_outcome_evidences
from agentlab.evidence.results import discover_result_files
from agentlab.evidence.snapshots import write_evidence_snapshot
from agentlab.reports.capability_digest import render_capability_evidence_digest
from agentlab.reports.capability_digest_html import (
    render_capability_evidence_digest_html,
)


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
        action="append",
        default=[],
        help=(
            "JSON file selecting the trial result files to include in the "
            "capability evidence digest. Can be repeated to combine selected "
            "evidence sets in one digest."
        ),
    )
    evidence_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown file to write. Defaults to stdout.",
    )
    evidence_parser.add_argument(
        "--html-output",
        default=None,
        help=(
            "Optional static HTML companion file to write. The HTML report "
            "uses the canonical audit layout and does not replace Markdown."
        ),
    )
    evidence_parser.add_argument(
        "--snapshot-output",
        default=None,
        help=(
            "Optional durable OutcomeEvidence snapshot JSON file to write for "
            "regenerating reports after local runs are removed."
        ),
    )
    evidence_parser.set_defaults(handler=handle_report_capability_evidence_digest)

    portability_parser = report_subcommands.add_parser(
        "check-evidence-portability",
        help=(
            "Check that selected evidence manifests have durable "
            "OutcomeEvidence snapshots."
        ),
    )
    portability_parser.add_argument(
        "--evidence-set",
        action="append",
        required=True,
        help=(
            "Evidence-set JSON file to check. Repeat for every manifest "
            "created or updated by a report/evidence branch."
        ),
    )
    portability_parser.set_defaults(handler=handle_report_check_evidence_portability)


def handle_report_capability_evidence_digest(args: argparse.Namespace) -> int:
    selection_context = None
    evidence_set_paths = _evidence_set_paths(args.evidence_set)
    if evidence_set_paths:
        results = []
        evidence_set_contexts = []
        selected_entries = 0
        selected_result_files = 0
        result_file_sources: dict[Path, str] = {}
        result_id_sources: dict[str, str] = {}
        for evidence_set_path in evidence_set_paths:
            try:
                evidence_set = load_evidence_set(
                    Path(evidence_set_path),
                    Path(args.runs_dir),
                )
            except (OSError, ValueError) as exc:
                print(f"ERROR {exc}", file=sys.stderr)
                return 1
            try:
                if evidence_set.snapshot_results is not None:
                    set_results = list(evidence_set.snapshot_results)
                else:
                    for result_file in evidence_set.result_files:
                        resolved_result_file = result_file.resolve()
                        if resolved_result_file in result_file_sources:
                            first_source = result_file_sources[resolved_result_file]
                            print(
                                "ERROR duplicate evidence-set result selected: "
                                f"{result_file} appears in both {first_source} and "
                                f"{evidence_set.source_path}",
                                file=sys.stderr,
                            )
                            return 1
                        result_file_sources[resolved_result_file] = str(
                            evidence_set.source_path
                        )
                    set_results = load_outcome_evidences(evidence_set.result_files)
            except OSError as exc:
                print(f"ERROR {exc}", file=sys.stderr)
                return 1
            for result in set_results:
                result_id = result.trial_id or result.run_id
                if not result_id:
                    continue
                if result_id in result_id_sources:
                    first_source = result_id_sources[result_id]
                    print(
                        "ERROR duplicate evidence-set result selected: "
                        f"{result_id} appears in both {first_source} and "
                        f"{evidence_set.source_path}",
                        file=sys.stderr,
                    )
                    return 1
                result_id_sources[result_id] = str(evidence_set.source_path)
            results.extend(set_results)
            context = evidence_set.digest_context()
            evidence_set_contexts.append(context)
            selected_entries += int(context.get("selected_entries") or 0)
            selected_result_files += int(context.get("selected_result_files") or 0)
        if len(evidence_set_contexts) == 1:
            selection_context = evidence_set_contexts[0]
        else:
            selection_context = {
                "evidence_sets": evidence_set_contexts,
                "selected_entries": selected_entries,
                "selected_result_files": selected_result_files,
            }
    else:
        result_files = discover_result_files(Path(args.runs_dir))
        results = load_outcome_evidences(result_files)
    if not results:
        print("No result.json files found.", file=sys.stderr)
        return 1

    digest = render_capability_evidence_digest(results, selection_context)
    output_path = Path(args.output) if args.output else None
    html_output_path = Path(args.html_output) if args.html_output else None
    snapshot_output_path = (
        Path(args.snapshot_output)
        if getattr(args, "snapshot_output", None)
        else None
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(digest, encoding="utf-8")
        print(f"Capability evidence digest: {output_path}")

    if snapshot_output_path:
        write_evidence_snapshot(snapshot_output_path, results)
        print(f"Outcome evidence snapshot: {snapshot_output_path}")

    if html_output_path:
        html_output_path.parent.mkdir(parents=True, exist_ok=True)
        html_report = render_capability_evidence_digest_html(
            results,
            selection_context,
            source_path=output_path,
            output_path=html_output_path,
            repo_root=Path.cwd(),
        )
        html_output_path.write_text(html_report, encoding="utf-8")
        output_stream = sys.stdout if output_path else sys.stderr
        print(f"Capability evidence digest HTML: {html_output_path}", file=output_stream)

    if output_path:
        return 0

    print(digest)
    return 0


def _evidence_set_paths(raw_evidence_set: object) -> list[str]:
    if raw_evidence_set is None:
        return []
    if isinstance(raw_evidence_set, str):
        return [raw_evidence_set]
    if isinstance(raw_evidence_set, list):
        return [str(path) for path in raw_evidence_set if str(path).strip()]
    return [str(raw_evidence_set)]


def handle_report_check_evidence_portability(args: argparse.Namespace) -> int:
    evidence_set_paths = _evidence_set_paths(args.evidence_set)
    if not evidence_set_paths:
        print("ERROR at least one --evidence-set is required", file=sys.stderr)
        return 1

    has_error = False
    for raw_path in evidence_set_paths:
        report = check_evidence_set_portability(Path(raw_path))
        if report.is_portable:
            snapshot = report.snapshot_path or Path("<missing>")
            print(
                "OK evidence set portable: "
                f"{report.source_path} "
                f"snapshot={snapshot} "
                f"records={report.snapshot_records}"
            )
            continue

        has_error = True
        print(
            f"ERROR evidence set is not portable: {report.source_path}",
            file=sys.stderr,
        )
        for error in report.errors:
            print(f"  - {error}", file=sys.stderr)

    return 1 if has_error else 0
