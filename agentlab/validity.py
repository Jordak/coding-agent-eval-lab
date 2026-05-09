from __future__ import annotations

from typing import Any, Dict

DEFAULT_TRIAL_VALIDITY = "valid"
EXCLUDED_TRIAL_VALIDITY = "excluded"

TRIAL_VALIDITIES = [
    DEFAULT_TRIAL_VALIDITY,
    EXCLUDED_TRIAL_VALIDITY,
]

EXCLUSION_REASONS = [
    "dependency_issue",
    "eval_harness_error",
    "setup_error",
    "operator_error",
    "invalid_task",
    "unknown",
]

LEGACY_EXCLUSION_REASON_ALIASES = {
    "harness_error": "eval_harness_error",
}


def normalize_trial_validity(value: object) -> str:
    if value is None or value == "":
        return DEFAULT_TRIAL_VALIDITY
    value = str(value)
    if value not in TRIAL_VALIDITIES:
        raise ValueError(f"unknown trial validity: {value}")
    return value


def normalize_exclusion_reason(value: object) -> str | None:
    if value is None or value == "":
        return None
    value = LEGACY_EXCLUSION_REASON_ALIASES.get(str(value), str(value))
    if value not in EXCLUSION_REASONS:
        raise ValueError(f"unknown exclusion reason: {value}")
    return value


def trial_validity(result: Dict[str, Any]) -> str:
    review = result.get("review")
    if isinstance(review, dict) and review.get("trial_validity"):
        return normalize_trial_validity(review.get("trial_validity"))
    return normalize_trial_validity(result.get("trial_validity"))


def trial_is_valid(result: Dict[str, Any]) -> bool:
    return trial_validity(result) == DEFAULT_TRIAL_VALIDITY


def exclusion_reason(result: Dict[str, Any]) -> str:
    review = result.get("review")
    reason = None
    if isinstance(review, dict):
        reason = review.get("exclusion_reason")
    if reason is None:
        reason = result.get("exclusion_reason")
    return normalize_exclusion_reason(reason) or ""
