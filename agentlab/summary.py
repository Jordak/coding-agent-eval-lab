from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List, Tuple

from agentlab.validity import exclusion_reason, trial_is_valid


@dataclass(frozen=True)
class TrialGroupSummary:
    eval_suite: str
    eval_type: str
    task_id: str
    agent_name: str
    model_name: str
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
    exclusion_reasons: Dict[str, int]


def summarize_trials(results: Iterable[Dict[str, Any]]) -> List[TrialGroupSummary]:
    groups: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for result in results:
        groups[_group_key(result)].append(result)

    summaries = [
        _summarize_group(key, grouped_results)
        for key, grouped_results in sorted(groups.items())
    ]
    return summaries


def _group_key(result: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    return (
        str(result.get("eval_suite", "")),
        str(result.get("eval_type", "")),
        str(result.get("task_id", "")),
        str(result.get("agent_name", "")),
        str(result.get("model_name") or ""),
    )


def _summarize_group(
    key: Tuple[str, str, str, str, str],
    results: List[Dict[str, Any]],
) -> TrialGroupSummary:
    valid_results = [result for result in results if trial_is_valid(result)]
    excluded_results = [result for result in results if not trial_is_valid(result)]
    passes = sum(1 for result in valid_results if bool(result.get("success")))
    trials = len(valid_results)
    durations = [int(result.get("duration_ms") or 0) for result in valid_results]
    files_changed = [
        len(result.get("files_changed") or [])
        for result in valid_results
    ]
    lines_added = [int(result.get("lines_added") or 0) for result in valid_results]
    lines_deleted = [int(result.get("lines_deleted") or 0) for result in valid_results]
    review_labels = Counter(
        label for result in valid_results for label in [_review_label(result)] if label
    )
    exclusion_reasons = Counter(
        reason
        for result in excluded_results
        for reason in [exclusion_reason(result) or "unknown"]
    )
    eval_suite, eval_type, task_id, agent_name, model_name = key
    pass_rate = passes / trials if trials else 0.0
    return TrialGroupSummary(
        eval_suite=eval_suite,
        eval_type=eval_type,
        task_id=task_id,
        agent_name=agent_name,
        model_name=model_name,
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
        exclusion_reasons=dict(sorted(exclusion_reasons.items())),
    )


def _review_label(result: Dict[str, Any]) -> str:
    review = result.get("review")
    if isinstance(review, dict):
        return str(review.get("primary_label", ""))
    return ""
