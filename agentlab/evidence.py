from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from agentlab.outcome_evidence import (
    OutcomeEvidence,
    normalize_outcome_evidences,
)
from agentlab.summary import summarize_trials


def render_capability_evidence_digest(
    results: Iterable[Mapping[str, Any] | OutcomeEvidence],
    selection_context: Mapping[str, object] | None = None,
) -> str:
    results = normalize_outcome_evidences(results)
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
        f"- Agent trials: `{len(results)}`",
    ]
    if selection_context is not None:
        lines.extend(_selection_context_lines(selection_context))
    lines.extend(
        [
            "",
            "## Aggregate Summaries",
            "",
        ]
    )

    summaries = summarize_trials(results)
    if not summaries:
        lines.append("No agent-trial results found.")
    else:
        lines.extend(
            _markdown_table(
                [
                    "Suite",
                    "Type",
                    "Task",
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
                    "Primary Review Labels",
                    "Secondary Review Labels",
                    "Exclusions",
                ],
                [
                    [
                        summary.eval_suite,
                        summary.eval_type,
                        summary.task_id,
                        summary.agent_name,
                        summary.model_name_display,
                        summary.reasoning_effort_display,
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
                        _format_counts(summary.review_labels),
                        _format_counts(summary.secondary_review_labels),
                        _format_counts(summary.exclusion_reasons),
                    ]
                    for summary in summaries
                ],
            )
        )

    lines.extend(["", "## Trial Evidence", ""])
    if not results:
        lines.append("No agent-trial results found.")
    else:
        lines.extend(
            _markdown_table(
                [
                    "Trial",
                    "Task",
                    "Agent Harness",
                    "Model",
                    "Effort",
                    "Grader Outcome",
                    "Validity",
                    "Primary Review Label",
                    "Secondary Review Labels",
                    "Exclusion",
                    "Files",
                    "+Lines",
                    "-Lines",
                    "Input Tokens",
                    "Output Tokens",
                    "Reasoning Tokens",
                    "Cost USD",
                    "Duration ms",
                    "Report",
                    "Transcript",
                    "Diff",
                    "Result",
                ],
                [_trial_row(result) for result in results],
            )
        )

    lines.append("")
    return "\n".join(lines)


def render_evidence_appendix(results: Iterable[Dict[str, Any]]) -> str:
    return render_capability_evidence_digest(results)


def _selection_context_lines(context: Mapping[str, object]) -> list[str]:
    lines: list[str] = []
    name = context.get("name")
    if name:
        lines.append(f"- Evidence set: `{name}`")
    source_path = context.get("source_path")
    if source_path:
        lines.append(f"- Evidence set source: `{source_path}`")
    description = context.get("description")
    if description:
        lines.append(f"- Evidence set description: {description}")
    selected_entries = context.get("selected_entries")
    if selected_entries is not None:
        lines.append(f"- Selected entries: `{selected_entries}`")
    selected_result_files = context.get("selected_result_files")
    if selected_result_files is not None:
        lines.append(f"- Selected result files: `{selected_result_files}`")
    return lines


def _trial_row(result: OutcomeEvidence) -> List[object]:
    return [
        result.trial_id,
        result.task_id,
        result.agent_name,
        result.model_name_display,
        result.reasoning_effort_display,
        result.status,
        result.trial_validity,
        result.primary_review_label,
        _format_labels(result.secondary_review_labels),
        result.exclusion_reason_display,
        result.files_changed_count,
        result.lines_added,
        result.lines_deleted,
        _unknown_if_none(result.input_tokens),
        _unknown_if_none(result.output_tokens),
        _unknown_if_none(result.reasoning_output_tokens),
        _unknown_if_none(result.cost_usd),
        result.duration_ms,
        _markdown_link("report", result.report_path),
        _markdown_link("transcript", result.transcript_path),
        _markdown_link("diff", result.diff_path),
        _markdown_link("result", result.result_path),
    ]


def _markdown_table(headers: List[str], rows: List[List[object]]) -> List[str]:
    table = [
        "| " + " | ".join(_escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return table


def _markdown_link(label: str, path: object) -> str:
    if not path:
        return ""
    target = Path(str(path))
    target_text = str(target)
    if " " in target_text:
        target_text = f"<{target_text}>"
    return f"[{label}]({target_text})"


def _format_rate(value: float) -> str:
    return f"{value:.2f}"


def _format_counts(counts: Dict[str, int]) -> str:
    if not counts:
        return ""
    return ", ".join(f"{label}:{count}" for label, count in counts.items())


def _format_labels(labels: List[str]) -> str:
    return ", ".join(labels)


def _unknown_if_none(value: object) -> object:
    if value is None:
        return "unknown"
    return value


def _escape_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")
