from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

UNKNOWN = "unknown"

RUN_SURFACE_FIELDS = (
    "execution_surface",
    "runtime_version",
    "model_identity_source",
    "sandbox_mode",
    "approval_policy",
    "tool_policy",
    "memory_scope",
    "network_policy",
    "timeout_seconds",
    "turn_or_step_budget",
    "stop_reason",
    "human_intervention_events",
)


def normalize_run_surface(
    run_surface: Mapping[str, Any] | None = None,
    *,
    agent_harness_config: Mapping[str, Any] | None = None,
    agent_name: str | None = None,
    status: str | None = None,
    success: bool | None = None,
    error: Any = None,
) -> Dict[str, Any]:
    config = dict(agent_harness_config or {})
    surface = dict(run_surface or {})
    generated = _run_surface_from_config(
        config,
        agent_name=agent_name,
        status=status,
        success=success,
        error=error,
    )

    normalized: Dict[str, Any] = {
        str(key): value
        for key, value in surface.items()
        if str(key) not in RUN_SURFACE_FIELDS
    }
    for field in RUN_SURFACE_FIELDS:
        value = surface.get(field, generated[field])
        normalized[field] = _normalize_field(field, value)
    return normalized


def stop_reason_from_outcome(
    *,
    status: str | None = None,
    success: bool | None = None,
    error: Any = None,
) -> str:
    error_text = _optional_str(error)
    if error_text:
        lowered = error_text.lower()
        if "timeout" in lowered or "timed out" in lowered:
            return "timeout"
        if "setup" in lowered:
            return "setup_error"
        if "interrupt" in lowered or "operator" in lowered:
            return "operator_interruption"
        return "agent_error"

    status_text = (status or "").strip().lower()
    if success is True or status_text in {"passed", "success"}:
        return "success"
    if success is False or status_text in {"failed", "failure"}:
        return "grader_failure"
    return UNKNOWN


def _run_surface_from_config(
    config: Mapping[str, Any],
    *,
    agent_name: str | None,
    status: str | None,
    success: bool | None,
    error: Any,
) -> Dict[str, Any]:
    return {
        "execution_surface": _execution_surface(config, agent_name),
        "runtime_version": _first_known(
            config.get("runtime_version"),
            config.get("cli_version"),
        ),
        "model_identity_source": _first_known(config.get("model_source")),
        "sandbox_mode": _first_known(
            config.get("sandbox_mode"),
            config.get("sandbox"),
        ),
        "approval_policy": _first_known(
            config.get("approval_policy"),
            config.get("permission_mode"),
        ),
        "tool_policy": _tool_policy(config),
        "memory_scope": _memory_scope(config),
        "network_policy": _first_known(config.get("network_policy")),
        "timeout_seconds": _first_known(config.get("timeout_seconds")),
        "turn_or_step_budget": _turn_or_step_budget(config),
        "stop_reason": stop_reason_from_outcome(
            status=status,
            success=success,
            error=error,
        ),
        "human_intervention_events": _human_intervention_events(config),
    }


def _execution_surface(
    config: Mapping[str, Any],
    agent_name: str | None,
) -> str:
    configured = _optional_str(config.get("execution_surface"))
    if configured:
        return configured

    harness = _optional_str(config.get("agent_harness")) or agent_name or ""
    adapter = _optional_str(config.get("agent_adapter")) or ""
    if adapter in {"codex_cli", "claude_code_cli"}:
        return "local_cli"
    if harness in {"codex", "claude", "claude_code"} and config.get("command"):
        return "local_cli"
    return UNKNOWN


def _tool_policy(config: Mapping[str, Any]) -> object:
    if "tool_policy" in config:
        return _first_known(config.get("tool_policy"))
    if "allowed_tools" in config or "disallowed_tools" in config:
        return {
            "allowed_tools": _list_or_unknown(config.get("allowed_tools")),
            "disallowed_tools": _list_or_unknown(config.get("disallowed_tools")),
        }
    return UNKNOWN


def _memory_scope(config: Mapping[str, Any]) -> str:
    configured = _optional_str(config.get("memory_scope"))
    if configured:
        return configured
    if config.get("no_session_persistence") is True:
        return "no_session_persistence"
    return UNKNOWN


def _turn_or_step_budget(config: Mapping[str, Any]) -> object:
    if config.get("turn_or_step_budget") is not None:
        return _first_known(config.get("turn_or_step_budget"))
    if config.get("max_turns") is not None:
        return {"max_turns": config.get("max_turns")}
    return UNKNOWN


def _human_intervention_events(config: Mapping[str, Any]) -> object:
    if "human_intervention_events" not in config:
        return []
    events = config.get("human_intervention_events")
    if events is None:
        return UNKNOWN
    if isinstance(events, list):
        return list(events)
    if isinstance(events, tuple):
        return list(events)
    return _first_known(events)


def _normalize_field(field: str, value: object) -> object:
    if field == "human_intervention_events":
        if isinstance(value, list):
            return list(value)
        if isinstance(value, tuple):
            return list(value)
        if value is None:
            return UNKNOWN
        return _first_known(value)
    if field == "turn_or_step_budget":
        return _normalize_turn_or_step_budget(value)
    if field == "tool_policy":
        return _normalize_structured_or_unknown(value)
    return _first_known(value)


def _normalize_turn_or_step_budget(value: object) -> object:
    if isinstance(value, Mapping) and set(value) == {"reasoning_effort"}:
        return UNKNOWN
    return _normalize_structured_or_unknown(value)


def _normalize_structured_or_unknown(value: object) -> object:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return _first_known(value)


def _list_or_unknown(value: object) -> object:
    if value is None:
        return UNKNOWN
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [str(value)]


def _first_known(*values: object) -> object:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return UNKNOWN


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text
