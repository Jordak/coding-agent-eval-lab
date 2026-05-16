from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agentlab.evidence import _format_counts, _format_rate, _markdown_table
from agentlab.evidence_sets import EvidenceSet
from agentlab.outcome_evidence import normalize_result_dicts
from agentlab.summary import result_reasoning_effort, summarize_trials
from agentlab.validity import trial_is_valid


@dataclass(frozen=True)
class ComparisonEvidenceSource:
    name: str
    description: str
    source_path: str
    selected_entries: int
    selected_result_files: int
    results: list[Dict[str, Any]]

    @classmethod
    def from_evidence_set(
        cls,
        evidence_set: EvidenceSet,
        results: Iterable[Dict[str, Any]],
    ) -> "ComparisonEvidenceSource":
        return cls(
            name=evidence_set.name,
            description=evidence_set.description,
            source_path=str(evidence_set.source_path),
            selected_entries=len(evidence_set.trial_entries),
            selected_result_files=len(evidence_set.result_files),
            results=list(results),
        )


def render_comparison_evidence_digest(
    sources: Iterable[ComparisonEvidenceSource],
) -> str:
    normalized_sources = [
        ComparisonEvidenceSource(
            name=source.name,
            description=source.description,
            source_path=source.source_path,
            selected_entries=source.selected_entries,
            selected_result_files=source.selected_result_files,
            results=normalize_result_dicts(source.results),
        )
        for source in sources
    ]
    total_results = sum(len(source.results) for source in normalized_sources)

    lines = [
        "# Comparison Evidence Digest",
        "",
        (
            "This digest is generated from selected evidence-set manifests. It "
            "reports comparison evidence only; hand-authored comparison reports "
            "should remain the interpretation layer."
        ),
        "",
        f"- Evidence sets: `{len(normalized_sources)}`",
        f"- Agent trials: `{total_results}`",
        "",
        "## Evidence Sets",
        "",
    ]

    if not normalized_sources:
        lines.append("No evidence sets provided.")
    else:
        lines.extend(_source_table(normalized_sources))

    lines.extend(["", "## Task-Aligned Summaries", ""])
    rows = _summary_rows(normalized_sources)
    if not rows:
        lines.append("No agent-trial results found.")
    else:
        lines.extend(
            _markdown_table(
                [
                    "Task",
                    "Evidence Set",
                    "Suite",
                    "Type",
                    "Agent Harness",
                    "Model",
                    "Effort",
                    "Total",
                    "Fair",
                    "Excluded",
                    "Passes",
                    "Pass Rate",
                    "pass@k",
                    "pass^k",
                    "Median ms",
                    "Median Files",
                    "Median +Lines",
                    "Median -Lines",
                    "Total Input Tokens",
                    "Total Cached Input Tokens",
                    "Total Output Tokens",
                    "Total Reasoning Tokens",
                    "Total Cost USD",
                    "Primary Review Labels",
                    "Secondary Review Labels",
                    "Exclusions",
                    "Evidence Gaps",
                ],
                [row.values for row in rows],
            )
        )

    lines.append("")
    return "\n".join(lines)


@dataclass(frozen=True)
class _RenderedSummaryRow:
    sort_key: tuple[str, str, str, str, str, str, str]
    values: list[object]


_RESOURCE_FIELDS = [
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "cost_usd",
]


def _source_table(sources: list[ComparisonEvidenceSource]) -> List[str]:
    return _markdown_table(
        [
            "Evidence Set",
            "Source",
            "Description",
            "Selected Entries",
            "Result Files",
            "Agent Trials",
        ],
        [
            [
                source.name,
                _display_path(source.source_path),
                source.description,
                source.selected_entries,
                source.selected_result_files,
                len(source.results),
            ]
            for source in sources
        ],
    )


