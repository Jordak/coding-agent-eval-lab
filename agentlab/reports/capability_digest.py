from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

from agentlab.evidence.outcome import OutcomeEvidence
from agentlab.evidence.summary import TrialGroupSummary, summarize_trials
from agentlab.reports.operability_evidence import (
    render_agent_harness_operability_table,
)
from agentlab.reports.patch_caveats import (
    has_patch_size_caveats,
    has_summary_patch_size_caveats,
    patch_size_caveat_note,
    patch_stat,
    setup_created_untracked_coverage_caveat_count,
    setup_created_untracked_coverage_caveat_note,
    summary_has_patch_size_caveat,
)
from agentlab.reports.scope_oracle import compact_scope_oracle_metadata


PORTABLE_MARKDOWN_POLICY = (
    "Portable Markdown policy: checked-in digests intentionally omit per-trial "
    "artifact links because local `runs/` artifacts are ignored and can "
    "disappear after temporary worktree cleanup. HTML reports generated from "
    "durable snapshot-backed evidence may be checked in when they pass the "
    "same no-local-artifact-link portability check."
)


@dataclass(frozen=True)
class MarkdownRunContext:
    eval_suite: str
    agent_name: str
    model_name: str
    reasoning_effort: str
    summaries: List[TrialGroupSummary]
    results: List[OutcomeEvidence]

    @property
    def label(self) -> str:
        return (
            f"{self.eval_suite} / {self.agent_name} / "
            f"{self.model_name} / {self.reasoning_effort}"
        )


def render_capability_evidence_digest(
    results: Iterable[OutcomeEvidence],
    selection_context: Mapping[str, object] | None = None,
) -> str:
    results = list(results)
    lines = [
        "# Capability Evidence Digest",
        "",
        (
            "This digest is generated from stored agent-trial results. It "
            "reports evidence only; hand-authored agent capability reports "
            "should interpret these observations within the evaluated "
            "conditions."
        ),
        "",
        PORTABLE_MARKDOWN_POLICY,
        "",
        f"- Agent trials: `{len(results)}`",
    ]
    if selection_context is not None:
        lines.extend(_selection_context_lines(selection_context))
    summaries = summarize_trials(results)
    if not summaries:
        lines.extend(["", "## Run Contexts", ""])
        lines.append("No agent-trial results found.")
    else:
        contexts = _run_contexts(summaries, results)
        lines.append("")
        for context in contexts:
            lines.extend(_run_context_lines(context))

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def render_evidence_appendix(results: Iterable[OutcomeEvidence]) -> str:
    return render_capability_evidence_digest(results)


def _run_contexts(
    summaries: List[TrialGroupSummary],
    results: List[OutcomeEvidence],
) -> List[MarkdownRunContext]:
    summaries_by_key: Dict[tuple[str, str, str, str], List[TrialGroupSummary]] = {}
    results_by_key: Dict[tuple[str, str, str, str], List[OutcomeEvidence]] = {}

    for summary in summaries:
        summaries_by_key.setdefault(_summary_context_key(summary), []).append(summary)
    for result in results:
        results_by_key.setdefault(_result_context_key(result), []).append(result)

    contexts: List[MarkdownRunContext] = []
    for key in sorted(set(summaries_by_key) | set(results_by_key)):
        eval_suite, agent_name, model_name, reasoning_effort = key
        contexts.append(
            MarkdownRunContext(
                eval_suite=eval_suite or "unknown",
                agent_name=agent_name or "unknown",
                model_name=model_name or "unknown",
                reasoning_effort=reasoning_effort or "unknown",
                summaries=sorted(
                    summaries_by_key.get(key, []),
                    key=lambda summary: (summary.eval_type, summary.task_id),
                ),
                results=results_by_key.get(key, []),
            )
        )
    return contexts


def _summary_context_key(summary: TrialGroupSummary) -> tuple[str, str, str, str]:
    return (
        summary.eval_suite,
        summary.agent_name,
        summary.model_name_display,
        summary.reasoning_effort_display,
    )


def _result_context_key(result: OutcomeEvidence) -> tuple[str, str, str, str]:
    return (
        result.eval_suite,
        result.agent_name,
        result.model_name_display,
        result.reasoning_effort_display,
    )


