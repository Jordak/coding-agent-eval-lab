from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ModelIdentity:
    model_name: str | None = None
    model_source: str = "unknown"
    requested_model_name: str | None = None
    reasoning_effort: str | None = None
    model_provider: str | None = None
    codex_thread_id: str | None = None
    codex_thread_source: str | None = None
    cli_version: str | None = None


def model_identity_from_events(
    events_jsonl: str,
    *,
    requested_model_name: str | None = None,
) -> ModelIdentity:
    event_model = parse_model_name_from_events(events_jsonl)
    if event_model:
        return ModelIdentity(
            model_name=event_model,
            model_source="events",
            requested_model_name=requested_model_name,
        )
    if requested_model_name:
        return ModelIdentity(
            model_name=requested_model_name,
            model_source="explicit",
            requested_model_name=requested_model_name,
        )
    return ModelIdentity(requested_model_name=requested_model_name)


def parse_model_name_from_events(events_jsonl: str) -> str | None:
    fallback_model = None
    for event in _iter_json_messages(events_jsonl):
        for candidate in _direct_model_candidates(event):
            if candidate:
                return candidate
        fallback_model = fallback_model or _single_usage_model(event)
    return fallback_model


def _iter_json_messages(events_jsonl: str) -> Iterable[dict[str, Any]]:
    for line in events_jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def _direct_model_candidates(event: dict[str, Any]) -> Iterable[str | None]:
    yield _string_value(event, "model")
    yield _string_value(event, "model_name")
    yield _string_value(event, "modelName")

    for container_key in ["message", "response", "item", "turn"]:
        container = event.get(container_key)
        if not isinstance(container, dict):
            continue
        yield _string_value(container, "model")
        yield _string_value(container, "model_name")
        yield _string_value(container, "modelName")


def _single_usage_model(event: dict[str, Any]) -> str | None:
    for key in ["modelUsage", "model_usage"]:
        usage = event.get(key)
        if isinstance(usage, dict) and len(usage) == 1:
            model_name = next(iter(usage))
            if isinstance(model_name, str) and model_name:
                return model_name
    return None


def _string_value(values: dict[str, Any], key: str) -> str | None:
    value = values.get(key)
    if isinstance(value, str) and value:
        return value
    return None
