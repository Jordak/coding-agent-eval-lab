from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from agentlab.evidence.human_review import (
    human_review_outcome_from_mapping,
    human_review_outcome_to_mapping,
)
from agentlab.evidence.outcome import OutcomeEvidence, normalize_outcome_evidence


SNAPSHOT_SCHEMA = "agentlab.outcome-evidence-snapshot.v1"


def write_evidence_snapshot(
    path: Path,
    results: Iterable[OutcomeEvidence],
) -> Path:
    records = [
        outcome_evidence_to_snapshot_record(result)
        for result in results
    ]
    payload = {
        "schema": SNAPSHOT_SCHEMA,
        "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def load_evidence_snapshot(path: Path) -> list[OutcomeEvidence]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"evidence snapshot must be JSON: {path}") from exc
    except OSError as exc:
        raise FileNotFoundError(str(exc)) from exc

    if not isinstance(raw, Mapping):
        raise ValueError("evidence snapshot must contain a JSON object")
    if raw.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError(f"unsupported evidence snapshot schema: {raw.get('schema')}")
    records = raw.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("evidence snapshot requires a non-empty records list")

    results = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"evidence snapshot record {index} must be an object")
        results.append(_outcome_evidence_from_snapshot_record(record, index))
    return results


def outcome_evidence_to_snapshot_record(
    result: OutcomeEvidence,
) -> dict[str, Any]:
    result_data = result.to_result_dict()
    result_data["artifact_receipts"] = result.artifact_receipts

    # Keep the snapshot portable: artifact presence is durable evidence, but
    # local run paths are not.
    result_data["run_dir"] = ""
    result_data["report_path"] = None
    result_data["result_path"] = None
    result_data["transcript_path"] = None
    result_data["diff_path"] = None
    outcome = result_data.get("outcome")
    if isinstance(outcome, dict):
        outcome.pop("diff_path", None)

    review = None
    if result.human_review_outcome is not None:
        review = human_review_outcome_to_mapping(result.human_review_outcome)

    return {
        "outcome_evidence": result_data,
        "human_review_outcome": review,
    }


def _outcome_evidence_from_snapshot_record(
    record: Mapping[str, Any],
    index: int,
) -> OutcomeEvidence:
    result = record.get("outcome_evidence")
    if not isinstance(result, Mapping):
        raise ValueError(
            f"evidence snapshot record {index} requires outcome_evidence"
        )

    review = record.get("human_review_outcome")
    human_review = None
    if review is not None:
        if not isinstance(review, Mapping):
            raise ValueError(
                f"evidence snapshot record {index} human_review_outcome "
                "must be an object"
            )
        human_review = human_review_outcome_from_mapping(review)

    return normalize_outcome_evidence(
        result,
        run_dir=None,
        human_review_outcome=human_review,
    )