def _summary_rows(
    sources: list[ComparisonEvidenceSource],
) -> list[_RenderedSummaryRow]:
    rows: list[_RenderedSummaryRow] = []
    for source in sources:
        groups = _group_results(source.results)
        for group_results in groups.values():
            summary = summarize_trials(group_results)[0]
            resource_summary = _resource_summary(group_results)
            model = _display_gap_value(summary.model_name)
            effort = _display_gap_value(summary.reasoning_effort)
            values = [
                summary.task_id,
                source.name,
                summary.eval_suite,
                summary.eval_type,
                summary.agent_name,
                model,
                effort,
                summary.total_trials,
                summary.trials,
                summary.excluded_trials,
                summary.passes,
                _format_rate(summary.pass_rate),
                _format_rate(summary.pass_at_k),
                _format_rate(summary.pass_caret_k),
                summary.median_duration_ms,
                summary.median_files_changed,
                summary.median_lines_added,
                summary.median_lines_deleted,
                resource_summary["input_tokens"],
                resource_summary["cached_input_tokens"],
                resource_summary["output_tokens"],
                resource_summary["reasoning_output_tokens"],
                resource_summary["cost_usd"],
                _format_counts(summary.review_labels),
                _format_counts(summary.secondary_review_labels),
                _format_counts(summary.exclusion_reasons),
                _format_evidence_gaps(
                    model_name=summary.model_name,
                    reasoning_effort=summary.reasoning_effort,
                    group_results=group_results,
                ),
            ]
            rows.append(
                _RenderedSummaryRow(
                    sort_key=(
                        summary.task_id,
                        summary.eval_suite,
                        summary.eval_type,
                        source.name,
                        summary.agent_name,
                        model,
                        effort,
                    ),
                    values=values,
                )
            )
    return sorted(rows, key=lambda row: row.sort_key)


def _group_results(
    results: Iterable[Dict[str, Any]],
) -> dict[Tuple[str, str, str, str, str, str], list[Dict[str, Any]]]:
    groups: dict[
        Tuple[str, str, str, str, str, str],
        list[Dict[str, Any]],
    ] = defaultdict(list)
    for result in results:
        groups[_result_group_key(result)].append(result)
    return dict(groups)


def _result_group_key(result: Mapping[str, Any]) -> Tuple[str, str, str, str, str, str]:
    return (
        str(result.get("eval_suite", "")),
        str(result.get("eval_type", "")),
        str(result.get("task_id", "")),
        str(result.get("agent_name", "")),
        str(result.get("model_name") or ""),
        result_reasoning_effort(result),
    )


def _resource_summary(results: list[Dict[str, Any]]) -> dict[str, object]:
    fair_results = [result for result in results if trial_is_valid(result)]
    return {
        field: _format_resource_total(
            [_resource_value(result, field) for result in fair_results],
            is_cost=field == "cost_usd",
        )
        for field in _RESOURCE_FIELDS
    }


def _format_resource_total(
    values: Iterable[float | int | None],
    *,
    is_cost: bool,
) -> object:
    all_values = list(values)
    known_values = [value for value in all_values if value is not None]
    if not all_values or not known_values:
        return "unknown"

    total = sum(known_values)
    if is_cost:
        rendered: object = _format_cost(total)
    elif all(float(value).is_integer() for value in known_values):
        rendered = int(total)
    else:
        rendered = total

    if len(known_values) != len(all_values):
        return f"{rendered} ({len(known_values)}/{len(all_values)} known)"
    return rendered


def _resource_value(result: Mapping[str, Any], field: str) -> float | int | None:
    value = result.get(field)
    if value is None:
        resource_usage = result.get("resource_usage")
        if isinstance(resource_usage, Mapping):
            value = resource_usage.get(field)
    if value is None and field == "cost_usd":
        config = result.get("agent_harness_config")
        if isinstance(config, Mapping):
            runtime = config.get("runtime_accountability")
            if isinstance(runtime, Mapping):
                value = runtime.get("cost_usd")
    return _coerce_number(value)


def _coerce_number(value: object) -> float | int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    try:
        number = float(str(value))
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def _format_evidence_gaps(
    *,
    model_name: str,
    reasoning_effort: str,
    group_results: list[Dict[str, Any]],
) -> str:
    fair_results = [result for result in group_results if trial_is_valid(result)]
    identity_count = len(group_results)
    gaps: list[str] = []
    if not model_name:
        gaps.append(f"model_name:{identity_count}")
    if not reasoning_effort:
        gaps.append(f"reasoning_effort:{identity_count}")
    for field in _RESOURCE_FIELDS:
        missing = sum(
            1
            for result in fair_results
            if _resource_value(result, field) is None
        )
        if missing:
            gaps.append(f"{field}:{missing}")
    return ", ".join(gaps)


def _display_gap_value(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value)
    if not text:
        return "unknown"
    return text


def _format_cost(value: float | int) -> str:
    text = f"{float(value):.4f}"
    return text.rstrip("0").rstrip(".")


def _display_path(value: str) -> str:
    path = Path(value)
    if not path.name:
        return value
    return str(path)
