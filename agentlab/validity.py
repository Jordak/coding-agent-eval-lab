from __future__ import annotations

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
