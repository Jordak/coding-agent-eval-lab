from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Callable

from agentlab.evidence.outcome import OutcomeEvidence


UNKNOWN = "unknown"


@dataclass(frozen=True)
class OperabilityEvidenceRow:
    dimension: str
    facts: tuple[tuple[str, str], ...]


def agent_harness_operability_rows(
    results: list[OutcomeEvidence],
) -> list[OperabilityEvidenceRow]:
    return [
        _row("Agent harness configuration", _configuration_facts(results)),
        _row("Budget controls", _budget_controls_facts(results)),
        _row("Approval boundaries", _approval_boundaries_facts(results)),
        _row("Verifier state", _verifier_state_facts(results)),
        _row("Halt reasons", _halt_reasons_facts(results)),
        _row("Interrupted-run receipt", _interrupted_receipt_facts(results)),
        _row("Tool/patch context", _tool_patch_context_facts(results)),
        _row("Receipt basics", _receipt_basics_facts(results)),
    ]


def format_operability_evidence_markdown(row: OperabilityEvidenceRow) -> str:
    return "<br>".join(
        f"{label}: `{value}`" for label, value in row.facts
    )


def render_agent_harness_operability_table(
    results: list[OutcomeEvidence],
) -> list[str]:
    rows = [
        [row.dimension, format_operability_evidence_markdown(row)]
        for row in agent_harness_operability_rows(results)
    ]
    lines = [
        "### Agent Harness Operability",
        "",
        *_markdown_table(["Operability Dimension", "Evidence"], rows),
    ]
    lines.append("")
    return lines


def _row(
    label: str,
    facts: Iterable[tuple[str, object]],
) -> OperabilityEvidenceRow:
    return OperabilityEvidenceRow(
        dimension=label,
        facts=tuple((fact_label, _format_value(value)) for fact_label, value in facts),
    )


def _configuration_facts(results: list[OutcomeEvidence]) -> list[tuple[str, object]]:
    return [
        ("agent_harness", _result_values(results, lambda result: result.agent_name)),
        (
            "model",
            _result_values(results, lambda result: result.model_name_display),
        ),
        (
            "reasoning_effort",
            _result_values(results, lambda result: result.reasoning_effort_display),
        ),
        ("trials", str(len(results))),
    ]


def _budget_controls_facts(results: list[OutcomeEvidence]) -> list[tuple[str, object]]:
    return [
        ("timeout_seconds", _surface_values(results, "timeout_seconds")),
        (
            "turn_or_step_budget",
            _result_values(results, _explicit_turn_or_step_budget),
        ),
        (
            "observed_input_output_tokens",
            _coverage(
                results,
                lambda result: (
                    result.input_tokens is not None
                    and result.output_tokens is not None
                ),
            ),
        ),
        (
            "observed_cost_usd",
            _coverage(results, lambda result: result.cost_usd is not None),
        ),
        ("configured_token_cost_quota_limits", UNKNOWN),
    ]


def _approval_boundaries_facts(
    results: list[OutcomeEvidence],
) -> list[tuple[str, object]]:
    return [
        ("sandbox_mode", _surface_values(results, "sandbox_mode")),
        ("approval_policy", _surface_values(results, "approval_policy")),
        ("tool_policy", _surface_values(results, "tool_policy")),
        ("memory_scope", _surface_values(results, "memory_scope")),
        ("network_policy", _surface_values(results, "network_policy")),
    ]


def _verifier_state_facts(results: list[OutcomeEvidence]) -> list[tuple[str, object]]:
    return [
        ("final_grader_status", _result_values(results, lambda result: result.status)),
        ("checks_array", _coverage(results, lambda result: bool(result.checks))),
        ("graders_array", _coverage(results, lambda result: bool(result.graders))),
        ("intermediate_verifier_movement", UNKNOWN),
    ]


def _halt_reasons_facts(results: list[OutcomeEvidence]) -> list[tuple[str, object]]:
    return [
        (
            "normalized_or_derived_stop_reason",
            _surface_values(results, "stop_reason"),
        ),
        ("first_class_halt_reason_taxonomy", UNKNOWN),
        ("error_field", _coverage(results, lambda result: result.error is not None)),
        ("budget_operator_interruption_taxonomy", UNKNOWN),
    ]


