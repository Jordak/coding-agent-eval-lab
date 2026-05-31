from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agentlab.evidence.outcome import load_outcome_evidence
from agentlab.evidence.results import discover_result_files


@dataclass(frozen=True)
class ArchiveCandidate:
    run_dir: Path
    archive_dir: Path
    trial_id: str
    task_id: str
    agent_name: str
    exclusion_reason: str

    @property
    def archived_run_dir(self) -> Path:
        return self.archive_dir / "excluded" / self.exclusion_reason / self.run_dir.name


@dataclass(frozen=True)
class ArchiveResult:
    dry_run: bool
    candidates: list[ArchiveCandidate]
    manifest_path: Path | None = None


def plan_excluded_trial_archive(
    runs_dir: Path,
    archive_dir: Path | None = None,
    exclusion_reasons: list[str] | None = None,
) -> list[ArchiveCandidate]:
    archive_root = archive_dir or runs_dir / "_archive"
    reason_filter = set(exclusion_reasons or [])
    candidates: list[ArchiveCandidate] = []

    for result_path in discover_result_files(runs_dir):
        run_dir = result_path.parent
        if not (run_dir / "review.json").is_file():
            continue
        evidence = load_outcome_evidence(result_path)
        if evidence is None:
            continue
        if evidence.is_valid_trial:
            continue
        reason = evidence.exclusion_reason_display or "unknown"
        if reason_filter and reason not in reason_filter:
            continue
        candidates.append(
            ArchiveCandidate(
                run_dir=run_dir,
                archive_dir=archive_root,
                trial_id=evidence.trial_id or run_dir.name,
                task_id=evidence.task_id,
                agent_name=evidence.agent_name,
                exclusion_reason=reason,
            )
        )

    return candidates


def archive_excluded_trials(
    runs_dir: Path,
    archive_dir: Path | None = None,
    exclusion_reasons: list[str] | None = None,
    apply: bool = False,
) -> ArchiveResult:
    candidates = plan_excluded_trial_archive(
        runs_dir,
        archive_dir=archive_dir,
        exclusion_reasons=exclusion_reasons,
    )
    if not apply:
        return ArchiveResult(dry_run=True, candidates=candidates)

    archive_root = archive_dir or runs_dir / "_archive"
    manifest_path = archive_root / "archive-manifest.jsonl"
    archive_root.mkdir(parents=True, exist_ok=True)

    manifest_entries = []
    archived_at = datetime.now(timezone.utc).isoformat()
    for candidate in candidates:
        destination = candidate.archived_run_dir
        if destination.exists():
            raise FileExistsError(f"archive destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(candidate.run_dir), str(destination))
        manifest_entries.append(_manifest_entry(candidate, destination, archived_at))

    if manifest_entries:
        with manifest_path.open("a", encoding="utf-8") as handle:
            for entry in manifest_entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

    return ArchiveResult(
        dry_run=False,
        candidates=candidates,
        manifest_path=manifest_path if manifest_entries else None,
    )


def _manifest_entry(
    candidate: ArchiveCandidate,
    archived_run_dir: Path,
    archived_at: str,
) -> dict[str, str]:
    return {
        "agent_harness": candidate.agent_name,
        "archived_at": archived_at,
        "archived_path": str(archived_run_dir),
        "exclusion_reason": candidate.exclusion_reason,
        "original_path": str(candidate.run_dir),
        "task_id": candidate.task_id,
        "trial_id": candidate.trial_id,
    }
