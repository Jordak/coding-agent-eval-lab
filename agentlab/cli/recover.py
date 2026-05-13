from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlab.codex_runtime_metadata import recover_codex_runtime_metadata
from agentlab.evidence_sets import load_evidence_set


def add_recover_command(subcommands: argparse._SubParsersAction) -> None:
    recover_parser = subcommands.add_parser(
        "recover",
        help="Recover explicit metadata for historical trial artifacts.",
    )
    recover_subcommands = recover_parser.add_subparsers(dest="recover_command")

    codex_parser = recover_subcommands.add_parser(
        "codex-runtime-metadata",
        help="Recover Codex model metadata from a local Codex state database.",
    )
    codex_parser.add_argument(
        "--evidence-set",
        required=True,
        help="Evidence-set JSON file selecting the Codex trial results to update.",
    )
    codex_parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where trial artifacts are stored.",
    )
    codex_parser.add_argument(
        "--codex-state-db",
        required=True,
        help="Codex state SQLite database, for example ~/.codex/state_5.sqlite.",
    )
    codex_parser.add_argument(
        "--dry-run",
        nargs="?",
        const=True,
        default=True,
        type=_parse_bool,
        metavar="{true,false}",
        help=(
            "Preview changes without writing result.json files. Defaults to "
            "true; pass --dry-run=false to write recovered metadata."
        ),
    )
    codex_parser.set_defaults(handler=handle_recover_codex_runtime_metadata)


def handle_recover_codex_runtime_metadata(args: argparse.Namespace) -> int:
    state_db = Path(args.codex_state_db).expanduser()
    if not state_db.is_file():
        print(f"ERROR Codex state database not found: {state_db}", file=sys.stderr)
        return 1

    try:
        evidence_set = load_evidence_set(
            Path(args.evidence_set),
            Path(args.runs_dir),
        )
    except (OSError, ValueError) as exc:
        _print_evidence_set_error(exc, Path(args.runs_dir))
        return 1

    dry_run = bool(args.dry_run)
    apply_changes = not dry_run
    summary = recover_codex_runtime_metadata(
        evidence_set.result_files,
        codex_state_db=state_db,
        apply=apply_changes,
    )
    for entry in summary.entries:
        model = entry.model_name or "unknown"
        thread = entry.thread_id or "unknown"
        print(
            f"{entry.status}: {entry.result_path} "
            f"(thread={thread}, model={model}) - {entry.message}"
        )

    action = "updated" if apply_changes else "would update"
    print(
        "Codex runtime metadata recovery: "
        f"{len(summary.changed_entries)} {action}; "
        f"{len(summary.error_entries)} errors; "
        f"{len(summary.entries)} selected."
    )
    if not apply_changes:
        print(
            "Dry run only. Re-run with --dry-run=false to write result.json files."
        )

    return 1 if summary.error_entries else 0


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(
        "expected one of true, false, yes, no, 1, or 0"
    )


def _print_evidence_set_error(exc: Exception, runs_dir: Path) -> None:
    print(f"ERROR {exc}", file=sys.stderr)
    if not runs_dir.exists():
        print(
            "Hint: --runs-dir does not exist. Historical run artifacts are "
            "often local and gitignored; pass the directory that contains "
            "the selected run folders.",
            file=sys.stderr,
        )
