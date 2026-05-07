from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class TrialGroupSummary:
    eval_suite: str
    eval_type: str
    task_id: str
    agent_name: str
    model_name: str
    trials: int
    passes: int
    pass_rate: float
    pass_at_k: float
    pass_caret_k: float
    median_duration_ms: int
    median_files_changed: float
    review_labels: Dict[str, int]


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
    passes = sum(1 for result in results if bool(result.get("success")))
    trials = len(results)
    durations = [int(result.get("duration_ms") or 0) for result in results]
    files_changed = [
        len(result.get("files_changed") or [])
        for result in results
    ]
    review_labels = Counter(
        label for result in results for label in [_review_label(result)] if label
    )
    eval_suite, eval_type, task_id, agent_name, model_name = key
    pass_rate = passes / trials if trials else 0.0
    return TrialGroupSummary(
        eval_suite=eval_suite,
        eval_type=eval_type,
        task_id=task_id,
        agent_name=agent_name,
        model_name=model_name,
        trials=trials,
        passes=passes,
        pass_rate=pass_rate,
        pass_at_k=1.0 if passes > 0 else 0.0,
        pass_caret_k=1.0 if passes == trials and trials > 0 else 0.0,
        median_duration_ms=int(median(durations)) if durations else 0,
        median_files_changed=median(files_changed) if files_changed else 0.0,
        review_labels=dict(sorted(review_labels.items())),
    )


def _review_label(result: Dict[str, Any]) -> str:
    review = result.get("review")
    if isinstance(review, dict):
        return str(review.get("primary_label", ""))
    return ""
