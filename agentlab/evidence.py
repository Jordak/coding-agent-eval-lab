from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from agentlab.summary import summarize_trials
from agentlab.validity import exclusion_reason, trial_validity


def render_evidence_appendix(results: Iterable[Dict[str, Any]]) -> str:
    results = list(results)
    lines = [
        "# Capability Report Evidence Appendix",
        "",
        (
            "This appendix is generated from stored agent-trial results. It "
            "reports evidence only; human-authored capability reports should "
            "interpret these observations within the evaluated conditions."
        ),
        "",
        f"- Agent trials: `{len(results)}`",
        "",
        "## Aggregate Summaries",
        "",
    ]

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
                    "Human Reviews",
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
                    "Human Review",
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


def _trial_row(result: Dict[str, Any]) -> List[object]:
    return [
        result.get("trial_id", result.get("run_id", "")),
        result.get("task_id", ""),
        result.get("agent_name", ""),
        result.get("model_name") or "",
        result.get("status", ""),
        trial_validity(result),
        _review_label(result),
        exclusion_reason(result),
        len(result.get("files_changed") or []),
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


def _format_rate(value: float) -> str:
    return f"{value:.2f}"


def _format_counts(counts: Dict[str, int]) -> str:
    if not counts:
        return ""
    return ", ".join(f"{label}:{count}" for label, count in counts.items())


def _unknown_if_none(value: object) -> object:
    if value is None:
        return "unknown"
    return value


def _escape_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")
