from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from agentlab.evidence.human_review import HumanReviewOutcome
from agentlab.runtime.resource_usage import ResourceUsage, resource_usage_to_dict
from agentlab.evidence.backfills import apply_result_backfills
from agentlab.evidence.review_artifacts import load_review
from agentlab.evidence.validity import DEFAULT_TRIAL_VALIDITY


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
    run_surface: Dict[str, Any]
    status: str
    success: bool
    outcome: Dict[str, Any]
    score_notes: list[Any]
    duration_ms: int
    error: Any
    resource_usage: ResourceUsage
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
    human_review_outcome: HumanReviewOutcome | None = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid_trial(self) -> bool:
        return self.trial_validity == DEFAULT_TRIAL_VALIDITY

    @property
    def trial_validity(self) -> str:
        if self.human_review_outcome is None:
            return DEFAULT_TRIAL_VALIDITY
        return self.human_review_outcome.trial_validity

    @property
    def exclusion_reason(self) -> str | None:
        if self.human_review_outcome is None:
            return None
        return self.human_review_outcome.exclusion_reason

    @property
    def primary_review_label(self) -> str:
        if self.human_review_outcome is None:
            return ""
        return self.human_review_outcome.primary_label_display

    @property
    def secondary_review_labels(self) -> list[str]:
        if self.human_review_outcome is None:
            return []
        return list(self.human_review_outcome.secondary_labels)

    @property
    def exclusion_reason_display(self) -> str:
        return self.exclusion_reason or ""

    @property
    def model_name_display(self) -> str:
        return _display_unknown(self.model_name)

    @property
    def reasoning_effort(self) -> str:
        direct_value = _optional_nonempty_str(self.raw.get("reasoning_effort"))
        if direct_value is not None:
            return direct_value

        config_value = _optional_nonempty_str(
            self.agent_harness_config.get("reasoning_effort")
        )
        if config_value is not None:
            return config_value

        return ""

    @property
    def reasoning_effort_display(self) -> str:
        return _display_unknown(self.reasoning_effort)

    @property
    def execution_surface_display(self) -> str:
        return _display_unknown(self.run_surface.get("execution_surface"))

    @property
    def runtime_version_display(self) -> str:
        return _display_unknown(self.run_surface.get("runtime_version"))

    @property
    def sandbox_mode_display(self) -> str:
        return _display_unknown(self.run_surface.get("sandbox_mode"))

    @property
    def approval_policy_display(self) -> str:
        return _display_unknown(self.run_surface.get("approval_policy"))

    @property
    def memory_scope_display(self) -> str:
        return _display_unknown(self.run_surface.get("memory_scope"))

    @property
    def network_policy_display(self) -> str:
        return _display_unknown(self.run_surface.get("network_policy"))

    @property
    def stop_reason_display(self) -> str:
        return _display_unknown(self.run_surface.get("stop_reason"))

    @property
    def files_changed_count(self) -> int:
        return self.n_files_changed

    @property
    def input_tokens(self) -> int | None:
        return self.resource_usage.input_tokens

    @property
    def cached_input_tokens(self) -> int | None:
        return self.resource_usage.cached_input_tokens

    @property
    def output_tokens(self) -> int | None:
        return self.resource_usage.output_tokens

    @property
    def reasoning_output_tokens(self) -> int | None:
        return self.resource_usage.reasoning_output_tokens

    @property
    def cost_usd(self) -> float | None:
        return self.resource_usage.cost_usd

    @property
    def result_path(self) -> str | None:
        if not self.run_dir:
            return None
        return str(Path(self.run_dir) / "result.json")

    def to_result_dict(self) -> Dict[str, Any]:
        result = dict(self.raw)
        result.pop("review", None)
        result.pop("trial_validity", None)
        result.pop("exclusion_reason", None)
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
                "run_surface": dict(self.run_surface),
                "status": self.status,
                "success": self.success,
                "outcome": dict(self.outcome),
                "score_notes": list(self.score_notes),
                "duration_ms": self.duration_ms,
                "error": self.error,
                "input_tokens": self.input_tokens,
                "cached_input_tokens": self.cached_input_tokens,
                "output_tokens": self.output_tokens,
                "reasoning_output_tokens": self.reasoning_output_tokens,
                "cost_usd": self.cost_usd,
                "resource_usage": resource_usage_to_dict(self.resource_usage),
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
        return result


def load_outcome_evidence(path: Path) -> OutcomeEvidence | None:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if result.get("trial_kind", "agent_trial") != "agent_trial":
        return None

    run_dir = path.parent
    return normalize_outcome_evidence(
        result,
        run_dir=run_dir,
        human_review_outcome=load_review(run_dir),
    )


def load_outcome_evidences(paths: Iterable[Path]) -> list[OutcomeEvidence]:
    evidences: list[OutcomeEvidence] = []
    for path in paths:
        evidence = load_outcome_evidence(path)
        if evidence is not None:
            evidences.append(evidence)
    return evidences


def normalize_outcome_evidence(
    result: Mapping[str, Any],
    run_dir: Path | str | None = None,
    human_review_outcome: HumanReviewOutcome | None = None,
) -> OutcomeEvidence:
    data = dict(result)
    resolved_run_dir = _resolve_run_dir(data, run_dir)

    apply_result_backfills(data, resolved_run_dir)

    status, success = _grader_status(data)

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
        run_surface=dict(data.get("run_surface") or {}),
        status=status,
        success=success,
        outcome=outcome,
        score_notes=_list(data.get("score_notes")),
        duration_ms=_optional_int(data.get("duration_ms")) or 0,
        error=data.get("error"),
        resource_usage=_resource_usage(data),
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
        human_review_outcome=human_review_outcome,
        raw=data,
    )


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


def _resource_usage(data: Mapping[str, Any]) -> ResourceUsage:
    return ResourceUsage(
        input_tokens=_optional_int(data.get("input_tokens")),
        cached_input_tokens=_optional_int(data.get("cached_input_tokens")),
        output_tokens=_optional_int(data.get("output_tokens")),
        reasoning_output_tokens=_optional_int(data.get("reasoning_output_tokens")),
        cost_usd=_optional_float(data.get("cost_usd")),
    )


def _optional_dict(value: object) -> Dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_nonempty_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return text


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


def _display_unknown(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value)
    if not text:
        return "unknown"
    return text
