from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from agentlab.human_review import (
    HumanReviewOutcome,
    create_human_review_outcome,
    human_review_outcome_from_mapping,
    human_review_outcome_to_mapping,
)
from agentlab.taxonomy import FAILURE_LABELS
from agentlab.validity import DEFAULT_TRIAL_VALIDITY


class ReviewArtifactError(ValueError):
    exit_code = 1

    def cli_message(self) -> str:
        return f"ERROR {self}"


def write_review(
    run_dir: Path,
    primary_label: str,
    note: str,
    secondary_labels: Iterable[str] = (),
    evidence: Iterable[str] = (),
    trial_validity: str = DEFAULT_TRIAL_VALIDITY,
    exclusion_reason: str | None = None,
) -> Path:
    review = create_human_review_outcome(
        primary_label=primary_label,
        note=note,
        secondary_labels=secondary_labels,
        evidence=evidence,
        trial_validity=trial_validity,
        exclusion_reason=exclusion_reason,
    )
    review_path = run_dir / "review.json"
    review_path.write_text(
        json.dumps(
            human_review_outcome_to_mapping(review),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return review_path


def load_review(run_dir: Path) -> HumanReviewOutcome | None:
    review_path = run_dir / "review.json"
    if not review_path.exists():
        return None
    try:
        raw = json.loads(review_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReviewArtifactError(f"could not read review artifact: {review_path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewArtifactError(f"review artifact must be JSON: {review_path}") from exc
    if not isinstance(raw, dict):
        raise ReviewArtifactError(f"review artifact must contain an object: {review_path}")
    try:
        return human_review_outcome_from_mapping(raw)
    except ValueError as exc:
        raise ReviewArtifactError(f"invalid review artifact: {review_path}: {exc}") from exc


def resolve_run_dir(runs_dir: Path, run: str) -> Path:
    if run != "latest":
        return Path(run)

    candidates = sorted(path for path in runs_dir.iterdir() if path.is_dir())
    if not candidates:
        raise FileNotFoundError(f"no runs found in {runs_dir}")
    return candidates[-1]
