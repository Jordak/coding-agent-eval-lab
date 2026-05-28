from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Dict, Iterable, List, Tuple

from agentlab.outcome_evidence import OutcomeEvidence


@dataclass(frozen=True)
class TrialGroupSummary:
    eval_suite: str
    eval_type: str
    task_id: str
    agent_name: str
    model_name: str
    reasoning_effort: str
    total_trials: int
    trials: int
    excluded_trials: int
    passes: int
    pass_rate: float
    pass_at_k: float
    pass_caret_k: float
    median_duration_ms: int
    median_files_changed: float
    median_lines_added: float
    median_lines_deleted: float
    review_labels: Dict[str, int]
    secondary_review_labels: Dict[str, int]
    exclusion_reasons: Dict[str, int]

    @property
    def model_name_display(self) -> str:
        return _display_unknown(self.model_name)

    @property
    def reasoning_effort_display(self) -> str:
        return _display_unknown(self.reasoning_effort)


def summarize_trials(
    results: Iterable[OutcomeEvidence],
) -> List[TrialGroupSummary]:
    groups: Dict[
        Tuple[str, str, str, str, str, str],
        List[OutcomeEvidence],
    ] = defaultdict(list)
    for result in results:
        groups[_group_key(result)].append(result)

    summaries = [
        _summarize_group(key, grouped_results)
        for key, grouped_results in sorted(groups.items())
    ]
    return summaries


def _group_key(result: OutcomeEvidence) -> Tuple[str, str, str, str, str, str]:
    return (
        result.eval_suite,
        result.eval_type,
        result.task_id,
        result.agent_name,
        result.model_name or "",
        result.reasoning_effort,
    )


def _summarize_group(
    key: Tuple[str, str, str, str, str, str],
    results: List[OutcomeEvidence],
) -> TrialGroupSummary:
    valid_results = [result for result in results if result.is_valid_trial]
    excluded_results = [result for result in results if not result.is_valid_trial]
    passes = sum(1 for result in valid_results if result.success)
    trials = len(valid_results)
    durations = [result.duration_ms for result in valid_results]
    files_changed = [result.files_changed_count for result in valid_results]
    lines_added = [result.lines_added for result in valid_results]
    lines_deleted = [result.lines_deleted for result in valid_results]
    review_labels = Counter(
        label
        for result in valid_results
        for label in [result.primary_review_label]
        if label
    )
    secondary_review_labels = Counter(
        label
        for result in valid_results
        for label in result.secondary_review_labels
    )
    exclusion_reasons = Counter(
        reason
        for result in excluded_results
        for reason in [result.exclusion_reason_display or "unknown"]
    )
    eval_suite, eval_type, task_id, agent_name, model_name, reasoning_effort = key
    pass_rate = passes / trials if trials else 0.0
    return TrialGroupSummary(
        eval_suite=eval_suite,
        eval_type=eval_type,
        task_id=task_id,
        agent_name=agent_name,
        model_name=model_name,
        reasoning_effort=reasoning_effort,
        total_trials=len(results),
        trials=trials,
        excluded_trials=len(excluded_results),
        passes=passes,
        pass_rate=pass_rate,
        pass_at_k=1.0 if passes > 0 else 0.0,
        pass_caret_k=1.0 if passes == trials and trials > 0 else 0.0,
        median_duration_ms=int(median(durations)) if durations else 0,
        median_files_changed=median(files_changed) if files_changed else 0.0,
        median_lines_added=median(lines_added) if lines_added else 0.0,
        median_lines_deleted=median(lines_deleted) if lines_deleted else 0.0,
        review_labels=dict(sorted(review_labels.items())),
        secondary_review_labels=dict(sorted(secondary_review_labels.items())),
        exclusion_reasons=dict(sorted(exclusion_reasons.items())),
    )


def _display_unknown(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value)
    if not text:
        return "unknown"
    return text
