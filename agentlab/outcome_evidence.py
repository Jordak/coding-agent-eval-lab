from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from agentlab.agent_harness_config import normalize_agent_harness_config
from agentlab.model_identity import model_identity_from_events
from agentlab.patches import count_patch_lines
from agentlab.resource_usage import (
    ResourceUsage,
    parse_resource_usage_events,
    resource_usage_to_dict,
)
from agentlab.review import load_review
from agentlab.validity import (
    EXCLUDED_TRIAL_VALIDITY,
    normalize_exclusion_reason,
    normalize_trial_validity,
)


@dataclass(frozen=True)
class OutcomeEvidence:
    trial_kind: str
    trial_id: str
    run_id: str
    task_id: str
    task_title: str
    eval_suite: str
    eval_type: str
    reference_artifact: Dict[str, Any] | None
    agent_name: str
    model_name: str | None
    agent_harness_config: Dict[str, Any]
    status: str
    success: bool
    trial_validity: str
    exclusion_reason: str | None
    outcome: Dict[str, Any]
    score_notes: list[Any]
    duration_ms: int
    error: Any
    resource_usage: Dict[str, Any]
    files_changed: list[str]
    n_files_changed: int
    lines_added: int
    lines_deleted: int
    commands_run: list[Any]
    checks: list[Any]
    graders: list[Any]
    report_path: str | None
    transcript_path: str | None
    diff_path: str | None
    run_dir: str
    review: Dict[str, Any] | None = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_result_dict(self) -> Dict[str, Any]:
        result = dict(self.raw)
        result.update(
            {
                "trial_kind": self.trial_kind,
                "trial_id": self.trial_id,
                "run_id": self.run_id,
                "task_id": self.task_id,
                "task_title": self.task_title,
                "eval_suite": self.eval_suite,
                "eval_type": self.eval_type,
                "reference_artifact": self.reference_artifact,
                "agent_name": self.agent_name,
                "model_name": self.model_name,
                "agent_harness_config": dict(self.agent_harness_config),
                "status": self.status,
                "success": self.success,
                "trial_validity": self.trial_validity,
                "exclusion_reason": self.exclusion_reason,
                "outcome": dict(self.outcome),
                "score_notes": list(self.score_notes),
                "duration_ms": self.duration_ms,
                "error": self.error,
                "resource_usage": dict(self.resource_usage),
                "files_changed": list(self.files_changed),
                "n_files_changed": self.n_files_changed,
                "lines_added": self.lines_added,
                "lines_deleted": self.lines_deleted,
                "commands_run": list(self.commands_run),
                "checks": list(self.checks),
                "graders": list(self.graders),
                "report_path": self.report_path,
                "transcript_path": self.transcript_path,
                "diff_path": self.diff_path,
                "run_dir": self.run_dir,
            }
        )
        if self.review is not None:
            result["review"] = dict(self.review)
        return result


def load_outcome_evidence(path: Path) -> OutcomeEvidence | None:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if result.get("trial_kind", "agent_trial") != "agent_trial":
        return None

    run_dir = Path(str(result.get("run_dir") or path.parent))
    return normalize_outcome_evidence(
        result,
        run_dir=run_dir,
        review=load_review(run_dir),
    )


def normalize_outcome_evidence(
    result: Mapping[str, Any],
    run_dir: Path | str | None = None,
    review: Mapping[str, Any] | None = None,
) -> OutcomeEvidence:
    data = dict(result)
    resolved_run_dir = _resolve_run_dir(data, run_dir)
    loaded_review = _review_overlay(data, review)

    _backfill_edit_size(data, resolved_run_dir)
    _backfill_resource_usage(data, resolved_run_dir)
    _backfill_model_identity(data, resolved_run_dir)
    _backfill_agent_harness_config(data)

    status, success = _grader_status(data)
    trial_validity, review_exclusion_reason = _review_validity(
        data,
        loaded_review,
    )
    if loaded_review is not None:
        exclusion_reason = review_exclusion_reason
    else:
        exclusion_reason = _optional_str(data.get("exclusion_reason"))

    files_changed = _files_changed(data)
    n_files_changed = _files_changed_count(data, files_changed)
    lines_added = _optional_int(data.get("lines_added")) or 0
    lines_deleted = _optional_int(data.get("lines_deleted")) or 0
    outcome = _outcome(
        data,
        status,
        files_changed,
        n_files_changed,
        lines_added,
        lines_deleted,
    )

    trial_id = str(
        data.get("trial_id")
        or data.get("run_id")
        or (resolved_run_dir.name if resolved_run_dir is not None else "")
    )
    run_id = str(data.get("run_id") or trial_id)

    return OutcomeEvidence(
        trial_kind=str(data.get("trial_kind") or "agent_trial"),
        trial_id=trial_id,
        run_id=run_id,
        task_id=str(data.get("task_id") or ""),
        task_title=str(data.get("task_title") or ""),
        eval_suite=str(data.get("eval_suite") or ""),
        eval_type=str(data.get("eval_type") or ""),
        reference_artifact=_optional_dict(data.get("reference_artifact")),
        agent_name=str(data.get("agent_name") or ""),
        model_name=_optional_str(data.get("model_name")),
        agent_harness_config=dict(data.get("agent_harness_config") or {}),
        status=status,
        success=success,
        trial_validity=trial_validity,
        exclusion_reason=exclusion_reason,
        outcome=outcome,
        score_notes=_list(data.get("score_notes")),
        duration_ms=_optional_int(data.get("duration_ms")) or 0,
        error=data.get("error"),
        resource_usage=dict(data.get("resource_usage") or {}),
        files_changed=files_changed,
        n_files_changed=n_files_changed,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        commands_run=_list(data.get("commands_run")),
        checks=_list(data.get("checks")),
        graders=_list(data.get("graders")),
        report_path=_optional_str(data.get("report_path")),
        transcript_path=_optional_str(data.get("transcript_path")),
        diff_path=_optional_str(data.get("diff_path")),
        run_dir=str(resolved_run_dir) if resolved_run_dir is not None else "",
        review=dict(loaded_review) if loaded_review is not None else None,
        raw=data,
    )