def _run_context_lines(context: MarkdownRunContext) -> List[str]:
    lines = [
        f"## Run Context: {context.label}",
        "",
        f"- Suite: `{context.eval_suite}`",
        f"- Agent Harness: `{context.agent_name}`",
        f"- Model: `{context.model_name}`",
        f"- Effort: `{context.reasoning_effort}`",
        "",
    ]
    lines.extend(_run_surface_summary_lines(context.results))
    lines.extend(render_agent_harness_operability_table(context.results))
    lines.extend(_aggregate_summary_tables(context.summaries, context.results))
    lines.extend(["", "### Trial Evidence", ""])
    lines.extend(
        _markdown_table(
            [
                "Task",
                "Type",
                "Trial",
                "Grader Outcome",
                "Validity",
                "Primary Review Label",
                "Secondary Review Labels",
                "Exclusion",
                "Files",
                "+Lines",
                "-Lines",
                "Input Tokens",
                "Cached Input Tokens",
                "Output Tokens",
                "Reasoning Tokens",
                "Cost USD",
                "Duration ms",
                "Scope Oracle",
                "Task Provenance",
            ],
            [_trial_row(result) for result in context.results],
        )
    )
    if has_patch_size_caveats(context.results):
        lines.extend(
            [
                "",
                patch_size_caveat_note(marker="`*`"),
            ]
        )
    setup_coverage_caveat_count = (
        setup_created_untracked_coverage_caveat_count(context.results)
    )
    if setup_coverage_caveat_count:
        lines.extend(
            [
                "",
                setup_created_untracked_coverage_caveat_note(
                    count=setup_coverage_caveat_count
                ),
            ]
        )
    lines.append("")
    return lines


def _run_surface_summary_lines(results: List[OutcomeEvidence]) -> List[str]:
    rows = [
        [
            _surface_context_value(results, "execution_surface"),
            _surface_context_value(results, "runtime_version"),
            _surface_context_value(results, "model_identity_source"),
            _surface_context_value(results, "sandbox_mode"),
            _surface_context_value(results, "approval_policy"),
            _surface_context_value(results, "memory_scope"),
            _surface_context_value(results, "network_policy"),
            _surface_context_value(results, "timeout_seconds"),
            _surface_context_value(results, "stop_reason"),
            _surface_context_value(results, "workspace_history_policy"),
            _surface_context_value(results, "workspace_base_ref"),
        ]
    ]
    return [
        "### Run Surface",
        "",
        *_markdown_table(
            [
                "Execution Surface",
                "Runtime Version",
                "Model Source",
                "Sandbox",
                "Approval",
                "Memory",
                "Network",
                "Timeout Seconds",
                "Stop Reason",
                "Workspace History",
                "Workspace Base Ref",
            ],
            rows,
        ),
        "",
    ]


def _surface_context_value(
    results: List[OutcomeEvidence],
    field: str,
) -> str:
    values = sorted(
        {
            _format_run_surface_value(result.run_surface.get(field))
            for result in results
        }
    )
    if not values:
        return "unknown"
    if len(values) == 1:
        return values[0]
    return "mixed: " + "; ".join(values)


def _aggregate_summary_tables(
    summaries: List[TrialGroupSummary],
    results: List[OutcomeEvidence],
) -> List[str]:
    lines: List[str] = []
    lines.extend(["### Outcome Summary", ""])
    lines.extend(
        _markdown_table(
            [
                "Task",
                "Type",
                "Total",
                "Fair",
                "Excluded",
                "Passes",
                "Accepted",
                "Pass Rate",
                "pass@k",
                "pass^k",
            ],
            [_outcome_summary_row(summary) for summary in summaries],
        )
    )
    lines.extend(["", "### Token Summary", ""])
    lines.extend(
        _markdown_table(
            [
                "Task",
                "Type",
                "IO Tokens",
                "Cached Tokens",
                "Reason Tokens",
                "IO Tok / Verified",
                "IO Tok / Accepted",
                "Cached Tok / Verified",
                "Reason Tok / Verified",
            ],
            [_token_summary_row(summary) for summary in summaries],
        )
    )
    lines.extend(["", "### Review and Patch Summary", ""])
    lines.extend(
        _markdown_table(
            [
                "Task",
                "Type",
                "Median ms",
                "Median Files",
                "Median +Lines",
                "Median -Lines",
                "Primary Review Labels",
                "Secondary Review Labels",
                "Exclusions",
            ],
            [_review_summary_row(summary, results) for summary in summaries],
        )
    )
    if has_summary_patch_size_caveats(summaries, results):
        lines.extend(
            [
                "",
                patch_size_caveat_note(marker="`*`"),
            ]
        )
    return lines


def _summary_identity(summary: TrialGroupSummary) -> List[object]:
    return [
        summary.task_id,
        summary.eval_type,
    ]


def _outcome_summary_row(summary: TrialGroupSummary) -> List[object]:
    return _summary_identity(summary) + [
        summary.total_trials,
        summary.trials,
        summary.excluded_trials,
        summary.passes,
        summary.accepted_results,
        _format_rate(summary.pass_rate),
        _format_rate(summary.pass_at_k),
        _format_rate(summary.pass_caret_k),
    ]


def _token_summary_row(summary: TrialGroupSummary) -> List[object]:
    return _summary_identity(summary) + [
        _format_optional_number(summary.total_input_output_tokens),
        _format_optional_number(summary.total_cached_input_tokens),
        _format_optional_number(summary.total_reasoning_output_tokens),
        _format_optional_number(summary.input_output_tokens_per_verified_result),
        _format_optional_number(summary.input_output_tokens_per_accepted_result),
        _format_optional_number(summary.cached_input_tokens_per_verified_result),
        _format_optional_number(summary.reasoning_output_tokens_per_verified_result),
    ]


