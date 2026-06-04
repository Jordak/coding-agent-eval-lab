from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from agentlab.evidence.snapshots import load_evidence_snapshot


@dataclass(frozen=True)
class EvidenceSetPortabilityReport:
    source_path: Path
    selected_entries: int
    snapshot_path: Path | None
    snapshot_records: int | None
    errors: tuple[str, ...]

    @property
    def is_portable(self) -> bool:
        return not self.errors


def check_evidence_set_portability(path: Path) -> EvidenceSetPortabilityReport:
    source_path = path.resolve()
    errors: list[str] = []
    selected_entries = 0
    snapshot_path: Path | None = None
    snapshot_records: int | None = None

    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return EvidenceSetPortabilityReport(
            source_path=source_path,
            selected_entries=0,
            snapshot_path=None,
            snapshot_records=None,
            errors=(f"evidence set must be JSON: {exc}",),
        )
    except OSError as exc:
        return EvidenceSetPortabilityReport(
            source_path=source_path,
            selected_entries=0,
            snapshot_path=None,
            snapshot_records=None,
            errors=(f"could not read evidence set: {exc}",),
        )

    if not isinstance(raw, Mapping):
        errors.append("evidence set must contain a JSON object")
    else:
        entries = raw.get("trials")
        if isinstance(entries, list):
            selected_entries = len(entries)
            if not entries:
                errors.append("evidence set requires a non-empty trials list")
        else:
            errors.append("evidence set requires a trials list")

        raw_snapshot = raw.get("outcome_evidence_snapshot")
        if raw_snapshot is None:
            errors.append(
                "missing outcome_evidence_snapshot; selected evidence would "
                "depend on local runs"
            )
        elif not isinstance(raw_snapshot, str) or not raw_snapshot.strip():
            errors.append("outcome_evidence_snapshot must be a non-empty string")
        else:
            snapshot_path = _resolve_snapshot_path(raw_snapshot, source_path.parent)
            try:
                snapshot_results = load_evidence_snapshot(snapshot_path)
            except (OSError, ValueError) as exc:
                errors.append(f"could not load outcome evidence snapshot: {exc}")
            else:
                snapshot_records = len(snapshot_results)
                if selected_entries and snapshot_records != selected_entries:
                    errors.append(
                        "snapshot record count does not match selected trials: "
                        f"{snapshot_records} != {selected_entries}"
                    )

    return EvidenceSetPortabilityReport(
        source_path=source_path,
        selected_entries=selected_entries,
        snapshot_path=snapshot_path,
        snapshot_records=snapshot_records,
        errors=tuple(errors),
    )


def _resolve_snapshot_path(raw_snapshot: str, manifest_dir: Path) -> Path:
    snapshot_path = Path(raw_snapshot)
    if snapshot_path.is_absolute():
        return snapshot_path
    return (manifest_dir / snapshot_path).resolve()
