from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from agentlab.evidence.human_review import create_human_review_outcome
from agentlab.evidence.outcome import OutcomeEvidence, normalize_outcome_evidence
from agentlab.evidence.review_artifacts import ReviewArtifactError
from agentlab.evidence.validity import DEFAULT_TRIAL_VALIDITY, EXCLUDED_TRIAL_VALIDITY
from agentlab.tasks import EvalTask, TaskLoadError, load_task


REVIEW_PROPOSAL_FILENAME = "review.proposed.json"
REVIEW_PROPOSAL_SCHEMA_VERSION = 1
DEFAULT_REVIEWER_IDENTITY = "agentlab-deterministic-review-proposer"


class ReviewProposalArtifactError(ReviewArtifactError):
    pass


@dataclass(frozen=True)
class ReviewProposal:
    proposed_primary_label: str
    proposed_secondary_labels: tuple[str, ...] = field(default_factory=tuple)
    proposed_note: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)
    proposed_trial_validity: str = DEFAULT_TRIAL_VALIDITY
    proposed_exclusion_reason: str | None = None
    confidence: float = 0.0
    reviewer_identity: str = DEFAULT_REVIEWER_IDENTITY
    created_at: str = field(default_factory=lambda: _utc_timestamp())
    schema_version: int = REVIEW_PROPOSAL_SCHEMA_VERSION


@dataclass(frozen=True)
class ReviewProposalContext:
    run_dir: Path
    result_path: Path
    result: OutcomeEvidence
    task: EvalTask | None = None
    task_path: Path | None = None
    artifact_paths: Mapping[str, Path] = field(default_factory=dict)
    report_excerpt: str = ""
    diff_excerpt: str = ""
    transcript_excerpt: str = ""


class ReviewProposer(Protocol):
    def propose(self, context: ReviewProposalContext) -> ReviewProposal:
        ...


class DeterministicReviewProposer:
    def __init__(
        self,
        reviewer_identity: str = DEFAULT_REVIEWER_IDENTITY,
        created_at: str | None = None,
    ) -> None:
        self.reviewer_identity = reviewer_identity
        self.created_at = created_at

    def propose(self, context: ReviewProposalContext) -> ReviewProposal:
        result = context.result
        evidence = _default_evidence(context)
        created_at = self.created_at or _utc_timestamp()

        if _looks_like_setup_issue(result):
            return create_review_proposal(
                proposed_primary_label="dependency_issue",
                proposed_note=(
                    "Artifacts suggest a setup or dependency problem; human review "
                    "should confirm whether the trial is fair to count."
                ),
                evidence=evidence,
                proposed_trial_validity=EXCLUDED_TRIAL_VALIDITY,
                proposed_exclusion_reason="setup_error",
                confidence=0.35,
                reviewer_identity=self.reviewer_identity,
                created_at=created_at,
            )

        if result.success:
            return create_review_proposal(
                proposed_primary_label="success_clean",
                proposed_note=(
                    "Deterministic graders passed and the stored result looks "
                    "clean; human review should still inspect patch quality."
                ),
                evidence=evidence,
                confidence=0.65,
                reviewer_identity=self.reviewer_identity,
                created_at=created_at,
            )

        return create_review_proposal(
            proposed_primary_label="spec_misread",
            proposed_note=(
                "Deterministic graders failed; human review should inspect the "
                "diff, report, and transcript before applying a final label."
            ),
            evidence=evidence,
            confidence=0.45,
            reviewer_identity=self.reviewer_identity,
            created_at=created_at,
        )


def create_review_proposal(
    *,
    proposed_primary_label: str,
    proposed_note: str,
    proposed_secondary_labels: Iterable[str] = (),
    evidence: Iterable[str] = (),
    proposed_trial_validity: object = DEFAULT_TRIAL_VALIDITY,
    proposed_exclusion_reason: object = None,
    confidence: object,
    reviewer_identity: object,
    created_at: object | None = None,
    schema_version: object = REVIEW_PROPOSAL_SCHEMA_VERSION,
) -> ReviewProposal:
    outcome = create_human_review_outcome(
        primary_label=proposed_primary_label,
        note=proposed_note,
        secondary_labels=proposed_secondary_labels,
        evidence=evidence,
        trial_validity=proposed_trial_validity,
        exclusion_reason=proposed_exclusion_reason,
    )
    normalized_confidence = _normalize_confidence(confidence)
    normalized_reviewer = _required_string(
        reviewer_identity,
        field_name="reviewer_identity",
    )
    normalized_created_at = _required_string(
        _utc_timestamp() if created_at is None else created_at,
        field_name="created_at",
    )
    normalized_schema = _normalize_schema_version(schema_version)

    return ReviewProposal(
        proposed_primary_label=outcome.primary_label,
        proposed_secondary_labels=tuple(outcome.secondary_labels),
        proposed_note=outcome.note,
        evidence=tuple(outcome.evidence),
        proposed_trial_validity=outcome.trial_validity,
        proposed_exclusion_reason=outcome.exclusion_reason,
        confidence=normalized_confidence,
        reviewer_identity=normalized_reviewer,
        created_at=normalized_created_at,
        schema_version=normalized_schema,
    )


