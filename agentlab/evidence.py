from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from agentlab.outcome_evidence import (
    normalize_result_dicts,
    result_files_changed_count,
)
from agentlab.summary import summarize_trials
from agentlab.validity import exclusion_reason, trial_validity


def render_capability_evidence_digest(
    results: Iterable[Dict[str, Any]],
    selection_context: Mapping[str, object] | None = None,
) -> str:
    results = normalize_result_dicts(results)
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
                        summary.model_name,
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


def _trial_row(result: Dict[str, Any]) -> List[object]:
    return [
        result.get("trial_id", result.get("run_id", "")),
        result.get("task_id", ""),
        result.get("agent_name", ""),
        result.get("model_name") or "",
        result.get("status", ""),
        trial_validity(result),
        _review_label(result),
        _format_labels(_secondary_review_labels(result)),
        exclusion_reason(result),
        result_files_changed_count(result),
        result.get("lines_added", 0),
        result.get("lines_deleted", 0),
        _unknown_if_none(result.get("input_tokens")),
        _unknown_if_none(result.get("output_tokens")),
        _unknown_if_none(result.get("reasoning_output_tokens")),
        _unknown_if_none(result.get("cost_usd")),
        result.get("duration_ms", 0),
        _markdown_link("report", result.get("report_path")),
        _markdown_link("transcript", result.get("transcript_path")),
        _markdown_link("diff", result.get("diff_path")),
        _markdown_link("result", result.get("run_dir"), "result.json"),
    ]


def _markdown_table(headers: List[str], rows: List[List[object]]) -> List[str]:
    table = [
        "| " + " | ".join(_escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return table


def _markdown_link(label: str, path: object, child: str | None = None) -> str:
    if not path:
        return ""
    target = Path(str(path))
    if child is not None:
        target = target / child
    target_text = str(target)
    if " " in target_text:
        target_text = f"<{target_text}>"
    return f"[{label}]({target_text})"


def _review_label(result: Dict[str, Any]) -> str:
    review = result.get("review")
    if isinstance(review, dict):
        return str(review.get("primary_label", ""))
    return ""


def _secondary_review_labels(result: Dict[str, Any]) -> List[str]:
    review = result.get("review")
    if not isinstance(review, dict):
        return []
    labels = review.get("secondary_labels")
    if not isinstance(labels, list):
        return []
    return [str(label) for label in labels if label]


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