def _interrupted_receipt_facts(
    results: list[OutcomeEvidence],
) -> list[tuple[str, object]]:
    error_count = sum(1 for result in results if result.error is not None)
    excluded_count = sum(1 for result in results if result.exclusion_reason)
    if error_count == 0 and excluded_count == 0:
        receipt = "unknown: selected evidence has no interrupted/error receipts"
    else:
        receipt = (
            f"errors {error_count}/{len(results)}, "
            f"exclusions {excluded_count}/{len(results)}"
        )
    return [
        ("interrupted_or_error_receipt", receipt),
        ("admission_decision_evidence", _review_coverage(results)),
    ]


def _tool_patch_context_facts(
    results: list[OutcomeEvidence],
) -> list[tuple[str, object]]:
    return [
        (
            "changed_files",
            _coverage(results, lambda result: bool(result.files_changed)),
        ),
        ("commands_run", _coverage(results, lambda result: bool(result.commands_run))),
        ("human_review_overlay", _review_coverage(results)),
        ("transcript", _path_coverage(results, lambda result: result.transcript_path)),
        ("diff_patch", _path_coverage(results, lambda result: result.diff_path)),
    ]


def _receipt_basics_facts(results: list[OutcomeEvidence]) -> list[tuple[str, object]]:
    return [
        ("run_dir", _path_coverage(results, lambda result: result.run_dir)),
        ("report_md", _path_coverage(results, lambda result: result.report_path)),
        ("result_json", _path_coverage(results, lambda result: result.result_path)),
        ("transcript", _path_coverage(results, lambda result: result.transcript_path)),
        ("diff_patch", _path_coverage(results, lambda result: result.diff_path)),
    ]


def _review_coverage(results: list[OutcomeEvidence]) -> str:
    return _coverage(
        results,
        lambda result: (
            bool(result.primary_review_label)
            or bool(result.secondary_review_labels)
            or result.exclusion_reason is not None
        ),
    )


def _surface_values(results: list[OutcomeEvidence], field: str) -> str:
    return _result_values(results, lambda result: result.run_surface.get(field))


def _explicit_turn_or_step_budget(result: OutcomeEvidence) -> object:
    budget = result.run_surface.get("turn_or_step_budget")
    if isinstance(budget, Mapping) and set(budget) == {"reasoning_effort"}:
        return None
    return budget


def _result_values(
    results: list[OutcomeEvidence],
    value_getter: Callable[[OutcomeEvidence], object],
) -> str:
    if not results:
        return UNKNOWN
    known_values: set[str] = set()
    unknown_count = 0
    for result in results:
        formatted = _format_value(value_getter(result))
        if formatted == UNKNOWN:
            unknown_count += 1
        else:
            known_values.add(formatted)

    if not known_values:
        return UNKNOWN
    value_text = "; ".join(sorted(known_values))
    if unknown_count:
        value_text += f"; unknown in {unknown_count}/{len(results)}"
    return value_text


def _coverage(
    results: list[OutcomeEvidence],
    predicate: Callable[[OutcomeEvidence], bool],
) -> str:
    if not results:
        return UNKNOWN
    count = sum(1 for result in results if predicate(result))
    if count == 0:
        return UNKNOWN
    return f"{count}/{len(results)}"


def _path_coverage(
    results: list[OutcomeEvidence],
    path_getter: Callable[[OutcomeEvidence], object],
) -> str:
    return _coverage(results, lambda result: bool(path_getter(result)))


def _format_value(value: object) -> str:
    if value is None:
        return UNKNOWN
    if isinstance(value, str):
        text = value.strip()
        return text or UNKNOWN
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, Mapping):
        if not value:
            return "none"
        return json.dumps(dict(value), sort_keys=True)
    if isinstance(value, (list, tuple)):
        if not value:
            return "none"
        return ", ".join(_format_value(item) for item in value)
    return str(value)


def _markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    table = [
        "| " + " | ".join(_escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return table


def _escape_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")
