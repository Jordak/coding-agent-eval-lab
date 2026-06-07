from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from agentlab.evidence.outcome import OutcomeEvidence
from agentlab.evidence.summary import TrialGroupSummary, summarize_trials
from agentlab.reports.operability_evidence import (
    agent_harness_operability_rows,
)


INTRO_TEXT = (
    "This digest is generated from stored agent-trial results. It reports "
    "evidence only; hand-authored agent capability reports should interpret "
    "these observations within the evaluated conditions."
)

NUMERIC_HEADERS = {
    "Total",
    "Fair",
    "Excluded",
    "Passes",
    "Accepted",
    "Pass Rate",
    "pass@k",
    "pass^k",
    "IO Tokens",
    "Cached Tokens",
    "Reason Tokens",
    "IO Tok / Verified",
    "IO Tok / Accepted",
    "Cached Tok / Verified",
    "Reason Tok / Verified",
    "Median ms",
    "Median Files",
    "Median +Lines",
    "Median -Lines",
    "Files",
    "+Lines",
    "-Lines",
    "Input Tokens",
    "Cached Input Tokens",
    "Output Tokens",
    "Reasoning Tokens",
    "Cost USD",
    "Duration ms",
}

WRAP_HEADERS = {
    "Task",
    "Trial",
    "Primary Review Labels",
    "Secondary Review Labels",
    "Primary Review Label",
    "Exclusions",
    "Operability Dimension",
    "Evidence",
}


@dataclass(frozen=True)
class HtmlRenderContext:
    output_path: Path | None
    repo_root: Path
    source_path: Path | None
    task_card_root: Path


@dataclass(frozen=True)
class RunContext:
    key: str
    suite: str
    agent_name: str
    model_name: str
    reasoning_effort: str
    summaries: list[TrialGroupSummary]
    results: list[OutcomeEvidence]

    @property
    def label(self) -> str:
        return (
            f"{self.suite} / {self.agent_name} / "
            f"{self.model_name} / {self.reasoning_effort}"
        )


def render_capability_evidence_digest_html(
    results: Iterable[OutcomeEvidence],
    selection_context: Mapping[str, object] | None = None,
    *,
    source_path: Path | str | None = None,
    output_path: Path | str | None = None,
    repo_root: Path | str | None = None,
    task_card_root: Path | str = "tasks",
) -> str:
    """Render the static HTML companion for a capability evidence digest."""

    result_list = list(results)
    render_context = HtmlRenderContext(
        output_path=Path(output_path) if output_path is not None else None,
        repo_root=Path(repo_root) if repo_root is not None else Path.cwd(),
        source_path=Path(source_path) if source_path is not None else None,
        task_card_root=Path(task_card_root),
    )
    run_contexts = _run_contexts(result_list)
    return _clean_html(
        _document(
            result_list,
            run_contexts,
            selection_context or {},
            render_context,
        )
    )


def _clean_html(document: str) -> str:
    return "\n".join(line.rstrip() for line in document.splitlines()) + "\n"