def _review_summary_row(
    summary: TrialGroupSummary,
    results: List[OutcomeEvidence],
) -> List[object]:
    has_patch_size_caveat = summary_has_patch_size_caveat(summary, results)
    return _summary_identity(summary) + [
        summary.median_duration_ms,
        summary.median_files_changed,
        patch_stat(
            _format_optional_number(summary.median_lines_added),
            has_patch_size_caveat,
        ),
        patch_stat(
            _format_optional_number(summary.median_lines_deleted),
            has_patch_size_caveat,
        ),
        _format_counts(summary.review_labels),
        _format_counts(summary.secondary_review_labels),
        _format_counts(summary.exclusion_reasons),
    ]


def _selection_context_lines(context: Mapping[str, object]) -> list[str]:
    lines: list[str] = []
    evidence_sets = context.get("evidence_sets")
    if isinstance(evidence_sets, list):
        lines.append(f"- Evidence sets: `{len(evidence_sets)}`")
        for evidence_set in evidence_sets:
            if isinstance(evidence_set, Mapping):
                lines.extend(_evidence_set_context_lines(evidence_set))
    name = context.get("name")
    if name:
        lines.append(f"- Evidence set: `{name}`")
    source_path = context.get("source_path")
    if source_path:
        lines.append(f"- Evidence set source: `{source_path}`")
    snapshot_path = context.get("outcome_evidence_snapshot")
    if snapshot_path:
        lines.append(f"- Outcome evidence snapshot: `{snapshot_path}`")
    description = context.get("description")
    if description:
        lines.append(f"- Evidence set description: {description}")
    selected_entries = context.get("selected_entries")
    if selected_entries is not None:
        lines.append(f"- Selected entries: `{selected_entries}`")
    selected_result_files = context.get("selected_result_files")
    if selected_result_files is not None:
        lines.append(f"- Selected result files: `{selected_result_files}`")
    selected_snapshot_records = context.get("selected_snapshot_records")
    if selected_snapshot_records is not None:
        lines.append(f"- Selected snapshot records: `{selected_snapshot_records}`")
    return lines


def _evidence_set_context_lines(context: Mapping[str, object]) -> list[str]:
    lines: list[str] = []
    name = context.get("name") or "unknown"
    selected_result_files = context.get("selected_result_files")
    selected_text = (
        f", selected result files: `{selected_result_files}`"
        if selected_result_files is not None
        else ""
    )
    source_path = context.get("source_path")
    source_text = f", source: `{source_path}`" if source_path else ""
    snapshot_path = context.get("outcome_evidence_snapshot")
    snapshot_text = f", snapshot: `{snapshot_path}`" if snapshot_path else ""
    lines.append(
        f"- Evidence set: `{name}`{selected_text}{source_text}{snapshot_text}"
    )
    description = context.get("description")
    if description:
        lines.append(f"- Evidence set description: {description}")
    return lines


def _trial_row(result: OutcomeEvidence) -> List[object]:
    has_patch_size_caveat = bool(result.setup_created_untracked_changed_paths)
    return [
        result.task_id,
        result.eval_type,
        result.trial_id,
        result.status,
        result.trial_validity,
        result.primary_review_label,
        _format_labels(result.secondary_review_labels),
        result.exclusion_reason_display,
        result.files_changed_count,
        patch_stat(result.lines_added, has_patch_size_caveat),
        patch_stat(result.lines_deleted, has_patch_size_caveat),
        _unknown_if_none(result.input_tokens),
        _unknown_if_none(result.cached_input_tokens),
        _unknown_if_none(result.output_tokens),
        _unknown_if_none(result.reasoning_output_tokens),
        _unknown_if_none(result.cost_usd),
        result.duration_ms,
        compact_scope_oracle_metadata(result.scope_oracle),
        _trial_provenance(result),
    ]


def _trial_provenance(result: OutcomeEvidence) -> str:
    return "; ".join(
        [
            f"repo={_display_unknown(result.task_repo)}",
            f"commit={_display_unknown(result.task_commit)}",
            (
                "workspace_base_ref="
                f"{_format_run_surface_value(result.run_surface.get('workspace_base_ref'))}"
            ),
        ]
    )


def _markdown_table(headers: List[str], rows: List[List[object]]) -> List[str]:
    table = [
        "| " + " | ".join(_escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return table


def _format_rate(value: float) -> str:
    return f"{value:.2f}"


def _format_optional_number(value: object) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def _format_counts(counts: Dict[str, int]) -> str:
    if not counts:
        return ""
    return ", ".join(f"{label}:{count}" for label, count in counts.items())


def _format_labels(labels: List[str]) -> str:
    return ", ".join(labels)


def _format_run_surface_value(value: object) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, list):
        if not value:
            return "none"
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    text = str(value)
    if not text:
        return "unknown"
    return text


def _unknown_if_none(value: object) -> object:
    if value is None:
        return "unknown"
    return value


def _display_unknown(value: object) -> str:
    text = "" if value is None else str(value)
    return text or "unknown"


def _escape_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")
