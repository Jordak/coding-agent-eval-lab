from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from agentlab.execution.commands import run_commands
from agentlab.execution.changed_paths import capture_change_baseline
from agentlab.execution.changed_paths import capture_diff_details_preserving_index
from agentlab.execution.hidden_verifier import HiddenVerifierResult
from agentlab.execution.hidden_verifier import run_hidden_verifier
from agentlab.tasks.environment import build_task_environment
from agentlab.runtime.patches import count_patch_lines
from agentlab.execution.scoring import CheckResult
from agentlab.execution.scoring import Score
from agentlab.execution.scoring import calculate_grader_outcome
from agentlab.tasks import EvalTask
from agentlab.execution.workspace import prepare_workspace


TaskAction = Callable[[Path, Mapping[str, str]], "TaskActionResult"]
DiffPathResolver = Callable[[Path], Path]


@dataclass(frozen=True)
class TaskActionResult:
    checks: list[CheckResult] = field(default_factory=list)
    agent_error: str | None = None


@dataclass(frozen=True)
class TaskExecution:
    task: EvalTask
    workspace: Path
    score: Score
    setup_checks: list[CheckResult] = field(default_factory=list)
    baseline_checks: list[CheckResult] = field(default_factory=list)
    action_checks: list[CheckResult] = field(default_factory=list)
    target_checks: list[CheckResult] = field(default_factory=list)
    hidden_verifier: HiddenVerifierResult = field(
        default_factory=HiddenVerifierResult
    )
    files_changed: list[str] = field(default_factory=list)
    lines_added: int = 0
    lines_deleted: int = 0
    setup_created_untracked_changed_paths: list[str] = field(default_factory=list)
    setup_created_untracked_coverage_caveat_count: int = 0
    diff_path: Path = Path("diff.patch")
    workspace_history_policy: str = "unknown"
    workspace_base_ref: str = "unknown"

    @property
    def all_checks(self) -> list[CheckResult]:
        return (
            self.setup_checks
            + self.baseline_checks
            + self.action_checks
            + self.target_checks
        )


def execute_task_phases(
    task: EvalTask,
    workspace_root: Path,
    action: TaskAction,
    diff_path: Path | DiffPathResolver,
    *,
    diff_base_ref: str | None = None,
) -> TaskExecution:
    prepared = prepare_workspace(task, workspace_root)
    task_env = build_task_environment(task, prepared.path)
    setup_checks = run_commands(task.setup, prepared.path, env=task_env)
    baseline_checks = run_commands(task.baseline, prepared.path, env=task_env)
    change_baseline = capture_change_baseline(
        prepared.path,
        exact_untracked_patterns=_boundary_untracked_patterns(task),
    )

    action_result = action(prepared.path, task_env)

    resolved_diff_path = _resolve_diff_path(diff_path, prepared.path)
    captured_diff = capture_diff_details_preserving_index(
        prepared.path,
        resolved_diff_path,
        base_ref=diff_base_ref or change_baseline.tree_ref,
        baseline_untracked=change_baseline.untracked_files,
        baseline_reset_index=change_baseline.reset_index_entries,
    )
    patch_stats = count_patch_lines(
        resolved_diff_path.read_text(encoding="utf-8")
    )
    hidden_verifier = run_hidden_verifier(task, prepared.path, task_env)
    target_checks = (
        []
        if hidden_verifier.restore_notes
        else run_commands(task.test, prepared.path, env=task_env)
    )
    all_checks = (
        setup_checks
        + baseline_checks
        + action_result.checks
        + target_checks
    )
    score = calculate_grader_outcome(
        task,
        all_checks,
        captured_diff.files_changed,
        agent_error=action_result.agent_error,
        hidden_checks=hidden_verifier.checks,
    )
    return TaskExecution(
        task=task,
        workspace=prepared.path,
        score=score,
        setup_checks=setup_checks,
        baseline_checks=baseline_checks,
        action_checks=action_result.checks,
        target_checks=target_checks,
        hidden_verifier=hidden_verifier,
        files_changed=captured_diff.files_changed,
        lines_added=patch_stats.lines_added,
        lines_deleted=patch_stats.lines_deleted,
        setup_created_untracked_changed_paths=(
            captured_diff.setup_created_untracked_changed_paths
        ),
        setup_created_untracked_coverage_caveat_count=(
            captured_diff.setup_created_untracked_coverage_caveat_count
        ),
        diff_path=resolved_diff_path,
        workspace_history_policy=prepared.workspace_history_policy,
        workspace_base_ref=prepared.workspace_base_ref,
    )


def _resolve_diff_path(
    diff_path: Path | DiffPathResolver,
    workspace: Path,
) -> Path:
    if isinstance(diff_path, Path):
        return diff_path
    return diff_path(workspace)


def _boundary_untracked_patterns(task: EvalTask) -> list[str]:
    patterns = list(task.success.forbidden_paths)
    if task.success.allowed_paths is not None:
        patterns.extend(task.success.allowed_paths)
    return patterns