def review_proposal_to_mapping(proposal: ReviewProposal) -> dict[str, Any]:
    return {
        "schema_version": proposal.schema_version,
        "proposed_primary_label": proposal.proposed_primary_label,
        "proposed_secondary_labels": list(proposal.proposed_secondary_labels),
        "proposed_note": proposal.proposed_note,
        "evidence": list(proposal.evidence),
        "proposed_trial_validity": proposal.proposed_trial_validity,
        "proposed_exclusion_reason": proposal.proposed_exclusion_reason,
        "confidence": proposal.confidence,
        "reviewer_identity": proposal.reviewer_identity,
        "created_at": proposal.created_at,
    }


def review_proposal_from_mapping(proposal: Mapping[str, Any]) -> ReviewProposal:
    return create_review_proposal(
        proposed_primary_label=_required_string(
            proposal.get("proposed_primary_label"),
            field_name="proposed_primary_label",
        ),
        proposed_secondary_labels=_optional_string_tuple(
            proposal.get("proposed_secondary_labels"),
            field_name="proposed_secondary_labels",
        ),
        proposed_note=str(proposal.get("proposed_note") or ""),
        evidence=_optional_string_tuple(proposal.get("evidence"), field_name="evidence"),
        proposed_trial_validity=_required_string(
            proposal.get("proposed_trial_validity"),
            field_name="proposed_trial_validity",
        ),
        proposed_exclusion_reason=proposal.get("proposed_exclusion_reason"),
        confidence=proposal.get("confidence"),
        reviewer_identity=proposal.get("reviewer_identity"),
        created_at=proposal.get("created_at"),
        schema_version=proposal.get("schema_version"),
    )