def _document(
    results: Sequence[OutcomeEvidence],
    contexts: Sequence[RunContext],
    selection_context: Mapping[str, object],
    render_context: HtmlRenderContext,
) -> str:
    first_context = contexts[0].key if contexts else ""
    context_tabs = "".join(
        (
            f'<button class="context-tab{" active" if index == 0 else ""}" '
            f'data-context="{_attr(context.key)}" type="button">'
            f"{_text(context.label)}</button>"
        )
        for index, context in enumerate(contexts)
    )
    pages = "".join(
        _context_page(context, index == 0, render_context)
        for index, context in enumerate(contexts)
    )
    if not pages:
        pages = '<main class="page"><p>No agent-trial results found.</p></main>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Capability Evidence Digest</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f3;
      --panel: #ffffff;
      --ink: #1c2227;
      --muted: #66707a;
      --line: #d8ddd5;
      --line-strong: #aeb8ae;
      --accent: #126b62;
      --accent-soft: #e8f3f1;
      --warn: #966300;
      --warn-soft: #fff6dc;
      --bad: #9e3c35;
      --bad-soft: #fff0ed;
      --good: #286f43;
      --good-soft: #edf8f0;
      --code: #f0f2ed;
      --shadow: 0 14px 42px rgba(24, 30, 35, 0.16);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-size: 14px;
      line-height: 1.42;
    }}
    button, input {{ font: inherit; }}
    a {{ color: var(--accent); text-underline-offset: 2px; }}
    code {{
      background: var(--code);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 1px 4px;
    }}
    .hero {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 22px 28px 18px;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 29px;
      line-height: 1.1;
      letter-spacing: 0;
    }}
    .hero p {{ margin: 0; max-width: 1120px; color: var(--muted); }}
    .global-facts {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }}
    .global-facts span {{
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fbfcfa;
      padding: 4px 8px;
      color: var(--muted);
      font-size: 12px;
    }}
    .context-tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 16px 0 0;
    }}
    .context-tab {{
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: #fbfcfa;
      color: var(--ink);
      padding: 7px 12px;
      cursor: pointer;
    }}
    .context-tab.active {{
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
    }}
    .context-page {{ display: none; }}
    .context-page.active {{ display: block; }}
    .page {{ padding: 22px 28px 90px; }}
    .context-facts, .score-grid, .resource-grid {{
      display: grid;
      gap: 10px;
    }}
    .context-facts {{
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      margin-bottom: 16px;
    }}
    .score-grid {{
      grid-template-columns: repeat(6, minmax(120px, 1fr));
      margin-bottom: 22px;
    }}
    .resource-grid {{ grid-template-columns: repeat(4, minmax(160px, 1fr)); }}
    .fact, .metric {{
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfcfa;
      padding: 10px;
    }}
    .fact span, .metric span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .fact strong, .metric strong {{
      display: block;
      margin-top: 4px;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }}
    .metric strong {{ font-size: 20px; }}
    .section {{
      margin: 0 0 22px;
      padding-top: 14px;
      border-top: 1px solid var(--line-strong);
    }}
    .section h2, .section h3 {{
      margin: 0 0 10px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    .section h2 {{ font-size: 20px; }}
    .section h3 {{ font-size: 15px; color: var(--muted); }}
    .section-note {{
      margin: -2px 0 10px;
      color: var(--muted);
      font-size: 12px;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr);
      gap: 14px;
    }}
    .lane {{
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      padding: 12px;
      min-width: 0;
    }}
    .lane h3 {{ color: var(--ink); font-size: 15px; }}
    .lane ul, .lane ol {{ margin: 8px 0 0; padding-left: 20px; }}
    .lane li {{ margin: 8px 0; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      margin: 0 4px 4px 0;
      padding: 2px 7px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fbfcfa;
      white-space: nowrap;
      font-size: 12px;
    }}
    .pill.good {{ color: var(--good); border-color: #9acba9; background: var(--good-soft); }}
    .pill.warn {{ color: var(--warn); border-color: #dfc27c; background: var(--warn-soft); }}
    .pill.bad {{ color: var(--bad); border-color: #e2aaa4; background: var(--bad-soft); }}
    .table-wrap {{
      overflow: auto;
      max-height: 72vh;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
    }}
    table {{
      width: 100%;
      min-width: 820px;
      border-collapse: separate;
      border-spacing: 0;
    }}
    th, td {{
      padding: 7px 9px;
      border-bottom: 1px solid var(--line);
      border-right: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 4;
      background: #edf0eb;
      color: #22272b;
      font-size: 12px;
      font-weight: 700;
    }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    td.wrap {{ white-space: normal; min-width: 260px; }}
    .sticky-task td:first-child,
    .sticky-task th:first-child {{
      position: sticky;
      left: 0;
      z-index: 5;
      background: #f8faf7;
      box-shadow: 1px 0 0 var(--line);
    }}
    .sticky-task th:first-child {{ z-index: 7; background: #e3e8e3; }}
    @media (max-width: 1050px) {{
      .context-facts, .score-grid, .resource-grid, .two-col {{
        grid-template-columns: 1fr 1fr;
      }}
    }}
    @media (max-width: 720px) {{
      .context-facts, .score-grid, .resource-grid, .two-col {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Capability Evidence Digest</h1>
    <p>{_text(INTRO_TEXT)}</p>
    {_global_facts(results, selection_context)}
    <nav class="context-tabs" aria-label="Run contexts">{context_tabs}</nav>
  </header>
  <div id="contexts" data-default-context="{_attr(first_context)}">
    {pages}
  </div>
  <script>
    (function () {{
      const pages = Array.from(document.querySelectorAll("[data-context-page]"));
      const tabs = Array.from(document.querySelectorAll("[data-context]"));
      const defaultContext = document.getElementById("contexts").dataset.defaultContext;
      function setContext(key, updateUrl) {{
        const selected = pages.some((page) => page.dataset.contextPage === key) ? key : defaultContext;
        pages.forEach((page) => page.classList.toggle("active", page.dataset.contextPage === selected));
        tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.context === selected));
        if (updateUrl && selected) {{
          const params = new URLSearchParams(window.location.search);
          params.set("context", selected);
          window.history.replaceState(null, "", window.location.pathname + "?" + params.toString());
        }}
      }}
      tabs.forEach((tab) => tab.addEventListener("click", () => setContext(tab.dataset.context, true)));
      const params = new URLSearchParams(window.location.search);
      setContext(params.get("context") || defaultContext, false);
    }})();
  </script>
</body>
</html>
"""


def _global_facts(
    results: Sequence[OutcomeEvidence],
    selection_context: Mapping[str, object],
) -> str:
    facts = [f"Agent trials: {len(results)}"]
    evidence_sets = selection_context.get("evidence_sets")
    if isinstance(evidence_sets, list):
        facts.append(f"Evidence sets: {len(evidence_sets)}")
        for evidence_set in evidence_sets:
            if isinstance(evidence_set, Mapping):
                facts.append(_evidence_set_fact(evidence_set))
    name = selection_context.get("name")
    if name:
        facts.append(f"Evidence set: {name}")
    selected_entries = selection_context.get("selected_entries")
    if selected_entries is not None:
        facts.append(f"Selected entries: {selected_entries}")
    selected_result_files = selection_context.get("selected_result_files")
    if selected_result_files is not None:
        facts.append(f"Selected result files: {selected_result_files}")
    return (
        '<div class="global-facts">'
        + "".join(f"<span>{_text(fact)}</span>" for fact in facts)
        + "</div>"
    )


def _evidence_set_fact(context: Mapping[str, object]) -> str:
    name = context.get("name") or "unknown"
    fact = f"Evidence set: {name}"
    selected_result_files = context.get("selected_result_files")
    if selected_result_files is not None:
        fact += f", selected result files: {selected_result_files}"
    source_path = context.get("source_path")
    if source_path:
        fact += f", source: {source_path}"
    snapshot_path = context.get("outcome_evidence_snapshot")
    if snapshot_path:
        fact += f", snapshot: {snapshot_path}"
    description = context.get("description")
    if description:
        fact += f", description: {description}"
    return fact


def _context_page(
    context: RunContext,
    active: bool,
    render_context: HtmlRenderContext,
) -> str:
    totals = _context_totals(context)
    active_class = " active" if active else ""
    source = _source_html(render_context)
    return f"""
  <main class="page context-page{active_class}" data-context-page="{_attr(context.key)}">
    <div class="context-facts">
      <div class="fact"><span>Suite</span><strong>{_text(context.suite)}</strong></div>
      <div class="fact"><span>Agent harness</span><strong>{_text(context.agent_name)}</strong></div>
      <div class="fact"><span>Model</span><strong>{_text(context.model_name)}</strong></div>
      <div class="fact"><span>Effort</span><strong>{_text(context.reasoning_effort)}</strong></div>
      <div class="fact"><span>Execution surface</span><strong>{_text(_surface_context_value(context.results, "execution_surface"))}</strong></div>
      <div class="fact"><span>Runtime version</span><strong>{_text(_surface_context_value(context.results, "runtime_version"))}</strong></div>
      <div class="fact"><span>Sandbox</span><strong>{_text(_surface_context_value(context.results, "sandbox_mode"))}</strong></div>
      <div class="fact"><span>Approval</span><strong>{_text(_surface_context_value(context.results, "approval_policy"))}</strong></div>
      <div class="fact"><span>Network</span><strong>{_text(_surface_context_value(context.results, "network_policy"))}</strong></div>
      <div class="fact"><span>Workspace history</span><strong>{_text(_surface_context_value(context.results, "workspace_history_policy"))}</strong></div>
      <div class="fact"><span>Workspace base ref</span><strong>{_text(_surface_context_value(context.results, "workspace_base_ref"))}</strong></div>
      <div class="fact"><span>Source</span><strong>{source}</strong></div>
    </div>
    <div class="score-grid">
      <div class="metric"><span>Tasks</span><strong>{len(context.summaries)}</strong></div>
      <div class="metric"><span>Fair trials</span><strong>{totals["fair"]}</strong></div>
      <div class="metric"><span>Grader passes</span><strong>{totals["passes"]}</strong></div>
      <div class="metric"><span>Accepted</span><strong>{totals["accepted"]}</strong></div>
      <div class="metric"><span>IO tokens</span><strong>{_format_optional_number(totals["io"])}</strong></div>
      <div class="metric"><span>IO / verified</span><strong>{_format_optional_number(totals["io_per_verified"])}</strong></div>
    </div>
    {_summary_section("Agent Harness Operability", _operability_rows(context), ["Operability Dimension", "Evidence"])}
    {_resource_summary(context)}
    {_reviewer_focus(context, render_context)}
    {_summary_section("Outcome Summary", _outcome_rows(context, render_context), ["Task", "Type", "Total", "Fair", "Excluded", "Passes", "Accepted", "Pass Rate", "pass@k", "pass^k"])}
    {_summary_section("Token Summary", _token_rows(context, render_context), ["Task", "Type", "IO Tokens", "Cached Tokens", "Reason Tokens", "IO Tok / Verified", "IO Tok / Accepted", "Cached Tok / Verified", "Reason Tok / Verified"])}
    {_summary_section("Review and Patch Summary", _review_rows(context, render_context), ["Task", "Type", "Median ms", "Median Files", "Median +Lines", "Median -Lines", "Primary Review Labels", "Secondary Review Labels", "Exclusions"], note=_review_patch_size_caveat_note(context))}
    {_summary_section("Trial Evidence", _trial_rows(context, render_context), ["Task", "Type", "Trial", "Grader Outcome", "Validity", "Primary Review Label", "Secondary Review Labels", "Exclusion", "Files", "+Lines", "-Lines", "Input Tokens", "Cached Input Tokens", "Output Tokens", "Reasoning Tokens", "Cost USD", "Duration ms", "Report", "Transcript", "Diff", "Result"], note=_patch_size_caveat_note(context.results))}
  </main>
"""


def _resource_summary(context: RunContext) -> str:
    totals = _context_totals(context)
    return f"""
    <section class="section">
      <h2>Overall Resource Summary</h2>
      <div class="resource-grid">
        <div class="metric"><span>Total IO tokens</span><strong>{_format_optional_number(totals["io"])}</strong></div>
        <div class="metric"><span>Total cached tokens</span><strong>{_format_optional_number(totals["cached"])}</strong></div>
        <div class="metric"><span>Total reasoning tokens</span><strong>{_format_optional_number(totals["reason"])}</strong></div>
        <div class="metric"><span>IO / accepted</span><strong>{_format_optional_number(totals["io_per_accepted"])}</strong></div>
        <div class="metric"><span>Cached / verified</span><strong>{_format_optional_number(totals["cached_per_verified"])}</strong></div>
        <div class="metric"><span>Reasoning / verified</span><strong>{_format_optional_number(totals["reason_per_verified"])}</strong></div>
      </div>
    </section>
"""


def _reviewer_focus(
    context: RunContext,
    render_context: HtmlRenderContext,
) -> str:
    attention_items = [
        (summary, _attention_for(summary))
        for summary in context.summaries
    ]
    attention_items = [
        (summary, issues)
        for summary, issues in attention_items
        if issues
    ]
    high_token_tasks = sorted(
        context.summaries,
        key=lambda summary: (
            summary.total_input_output_tokens is not None,
            summary.total_input_output_tokens or 0,
        ),
        reverse=True,
    )[:5]

    attention_html = "".join(
        (
            f"<li><strong>{_task_link(summary, render_context)}</strong><br>"
            f"{''.join(_pill(issue, 'warn') for issue in issues)}</li>"
        )
        for summary, issues in attention_items
    )
    if not attention_html:
        attention_html = "<li>No task-level caveats detected.</li>"
    high_html = "".join(
        (
            f"<li><strong>{_task_link(summary, render_context)}</strong><br>"
            f"{_format_optional_number(summary.total_input_output_tokens)} IO tokens</li>"
        )
        for summary in high_token_tasks
    )

    return f"""
    <section class="section">
      <h2>Reviewer Focus</h2>
      <div class="two-col">
        <div class="lane">
          <h3>Needs Attention</h3>
          <ul>{attention_html}</ul>
        </div>
        <div class="lane">
          <h3>Highest IO Token Tasks</h3>
          <ol>{high_html}</ol>
        </div>
      </div>
    </section>
"""


def _summary_section(
    heading: str,
    rows: Sequence[Mapping[str, str]],
    headers: Sequence[str],
    *,
    note: str = "",
) -> str:
    note_html = f'<p class="section-note">{_text(note)}</p>' if note else ""
    return f"""
    <section class="section">
      <h2>{_text(heading)}</h2>
      {note_html}
      {_table(headers, rows)}
    </section>
"""


def _table(headers: Sequence[str], rows: Sequence[Mapping[str, str]]) -> str:
    header_html = "".join(
        f'<th class="{"num" if header in NUMERIC_HEADERS else ""}">{_text(header)}</th>'
        for header in headers
    )
    body_html = "".join(
        "<tr>"
        + "".join(
            _td(header, row.get(header, ""))
            for header in headers
        )
        + "</tr>"
        for row in rows
    )
    return (
        '<div class="table-wrap sticky-task"><table><thead><tr>'
        + header_html
        + "</tr></thead><tbody>"
        + body_html
        + "</tbody></table></div>"
    )


def _td(header: str, value: str) -> str:
    classes = []
    if header in NUMERIC_HEADERS:
        classes.append("num")
    if header in WRAP_HEADERS:
        classes.append("wrap")
    class_attr = f' class="{" ".join(classes)}"' if classes else ""
    return f"<td{class_attr}>{value}</td>"


def _outcome_rows(
    context: RunContext,
    render_context: HtmlRenderContext,
) -> list[dict[str, str]]:
    return [
        {
            "Task": _task_link(summary, render_context),
            "Type": _text(summary.eval_type),
            "Total": _text(summary.total_trials),
            "Fair": _text(summary.trials),
            "Excluded": _text(summary.excluded_trials),
            "Passes": _text(summary.passes),
            "Accepted": _text(summary.accepted_results),
            "Pass Rate": _text(_format_rate(summary.pass_rate)),
            "pass@k": _text(_format_rate(summary.pass_at_k)),
            "pass^k": _text(_format_rate(summary.pass_caret_k)),
        }
        for summary in context.summaries
    ]


def _token_rows(
    context: RunContext,
    render_context: HtmlRenderContext,
) -> list[dict[str, str]]:
    return [
        {
            "Task": _task_link(summary, render_context),
            "Type": _text(summary.eval_type),
            "IO Tokens": _text(_format_optional_number(summary.total_input_output_tokens)),
            "Cached Tokens": _text(_format_optional_number(summary.total_cached_input_tokens)),
            "Reason Tokens": _text(_format_optional_number(summary.total_reasoning_output_tokens)),
            "IO Tok / Verified": _text(_format_optional_number(summary.input_output_tokens_per_verified_result)),
            "IO Tok / Accepted": _text(_format_optional_number(summary.input_output_tokens_per_accepted_result)),
            "Cached Tok / Verified": _text(_format_optional_number(summary.cached_input_tokens_per_verified_result)),
            "Reason Tok / Verified": _text(_format_optional_number(summary.reasoning_output_tokens_per_verified_result)),
        }
        for summary in context.summaries
    ]


def _review_rows(
    context: RunContext,
    render_context: HtmlRenderContext,
) -> list[dict[str, str]]:
    return [
        {
            "Task": _task_link(summary, render_context),
            "Type": _text(summary.eval_type),
            "Median ms": _text(summary.median_duration_ms),
            "Median Files": _text(_format_optional_number(summary.median_files_changed)),
            "Median +Lines": _text(
                _patch_stat(
                    _format_optional_number(summary.median_lines_added),
                    _summary_has_patch_size_caveat(summary, context.results),
                )
            ),
            "Median -Lines": _text(
                _patch_stat(
                    _format_optional_number(summary.median_lines_deleted),
                    _summary_has_patch_size_caveat(summary, context.results),
                )
            ),
            "Primary Review Labels": _text(_format_counts(summary.review_labels)),
            "Secondary Review Labels": _text(_format_counts(summary.secondary_review_labels)),
            "Exclusions": _text(_format_counts(summary.exclusion_reasons)),
        }
        for summary in context.summaries
    ]


def _operability_rows(context: RunContext) -> list[dict[str, str]]:
    return [
        {
            "Operability Dimension": _text(row.dimension),
            "Evidence": "<br>".join(
                _text(f"{label}: {value}")
                for label, value in row.facts
            ),
        }
        for row in agent_harness_operability_rows(context.results)
    ]


def _trial_rows(
    context: RunContext,
    render_context: HtmlRenderContext,
) -> list[dict[str, str]]:
    return [
        {
            "Task": _task_link_from_result(result, render_context),
            "Type": _text(result.eval_type),
            "Trial": _text(result.trial_id),
            "Grader Outcome": _text(result.status),
            "Validity": _text(result.trial_validity),
            "Primary Review Label": _text(result.primary_review_label),
            "Secondary Review Labels": _text(_format_labels(result.secondary_review_labels)),
            "Exclusion": _text(result.exclusion_reason_display),
            "Files": _text(result.files_changed_count),
            "+Lines": _text(
                _patch_stat(
                    result.lines_added,
                    bool(result.setup_created_untracked_changed_paths),
                )
            ),
            "-Lines": _text(
                _patch_stat(
                    result.lines_deleted,
                    bool(result.setup_created_untracked_changed_paths),
                )
            ),
            "Input Tokens": _text(_unknown_if_none(result.input_tokens)),
            "Cached Input Tokens": _text(_unknown_if_none(result.cached_input_tokens)),
            "Output Tokens": _text(_unknown_if_none(result.output_tokens)),
            "Reasoning Tokens": _text(_unknown_if_none(result.reasoning_output_tokens)),
            "Cost USD": _text(_unknown_if_none(result.cost_usd)),
            "Duration ms": _text(result.duration_ms),
            "Report": _path_link("report", result.report_path, render_context),
            "Transcript": _path_link("transcript", result.transcript_path, render_context),
            "Diff": _path_link("diff", result.diff_path, render_context),
            "Result": _path_link("result", result.result_path, render_context),
        }
        for result in context.results
    ]


def _patch_size_caveat_note(results: Sequence[OutcomeEvidence]) -> str:
    if not any(result.setup_created_untracked_changed_paths for result in results):
        return ""
    return (
        "Patch size metrics marked with * have setup-created untracked "
        "path caveats; changed-file counts/lists and boundary metrics "
        "include detected caveat paths, but line-count metrics may not "
        "fully represent those paths."
    )


def _review_patch_size_caveat_note(context: RunContext) -> str:
    if not any(
        _summary_has_patch_size_caveat(summary, context.results)
        for summary in context.summaries
    ):
        return ""
    return (
        "Patch size metrics marked with * have setup-created untracked "
        "path caveats; changed-file counts/lists and boundary metrics "
        "include detected caveat paths, but line-count metrics may not "
        "fully represent those paths."
    )


def _summary_has_patch_size_caveat(
    summary: TrialGroupSummary,
    results: Sequence[OutcomeEvidence],
) -> bool:
    return any(
        result.is_valid_trial
        and result.setup_created_untracked_changed_paths
        and result.eval_suite == summary.eval_suite
        and result.eval_type == summary.eval_type
        and result.task_id == summary.task_id
        and result.agent_name == summary.agent_name
        and result.model_name_display == summary.model_name_display
        and result.reasoning_effort_display == summary.reasoning_effort_display
        for result in results
    )


def _patch_stat(value: object, has_caveat: bool) -> str:
    suffix = "*" if has_caveat else ""
    return f"{value}{suffix}"


def _run_contexts(results: Sequence[OutcomeEvidence]) -> list[RunContext]:
    summaries = summarize_trials(results)
    summaries_by_key: dict[tuple[str, str, str, str], list[TrialGroupSummary]] = {}
    results_by_key: dict[tuple[str, str, str, str], list[OutcomeEvidence]] = {}
    for summary in summaries:
        summaries_by_key.setdefault(_summary_context_key(summary), []).append(summary)
    for result in results:
        results_by_key.setdefault(_result_context_key(result), []).append(result)

    used_keys: dict[str, int] = {}
    run_contexts: list[RunContext] = []
    for key in sorted(set(summaries_by_key) | set(results_by_key)):
        suite, agent_name, model_name, reasoning_effort = key
        slug = _unique_slug(_slug("-".join(key)), used_keys)
        context_summaries = sorted(
            summaries_by_key.get(key, []),
            key=lambda summary: (summary.eval_type, summary.task_id),
        )
        context_results = sorted(
            results_by_key.get(key, []),
            key=lambda result: (result.task_id, result.trial_id),
        )
        run_contexts.append(
            RunContext(
                key=slug,
                suite=suite or "unknown",
                agent_name=agent_name or "unknown",
                model_name=model_name or "unknown",
                reasoning_effort=reasoning_effort or "unknown",
                summaries=context_summaries,
                results=context_results,
            )
        )
    return run_contexts


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


def _surface_context_value(
    results: Sequence[OutcomeEvidence],
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


def _context_totals(context: RunContext) -> dict[str, object]:
    fair = sum(summary.trials for summary in context.summaries)
    passes = sum(summary.passes for summary in context.summaries)
    accepted = sum(summary.accepted_results for summary in context.summaries)
    io_tokens = _sum_required(
        summary.total_input_output_tokens
        for summary in context.summaries
    )
    cached_tokens = _sum_required(
        summary.total_cached_input_tokens
        for summary in context.summaries
    )
    reason_tokens = _sum_required(
        summary.total_reasoning_output_tokens
        for summary in context.summaries
    )
    return {
        "fair": fair,
        "passes": passes,
        "accepted": accepted,
        "io": io_tokens,
        "cached": cached_tokens,
        "reason": reason_tokens,
        "io_per_verified": _per_result(io_tokens, passes),
        "io_per_accepted": _per_result(io_tokens, accepted),
        "cached_per_verified": _per_result(cached_tokens, passes),
        "reason_per_verified": _per_result(reason_tokens, passes),
    }


def _attention_for(summary: TrialGroupSummary) -> list[str]:
    issues: list[str] = []
    if summary.passes != summary.trials:
        issues.append(f"{summary.passes}/{summary.trials} grader passes")
    if summary.accepted_results != summary.passes:
        issues.append(f"{summary.accepted_results}/{summary.passes} accepted results")

    labels = sorted(
        set(summary.review_labels)
        | set(summary.secondary_review_labels)
    )
    for label in labels:
        if label == "success_clean":
            continue
        primary_count = summary.review_labels.get(label, 0)
        secondary_count = summary.secondary_review_labels.get(label, 0)
        total = primary_count + secondary_count
        parts: list[str] = []
        if primary_count:
            parts.append(f"{primary_count} primary")
        if secondary_count:
            parts.append(f"{secondary_count} secondary")
        issues.append(
            f"{label} on {total}/{summary.trials or '?'} trials "
            f"({', '.join(parts)})"
        )

    if not summary.review_labels:
        issues.append("primary review labels missing")
    return issues


def _source_html(render_context: HtmlRenderContext) -> str:
    if render_context.source_path is None:
        return _text("not written")
    label = _display_path(render_context.source_path, render_context.repo_root)
    href = _href_for(render_context.source_path, render_context)
    return _link(label, href)


def _task_link(
    summary: TrialGroupSummary,
    render_context: HtmlRenderContext,
) -> str:
    return _task_link_for(
        summary.eval_suite,
        summary.task_id,
        render_context,
    )


def _task_link_from_result(
    result: OutcomeEvidence,
    render_context: HtmlRenderContext,
) -> str:
    return _task_link_for(
        result.eval_suite,
        result.task_id,
        render_context,
    )


def _task_link_for(
    eval_suite: str,
    task_id: str,
    render_context: HtmlRenderContext,
) -> str:
    if not task_id:
        return ""
    if not eval_suite:
        return _text(task_id)
    task_card = (
        render_context.task_card_root
        / eval_suite
        / task_id
        / "task-card.md"
    )
    return _link(task_id, _href_for(task_card, render_context))


def _path_link(
    label: str,
    path: object,
    render_context: HtmlRenderContext,
) -> str:
    if not path:
        return ""
    return _link(label, _href_for(Path(str(path)), render_context))


def _href_for(path: Path, render_context: HtmlRenderContext) -> str:
    target = _absolute_path(path, render_context.repo_root)
    if render_context.output_path is not None:
        output = _absolute_path(
            render_context.output_path,
            render_context.repo_root,
        )
        try:
            return Path(os.path.relpath(target, output.parent)).as_posix()
        except ValueError:
            pass
    if path.is_absolute():
        return path.as_posix()
    return path.as_posix()


def _display_path(path: Path, repo_root: Path) -> str:
    absolute = _absolute_path(path, repo_root)
    try:
        return absolute.relative_to(repo_root).as_posix()
    except ValueError:
        pass
    if path.is_absolute():
        return path.as_posix()
    return path.as_posix()


def _absolute_path(path: Path, repo_root: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _sum_required(values: Iterable[int | None]) -> int | None:
    total = 0
    for value in values:
        if value is None:
            return None
        total += value
    return total


def _per_result(total: int | None, results: int) -> float | None:
    if total is None or results == 0:
        return None
    return total / results


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


def _format_counts(counts: Mapping[str, int]) -> str:
    if not counts:
        return ""
    return ", ".join(f"{label}:{count}" for label, count in counts.items())


def _format_labels(labels: Sequence[str]) -> str:
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


def _pill(text: str, kind: str = "") -> str:
    return f'<span class="pill {kind}">{_text(text)}</span>'


def _link(label: str, href: str) -> str:
    return f'<a href="{_attr(href)}">{_text(label)}</a>'


def _text(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _attr(value: object) -> str:
    return _text(value)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "context"


def _unique_slug(slug: str, used_keys: dict[str, int]) -> str:
    used_keys[slug] = used_keys.get(slug, 0) + 1
    if used_keys[slug] == 1:
        return slug
    return f"{slug}-{used_keys[slug]}"
