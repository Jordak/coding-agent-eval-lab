from __future__ import annotations

from typing import Any, Dict, Mapping


def unknown_runtime_accountability(
    cost_usd: float | None = None,
) -> Dict[str, Any]:
    return {
        "account": None,
        "billing_context": None,
        "cost_usd": cost_usd,
    }


def normalize_agent_harness_config(
    config: Mapping[str, Any] | None,
    *,
    agent_name: str | None = None,
    model_name: str | None = None,
    cost_usd: float | None = None,
) -> Dict[str, Any]:
    normalized = dict(config or {})
    normalized.setdefault("agent_harness", agent_name)
    normalized.setdefault("model_name", model_name)

    runtime_accountability = normalized.get("runtime_accountability")
    if not isinstance(runtime_accountability, dict):
        runtime_accountability = {}
    else:
        runtime_accountability = dict(runtime_accountability)

    for key, value in unknown_runtime_accountability(cost_usd).items():
        runtime_accountability.setdefault(key, value)

    normalized["runtime_accountability"] = runtime_accountability
    return normalized
