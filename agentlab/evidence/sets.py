from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from agentlab.evidence.outcome import OutcomeEvidence
from agentlab.evidence.snapshots import load_evidence_snapshot


@dataclass(frozen=True)
class EvidenceSet:
    name: str
    description: str
    source_path: Path
    trial_entries: list[str]
    result_files: list[Path]
    snapshot_path: Path | None = None
    snapshot_results: list[OutcomeEvidence] | None = None

    def digest_context(self) -> dict[str, object]:
        selected_result_files = len(self.result_files)
        if self.snapshot_results is not None:
            selected_result_files = len(self.snapshot_results)
        context: dict[str, object] = {
            "name": self.name,
            "source_path": _display_source_path(self.source_path),
            "selected_entries": len(self.trial_entries),
            "selected_result_files": selected_result_files,
        }
        if self.snapshot_path is not None:
            context["outcome_evidence_snapshot"] = _display_source_path(
                self.snapshot_path
            )
            context["selected_snapshot_records"] = len(self.snapshot_results or [])
        if self.description:
            context["description"] = self.description
        return context


def load_evidence_set(path: Path, runs_dir: Path) -> EvidenceSet:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"evidence set must be JSON: {path}") from exc
    except OSError as exc:
        raise FileNotFoundError(str(exc)) from exc

    if not isinstance(raw, Mapping):
        raise ValueError("evidence set must contain a JSON object")

    entries = raw.get("trials")
    if not isinstance(entries, list) or not entries:
        raise ValueError("evidence set requires a non-empty trials list")
    if not all(isinstance(entry, str) and entry.strip() for entry in entries):
        raise ValueError("evidence set trials must be non-empty strings")

    source_path = path.resolve()
    snapshot_path = _snapshot_path(raw, source_path.parent)
    snapshot_results = None
    if snapshot_path is not None:
        snapshot_results = load_evidence_snapshot(snapshot_path)

    result_files = []
    if snapshot_results is None:
        result_files = [
            _resolve_result_file(
                entry,
                manifest_dir=source_path.parent,
                runs_dir=runs_dir,
            )
            for entry in entries
        ]
    else:
        result_files = [
            result_file
            for entry in entries
            for result_file in [
                _optional_result_file(
                    entry,
                    manifest_dir=source_path.parent,
                    runs_dir=runs_dir,
                )
            ]
            if result_file is not None
        ]
    return EvidenceSet(
        name=str(raw.get("name") or path.stem),
        description=str(raw.get("description") or ""),
        source_path=source_path,
        trial_entries=list(entries),
        result_files=result_files,
        snapshot_path=snapshot_path,
        snapshot_results=snapshot_results,
    )


def _display_source_path(path: Path) -> str:
    resolved_path = path.resolve()
    try:
        return str(resolved_path.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(resolved_path)


def _snapshot_path(raw: Mapping[str, object], manifest_dir: Path) -> Path | None:
    raw_snapshot = raw.get("outcome_evidence_snapshot")
    if raw_snapshot is None:
        return None
    if not isinstance(raw_snapshot, str) or not raw_snapshot.strip():
        raise ValueError("outcome_evidence_snapshot must be a non-empty string")
    snapshot_path = Path(raw_snapshot)
    if snapshot_path.is_absolute():
        return snapshot_path
    return (manifest_dir / snapshot_path).resolve()


def _optional_result_file(entry: str, manifest_dir: Path, runs_dir: Path) -> Path | None:
    try:
        return _resolve_result_file(entry, manifest_dir=manifest_dir, runs_dir=runs_dir)
    except FileNotFoundError:
        return None


def _resolve_result_file(entry: str, manifest_dir: Path, runs_dir: Path) -> Path:
    raw_path = Path(entry)
    candidates: list[Path] = []

    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.extend(
            [
                manifest_dir / raw_path,
                Path.cwd() / raw_path,
                runs_dir / raw_path,
            ]
        )

    expanded_candidates: list[Path] = []
    for candidate in candidates:
        expanded_candidates.append(candidate)
        if candidate.suffix != ".json":
            expanded_candidates.append(candidate / "result.json")

    for candidate in expanded_candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"evidence set trial result not found: {entry}")
