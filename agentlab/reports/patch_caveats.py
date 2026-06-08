from typing import Sequence

from agentlab.evidence.outcome import OutcomeEvidence
from agentlab.evidence.summary import TrialGroupSummary


def patch_size_caveat_note(
    *,
    marker: str,
    path_phrase: str = "those paths",
) -> str:
    return (
        f"Patch size metrics marked with {marker} have setup-created "
        "untracked path caveats; changed-file counts/lists and boundary "
        "metrics include detected caveat paths, but line-count metrics may "
        "include setup-created baseline content or otherwise not fully "
        f"represent {path_phrase}."
    )


def setup_created_untracked_coverage_caveat_note(*, count: int) -> str:
    plural = "" if count == 1 else "s"
    return (
        "Setup-created untracked coverage caveat: "
        f"{count} setup-created untracked path{plural} existed outside exact "
        "boundary-pattern matching. Changed-file counts/lists and boundary "
        "metrics include detected changes, but detection remains best-effort "
        "for worktree-only content-preserving edits to those paths."
    )


def has_patch_size_caveats(results: Sequence[OutcomeEvidence]) -> bool:
    return any(result.setup_created_untracked_changed_paths for result in results)


def setup_created_untracked_coverage_caveat_count(
    results: Sequence[OutcomeEvidence],
) -> int:
    return sum(
        result.setup_created_untracked_coverage_caveat_count
        for result in results
    )


def has_summary_patch_size_caveats(
    summaries: Sequence[TrialGroupSummary],
    results: Sequence[OutcomeEvidence],
) -> bool:
    return any(
        summary_has_patch_size_caveat(summary, results)
        for summary in summaries
    )


def summary_has_patch_size_caveat(
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


def patch_stat(value: object, has_caveat: bool) -> str:
    suffix = "*" if has_caveat else ""
    return f"{value}{suffix}"
