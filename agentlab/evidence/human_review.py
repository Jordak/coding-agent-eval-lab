from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from agentlab.evidence.taxonomy import FAILURE_LABELS
from agentlab.evidence.validity import (
    DEFAULT_TRIAL_VALIDITY,
    EXCLUDED_TRIAL_VALIDITY,
    EXCLUSION_REASONS,
    normalize_exclusion_reason,
    normalize_trial_validity,
)


@dataclass(frozen=True)
class HumanReviewOutcome:
    primary_label: str
    secondary_labels: tuple[str, ...] = field(default_factory=tuple)
    note: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)
    trial_validity: str = DEFAULT_TRIAL_VALIDITY
    exclusion_reason: str | None = None

    @property
    def is_valid_trial(self) -> bool:
        return self.trial_validity == DEFAULT_TRIAL_VALIDITY

    @property
    def primary_label_display(self) -> str:
        return self.primary_label


def create_human_review_outcome(
    primary_label: str,
    note: str,
    secondary_labels: Iterable[str] = (),
    evidence: Iterable[str] = (),
    trial_validity: object = DEFAULT_TRIAL_VALIDITY,
    exclusion_reason: object = None,
) -> HumanReviewOutcome:
    secondary_label_tuple = _string_tuple(secondary_labels)
    evidence_tuple = _string_tuple(evidence)
    labels = [primary_label] + list(secondary_label_tuple)
    invalid = [label for label in labels if label not in FAILURE_LABELS]
    if invalid:
        raise ValueError(f"unknown review label(s): {', '.join(invalid)}")

    normalized_validity = normalize_trial_validity(trial_validity)
    normalized_exclusion_reason = _normalize_exclusion_for_validity(
        primary_label,
        normalized_validity,
        exclusion_reason,
    )

    return HumanReviewOutcome(
        primary_label=primary_label,
        secondary_labels=secondary_label_tuple,
        note=str(note),
        evidence=evidence_tuple,
        trial_validity=normalized_validity,
        exclusion_reason=normalized_exclusion_reason,
    )


def human_review_outcome_from_mapping(
    review: Mapping[str, Any],
) -> HumanReviewOutcome:
    primary_label = review.get("primary_label")
    if not isinstance(primary_label, str) or not primary_label:
        raise ValueError("human review outcome requires primary_label")
    trial_validity = review.get("trial_validity")
    if not trial_validity:
        raise ValueError("human review outcome requires trial_validity")
    exclusion_reason = review.get("exclusion_reason")
    if trial_validity == EXCLUDED_TRIAL_VALIDITY and not exclusion_reason:
        raise ValueError("excluded human review outcome requires exclusion_reason")

    return create_human_review_outcome(
        primary_label=primary_label,
        note=str(review.get("note") or ""),
        secondary_labels=_optional_string_tuple(
            review.get("secondary_labels"),
            field_name="secondary_labels",
        ),
        evidence=_optional_string_tuple(review.get("evidence"), field_name="evidence"),
        trial_validity=trial_validity,
        exclusion_reason=exclusion_reason,
    )


def human_review_outcome_to_mapping(
    outcome: HumanReviewOutcome,
) -> dict[str, Any]:
    return {
        "exclusion_reason": outcome.exclusion_reason,
        "primary_label": outcome.primary_label,
        "secondary_labels": list(outcome.secondary_labels),
        "note": outcome.note,
        "evidence": list(outcome.evidence),
        "trial_validity": outcome.trial_validity,
    }


def _normalize_exclusion_for_validity(
    primary_label: str,
    trial_validity: str,
    exclusion_reason: object,
) -> str | None:
    if trial_validity == EXCLUDED_TRIAL_VALIDITY:
        if exclusion_reason is None and primary_label in EXCLUSION_REASONS:
            exclusion_reason = primary_label
        normalized_exclusion_reason = normalize_exclusion_reason(exclusion_reason)
        if normalized_exclusion_reason is None:
            raise ValueError(
                "excluded trials require an exclusion reason: "
                + ", ".join(EXCLUSION_REASONS)
            )
        return normalized_exclusion_reason

    if exclusion_reason:
        raise ValueError("valid trials cannot have an exclusion reason")
    return None


def _optional_string_tuple(value: object, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"human review outcome {field_name} must be a list")
    return _string_tuple(value)


def _string_tuple(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(str(value) for value in values if value)