def normalize_result_dicts(
    results: Iterable[Mapping[str, Any]],
) -> list[Dict[str, Any]]:
    return [
        normalize_outcome_evidence(result).to_result_dict()
        for result in results
    ]


def result_files_changed_count(result: Mapping[str, Any]) -> int:
    value = _optional_int(result.get("n_files_changed"))
    if value is not None:
        return value
    return len(_files_changed(result))


def _resolve_run_dir(
    data: Mapping[str, Any],
    run_dir: Path | str | None,
) -> Path | None:
    if run_dir is not None:
        return Path(str(run_dir))
    raw_run_dir = data.get("run_dir")
    if raw_run_dir:
        return Path(str(raw_run_dir))
    return None


def _review_overlay(
    data: Mapping[str, Any],
    review: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    if review is not None:
        return dict(review)
    embedded = data.get("review")
    if isinstance(embedded, Mapping):
        return dict(embedded)
    return None


def _review_validity(
    data: Mapping[str, Any],
    review: Mapping[str, Any] | None,
) -> tuple[str, str | None]:
    if review is None:
        return normalize_trial_validity(data.get("trial_validity")), (
            normalize_exclusion_reason(data.get("exclusion_reason"))
        )

    validity = normalize_trial_validity(review.get("trial_validity"))
    exclusion_reason = normalize_exclusion_reason(review.get("exclusion_reason"))
    if validity != EXCLUDED_TRIAL_VALIDITY:
        exclusion_reason = None
    return validity, exclusion_reason


def _grader_status(data: Mapping[str, Any]) -> tuple[str, bool]:
    outcome = data.get("outcome")
    outcome_status = ""
    if isinstance(outcome, Mapping):
        outcome_status = str(outcome.get("status") or "")

    status = str(data.get("status") or outcome_status or "")
    success = data.get("success")
    if isinstance(success, bool):
        resolved_success = success
    elif status:
        resolved_success = status == "passed"
    else:
        resolved_success = False

    if not status:
        status = "passed" if resolved_success else "failed"
    return status, resolved_success


def _outcome(
    data: Mapping[str, Any],
    status: str,
    files_changed: list[str],
    n_files_changed: int,
    lines_added: int,
    lines_deleted: int,
) -> Dict[str, Any]:
    raw_outcome = data.get("outcome")
    outcome = dict(raw_outcome) if isinstance(raw_outcome, Mapping) else {}
    outcome["status"] = status
    outcome["files_changed"] = files_changed
    outcome["n_files_changed"] = n_files_changed
    outcome["lines_added"] = lines_added
    outcome["lines_deleted"] = lines_deleted
    if data.get("diff_path") is not None:
        outcome["diff_path"] = str(data.get("diff_path"))
    return outcome


def _backfill_edit_size(data: Dict[str, Any], run_dir: Path | None) -> None:
    outcome = data.get("outcome")
    if isinstance(outcome, Mapping):
        if "files_changed" not in data and isinstance(outcome.get("files_changed"), list):
            data["files_changed"] = list(outcome.get("files_changed") or [])
        if "lines_added" not in data and outcome.get("lines_added") is not None:
            data["lines_added"] = outcome.get("lines_added")
        if "lines_deleted" not in data and outcome.get("lines_deleted") is not None:
            data["lines_deleted"] = outcome.get("lines_deleted")
        if "n_files_changed" not in data and outcome.get("n_files_changed") is not None:
            data["n_files_changed"] = outcome.get("n_files_changed")

    needs_patch = (
        "files_changed" not in data
        or "lines_added" not in data
        or "lines_deleted" not in data
    )
    if needs_patch:
        patch_text = _patch_text(data, run_dir)
        if patch_text is not None:
            if "files_changed" not in data:
                data["files_changed"] = _patch_files_changed(patch_text)
            stats = count_patch_lines(patch_text)
            data.setdefault("lines_added", stats.lines_added)
            data.setdefault("lines_deleted", stats.lines_deleted)

    data.setdefault("files_changed", [])
    data.setdefault("lines_added", 0)
    data.setdefault("lines_deleted", 0)
    data.setdefault(
        "n_files_changed",
        _files_changed_count(data, _files_changed(data)),
    )


def _backfill_resource_usage(data: Dict[str, Any], run_dir: Path | None) -> None:
    resource_usage = data.get("resource_usage")
    if not isinstance(resource_usage, Mapping):
        resource_usage = {}

    if not resource_usage:
        event_usage = _resource_usage_from_events(run_dir)
        if event_usage is not None:
            resource_usage = resource_usage_to_dict(event_usage)

    for key in [
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "cost_usd",
    ]:
        data.setdefault(key, resource_usage.get(key))

    usage = ResourceUsage(
        input_tokens=_optional_int(data.get("input_tokens")),
        cached_input_tokens=_optional_int(data.get("cached_input_tokens")),
        output_tokens=_optional_int(data.get("output_tokens")),
        reasoning_output_tokens=_optional_int(data.get("reasoning_output_tokens")),
        cost_usd=_optional_float(data.get("cost_usd")),
    )
    data["resource_usage"] = resource_usage_to_dict(usage)


def _backfill_agent_harness_config(data: Dict[str, Any]) -> None:
    data["agent_harness_config"] = normalize_agent_harness_config(
        _optional_dict(data.get("agent_harness_config")),
        agent_name=_optional_str(data.get("agent_name")),
        model_name=_optional_str(data.get("model_name")),
        cost_usd=_optional_float(data.get("cost_usd")),
    )


def _backfill_model_identity(data: Dict[str, Any], run_dir: Path | None) -> None:
    events_text = _model_events_text(run_dir)
    if events_text is None:
        return

    config = _optional_dict(data.get("agent_harness_config")) or {}
    requested_model = _requested_model_name(data, config)
    identity = model_identity_from_events(
        events_text,
        requested_model_name=requested_model,
    )
    if not identity.model_name:
        return

    data["model_name"] = identity.model_name
    config["model_name"] = identity.model_name
    config["model_source"] = identity.model_source
    config["requested_model_name"] = identity.requested_model_name
    data["agent_harness_config"] = config


def _requested_model_name(
    data: Mapping[str, Any],
    config: Mapping[str, Any],
) -> str | None:
    requested = _optional_str(config.get("requested_model_name"))
    if requested is not None:
        return requested
    if config.get("model_source") == "explicit":
        return _optional_str(config.get("model_name"))
    return _optional_str(data.get("requested_model_name"))


def _model_events_text(run_dir: Path | None) -> str | None:
    if run_dir is None:
        return None
    for filename in ["claude-events.jsonl", "codex-events.jsonl"]:
        path = run_dir / filename
        if not path.exists():
            continue
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def _resource_usage_from_events(run_dir: Path | None) -> ResourceUsage | None:
    if run_dir is None:
        return None
    events_path = run_dir / "codex-events.jsonl"
    if not events_path.exists():
        return None
    try:
        usage = parse_resource_usage_events(events_path.read_text(encoding="utf-8"))
    except OSError:
        return None
    if usage.total_tokens is None and usage.cost_usd is None:
        return None
    return usage


def _patch_text(data: Mapping[str, Any], run_dir: Path | None) -> str | None:
    diff_path = _result_diff_path(data, run_dir)
    if diff_path is None or not diff_path.exists():
        return None
    try:
        return diff_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _result_diff_path(
    data: Mapping[str, Any],
    run_dir: Path | None,
) -> Path | None:
    raw_path = data.get("diff_path")
    if not raw_path:
        raw_path = "diff.patch"
    diff_path = Path(str(raw_path))
    if diff_path.is_absolute():
        return diff_path
    if run_dir is None:
        return None
    return run_dir / diff_path


def _patch_files_changed(patch_text: str) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for line in patch_text.splitlines():
        path = None
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = _strip_git_prefix(parts[3])
        elif line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            path = _strip_git_prefix(line[4:].strip())

        if path and path not in seen:
            files.append(path)
            seen.add(path)
    return files


def _strip_git_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def _files_changed(data: Mapping[str, Any]) -> list[str]:
    files = data.get("files_changed")
    if isinstance(files, list):
        return [str(path) for path in files]
    return []


def _files_changed_count(
    data: Mapping[str, Any],
    files_changed: list[str],
) -> int:
    raw_count = _optional_int(data.get("n_files_changed"))
    if raw_count is not None:
        return raw_count
    return len(files_changed)


def _optional_dict(value: object) -> Dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _list(value: object) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    return []
