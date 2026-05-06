from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


FAILURE_LABELS = [
    "success_clean",
    "success_messy",
    "context_miss",
    "spec_misread",
    "bad_local_fix",
    "test_gap",
    "over_edit",
    "tool_misuse",
    "dependency_issue",
    "stuck_or_timeout",
    "unsafe_action",
]


def write_review(
    run_dir: Path,
    primary_label: str,
    note: str,
    secondary_labels: Iterable[str] = (),
    evidence: Iterable[str] = (),
) -> Path:
    labels = [primary_label] + list(secondary_labels)
    invalid = [label for label in labels if label not in FAILURE_LABELS]
    if invalid:
        raise ValueError(f"unknown review label(s): {', '.join(invalid)}")

    review = {
        "primary_label": primary_label,
        "secondary_labels": list(secondary_labels),
        "note": note,
        "evidence": list(evidence),
    }
    review_path = run_dir / "review.json"
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
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
