from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agentlab.taxonomy import FAILURE_LABELS
from agentlab.validity import (
    DEFAULT_TRIAL_VALIDITY,
    EXCLUDED_TRIAL_VALIDITY,
    EXCLUSION_REASONS,
    normalize_trial_validity,
)


def write_review(
    run_dir: Path,
    primary_label: str,
    note: str,
    secondary_labels: Iterable[str] = (),
    evidence: Iterable[str] = (),
    trial_validity: str = DEFAULT_TRIAL_VALIDITY,
    exclusion_reason: str | None = None,
) -> Path:
    labels = [primary_label] + list(secondary_labels)
    invalid = [label for label in labels if label not in FAILURE_LABELS]
    if invalid:
        raise ValueError(f"unknown review label(s): {', '.join(invalid)}")

    trial_validity = normalize_trial_validity(trial_validity)
    if trial_validity == EXCLUDED_TRIAL_VALIDITY:
        if exclusion_reason is None and primary_label in EXCLUSION_REASONS:
            exclusion_reason = primary_label
        if exclusion_reason not in EXCLUSION_REASONS:
            raise ValueError(
                "excluded trials require an exclusion reason: "
                + ", ".join(EXCLUSION_REASONS)
            )
    elif exclusion_reason:
        raise ValueError("valid trials cannot have an exclusion reason")

    review = {
        "exclusion_reason": exclusion_reason,
        "primary_label": primary_label,
        "secondary_labels": list(secondary_labels),
        "note": note,
        "evidence": list(evidence),
        "trial_validity": trial_validity,
    }
    review_path = run_dir / "review.json"
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    _update_result_metadata(run_dir, review)
    return review_path


def load_review(run_dir: Path) -> Dict[str, Any] | None:
    review_path = run_dir / "review.json"
    if not review_path.exists():
        return None
    try:
        return json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def resolve_run_dir(runs_dir: Path, run: str) -> Path:
    if run != "latest":
        return Path(run)

    candidates = sorted(path for path in runs_dir.iterdir() if path.is_dir())
    if not candidates:
        raise FileNotFoundError(f"no runs found in {runs_dir}")
    return candidates[-1]


def _update_result_metadata(run_dir: Path, review: Dict[str, Any]) -> None:
    result_path = run_dir / "result.json"
    if not result_path.exists():
        return

    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    result["review"] = review
    result["trial_validity"] = review["trial_validity"]
    result["exclusion_reason"] = review["exclusion_reason"]
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
