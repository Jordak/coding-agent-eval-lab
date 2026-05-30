from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Dict, Iterable, List, Tuple

from agentlab.outcome_evidence import OutcomeEvidence

ACCEPTED_PRIMARY_REVIEW_LABELS = {"success_clean"}


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
    accepted_results: int
    pass_rate: float
    pass_at_k: float
    pass_caret_k: float
    total_input_output_tokens: int | None
    total_cached_input_tokens: int | None
    total_reasoning_output_tokens: int | None
    input_output_tokens_per_verified_result: float | None
    input_output_tokens_per_accepted_result: float | None
    cached_input_tokens_per_verified_result: float | None
    reasoning_output_tokens_per_verified_result: float | None
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
    accepted_results = sum(
        1
        for result in valid_results
        if _accepted_result(result)
    )
    trials = len(valid_results)
    total_input_output_tokens = _sum_required(
        _input_output_tokens(result) for result in valid_results
    )
    total_cached_input_tokens = _sum_required(
        result.cached_input_tokens for result in valid_results
    )
    total_reasoning_output_tokens = _sum_required(
        result.reasoning_output_tokens for result in valid_results
    )
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
        accepted_results=accepted_results,
        pass_rate=pass_rate,
        pass_at_k=1.0 if passes > 0 else 0.0,
        pass_caret_k=1.0 if passes == trials and trials > 0 else 0.0,
        total_input_output_tokens=total_input_output_tokens,
        total_cached_input_tokens=total_cached_input_tokens,
        total_reasoning_output_tokens=total_reasoning_output_tokens,
        input_output_tokens_per_verified_result=_per_result(
            total_input_output_tokens,
            passes,
        ),
        input_output_tokens_per_accepted_result=_per_result(
            total_input_output_tokens,
            accepted_results,
        ),
        cached_input_tokens_per_verified_result=_per_result(
            total_cached_input_tokens,
            passes,
        ),
        reasoning_output_tokens_per_verified_result=_per_result(
            total_reasoning_output_tokens,
            passes,
        ),
        median_duration_ms=int(median(durations)) if durations else 0,
        median_files_changed=median(files_changed) if files_changed else 0.0,
        median_lines_added=median(lines_added) if lines_added else 0.0,
        median_lines_deleted=median(lines_deleted) if lines_deleted else 0.0,
        review_labels=dict(sorted(review_labels.items())),
        secondary_review_labels=dict(sorted(secondary_review_labels.items())),
        exclusion_reasons=dict(sorted(exclusion_reasons.items())),
    )


def _accepted_result(result: OutcomeEvidence) -> bool:
    return result.success and result.primary_review_label in (
        ACCEPTED_PRIMARY_REVIEW_LABELS
    )


def _input_output_tokens(result: OutcomeEvidence) -> int | None:
    input_tokens = result.input_tokens
    output_tokens = result.output_tokens
    if input_tokens is None or output_tokens is None:
        return None
    return input_tokens + output_tokens


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


def _display_unknown(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value)
    if not text:
        return "unknown"
    return text
