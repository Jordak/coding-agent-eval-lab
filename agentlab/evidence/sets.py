from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class EvidenceSet:
    name: str
    description: str
    source_path: Path
    trial_entries: list[str]
    result_files: list[Path]

    def digest_context(self) -> dict[str, object]:
        context: dict[str, object] = {
            "name": self.name,
            "source_path": str(self.source_path),
            "selected_entries": len(self.trial_entries),
            "selected_result_files": len(self.result_files),
        }
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
    result_files = [
        _resolve_result_file(entry, manifest_dir=source_path.parent, runs_dir=runs_dir)
        for entry in entries
    ]
    return EvidenceSet(
        name=str(raw.get("name") or path.stem),
        description=str(raw.get("description") or ""),
        source_path=source_path,
        trial_entries=list(entries),
        result_files=result_files,
    )


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