def write_review_proposal(run_dir: Path, proposal: ReviewProposal) -> Path:
    proposal_path = run_dir / REVIEW_PROPOSAL_FILENAME
    proposal_path.write_text(
        json.dumps(
            review_proposal_to_mapping(proposal),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return proposal_path


def load_review_proposal(run_dir: Path) -> ReviewProposal | None:
    proposal_path = run_dir / REVIEW_PROPOSAL_FILENAME
    if not proposal_path.exists():
        return None
    try:
        raw = json.loads(proposal_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReviewProposalArtifactError(
            f"could not read review proposal artifact: {proposal_path}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise ReviewProposalArtifactError(
            f"review proposal artifact must be UTF-8 JSON: {proposal_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ReviewProposalArtifactError(
            f"review proposal artifact must be JSON: {proposal_path}"
        ) from exc
    if not isinstance(raw, Mapping):
        raise ReviewProposalArtifactError(
            f"review proposal artifact must contain an object: {proposal_path}"
        )
    try:
        return review_proposal_from_mapping(raw)
    except ValueError as exc:
        raise ReviewProposalArtifactError(
            f"invalid review proposal artifact: {proposal_path}: {exc}"
        ) from exc


def clear_review_proposal(run_dir: Path) -> Path | None:
    proposal_path = run_dir / REVIEW_PROPOSAL_FILENAME
    if not proposal_path.exists():
        return None
    proposal_path.unlink()
    return proposal_path


def build_review_proposal_context(result_path: Path) -> ReviewProposalContext:
    run_dir = result_path.parent
    raw = _load_result_mapping(result_path)
    if raw.get("trial_kind", "agent_trial") != "agent_trial":
        raise ReviewProposalArtifactError(
            f"review proposals require an agent trial result: {result_path}"
        )

    result = normalize_outcome_evidence(
        raw,
        run_dir=run_dir,
        human_review_outcome=None,
    )
    task, task_path = _load_task_for_result(result)
    artifact_paths = _artifact_paths(run_dir, result)
    return ReviewProposalContext(
        run_dir=run_dir,
        result_path=result_path,
        result=result,
        task=task,
        task_path=task_path,
        artifact_paths=artifact_paths,
        report_excerpt=_read_excerpt(artifact_paths.get("report")),
        diff_excerpt=_read_excerpt(artifact_paths.get("diff")),
        transcript_excerpt=_read_excerpt(artifact_paths.get("transcript")),
    )


def generate_review_proposal_for_run(
    run_dir: Path,
    proposer: ReviewProposer | None = None,
) -> tuple[Path, ReviewProposal]:
    return generate_review_proposal_for_result(run_dir / "result.json", proposer)


def generate_review_proposal_for_result(
    result_path: Path,
    proposer: ReviewProposer | None = None,
) -> tuple[Path, ReviewProposal]:
    context = build_review_proposal_context(result_path)
    selected_proposer = proposer or DeterministicReviewProposer()
    proposal = selected_proposer.propose(context)
    return write_review_proposal(context.run_dir, proposal), proposal


def generate_review_proposals_for_results(
    result_files: Iterable[Path],
    proposer: ReviewProposer | None = None,
) -> list[tuple[Path, ReviewProposal]]:
    selected_proposer = proposer or DeterministicReviewProposer()
    generated: list[tuple[Path, ReviewProposal]] = []
    for result_file in result_files:
        generated.append(generate_review_proposal_for_result(result_file, selected_proposer))
    return generated


def _load_result_mapping(result_path: Path) -> Mapping[str, Any]:
    try:
        raw = json.loads(result_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReviewProposalArtifactError(
            f"could not read trial result artifact: {result_path}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise ReviewProposalArtifactError(
            f"trial result artifact must be UTF-8 JSON: {result_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ReviewProposalArtifactError(
            f"trial result artifact must be JSON: {result_path}"
        ) from exc
    if not isinstance(raw, Mapping):
        raise ReviewProposalArtifactError(
            f"trial result artifact must contain an object: {result_path}"
        )
    return raw


def _load_task_for_result(result: OutcomeEvidence) -> tuple[EvalTask | None, Path | None]:
    for candidate in _task_candidates(result):
        try:
            task = load_task(candidate)
        except (OSError, TaskLoadError):
            continue
        source_path = task.source_path or candidate
        return task, source_path
    return None, None


def _task_candidates(result: OutcomeEvidence) -> list[Path]:
    candidates: list[Path] = []
    for key in ("task_path", "task_file"):
        raw_path = result.raw.get(key)
        if raw_path:
            candidates.append(Path(str(raw_path)))
    if result.eval_suite and result.task_id:
        candidates.append(Path("tasks") / result.eval_suite / result.task_id)
    return candidates


def _artifact_paths(run_dir: Path, result: OutcomeEvidence) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for key, raw_path, fallback_name in [
        ("report", result.report_path, "report.md"),
        ("diff", result.diff_path, "diff.patch"),
        ("transcript", result.transcript_path, "transcript.md"),
    ]:
        path = _resolve_artifact_path(run_dir, raw_path, fallback_name)
        if path is not None:
            artifacts[key] = path
    return artifacts


def _resolve_artifact_path(
    run_dir: Path,
    raw_path: str | None,
    fallback_name: str,
) -> Path | None:
    candidates: list[Path] = []
    if raw_path:
        path = Path(raw_path)
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.extend([run_dir / path, Path.cwd() / path])
    candidates.append(run_dir / fallback_name)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _default_evidence(context: ReviewProposalContext) -> tuple[str, ...]:
    result = context.result
    evidence = [
        (
            "result.json: "
            f"status={result.status}; success={result.success}; "
            f"files_changed={result.n_files_changed}; "
            f"lines_added={result.lines_added}; lines_deleted={result.lines_deleted}; "
            f"duration_ms={result.duration_ms}"
        )
    ]
    if context.task is not None:
        evidence.append(
            "task.yaml: "
            f"{context.task.id} - {context.task.title}; "
            f"failure_modes={','.join(context.task.failure_modes) or 'none'}"
        )
    elif context.task_path is not None:
        evidence.append(f"task.yaml: {context.task_path}")

    for check in result.checks[:3]:
        if isinstance(check, Mapping):
            command = str(check.get("command") or "").strip()
            passed = check.get("passed")
            if command:
                evidence.append(f"check: passed={passed}; command={command}")

    if context.report_excerpt:
        evidence.append(f"report.md excerpt: {context.report_excerpt}")
    if context.diff_excerpt:
        evidence.append(f"diff.patch excerpt: {context.diff_excerpt}")
    if context.transcript_excerpt:
        evidence.append(f"transcript excerpt: {context.transcript_excerpt}")
    return tuple(evidence)


def _looks_like_setup_issue(result: OutcomeEvidence) -> bool:
    text_parts = [
        str(result.error or ""),
        " ".join(str(note) for note in result.score_notes),
    ]
    for check in result.checks:
        if isinstance(check, Mapping):
            text_parts.extend(
                [
                    str(check.get("stdout") or ""),
                    str(check.get("stderr") or ""),
                    str(check.get("command") or ""),
                ]
            )
    text = "\n".join(text_parts).lower()
    return any(
        needle in text
        for needle in [
            "no module named",
            "module not found",
            "command not found",
            "dependency",
            "failed to install",
            "setup failed",
            "environment",
        ]
    )


def _read_excerpt(path: Path | None, max_chars: int = 600) -> str:
    if path is None:
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    squashed = " ".join(text.split())
    if len(squashed) <= max_chars:
        return squashed
    return squashed[: max_chars - 3] + "..."


def _optional_string_tuple(value: object, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"review proposal {field_name} must be a list")
    return tuple(str(item) for item in value if item)


def _required_string(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"review proposal requires {field_name}")
    return value


def _normalize_confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("review proposal confidence must be a number")
    confidence = float(value)
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError("review proposal confidence must be between 0 and 1")
    return confidence


def _normalize_schema_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("review proposal schema_version must be an integer")
    if value != REVIEW_PROPOSAL_SCHEMA_VERSION:
        raise ValueError(f"unsupported review proposal schema_version: {value}")
    return value


def _utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
