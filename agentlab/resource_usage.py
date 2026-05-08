from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ResourceUsage:
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    cost_usd: float | None = None

    @property
    def total_tokens(self) -> int | None:
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)


def resource_usage_to_dict(usage: ResourceUsage) -> Dict[str, Any]:
    return {
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": usage.cached_input_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_output_tokens": usage.reasoning_output_tokens,
        "total_tokens": usage.total_tokens,
        "cost_usd": usage.cost_usd,
    }


def parse_resource_usage_events(events_jsonl: str) -> ResourceUsage:
    totals: dict[str, int] = {}
    cost_usd = 0.0
    saw_cost = False
    for line in events_jsonl.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue

        for key in [
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
        ]:
            value = usage.get(key)
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value

        for key in ["cost_usd", "estimated_cost_usd"]:
            value = usage.get(key)
            if isinstance(value, (int, float)):
                cost_usd += float(value)
                saw_cost = True

    return ResourceUsage(
        input_tokens=totals.get("input_tokens"),
        cached_input_tokens=totals.get("cached_input_tokens"),
        output_tokens=totals.get("output_tokens"),
        reasoning_output_tokens=totals.get("reasoning_output_tokens"),
        cost_usd=cost_usd if saw_cost else None,
    )
