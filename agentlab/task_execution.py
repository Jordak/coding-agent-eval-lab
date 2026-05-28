from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from agentlab.commands import run_commands
from agentlab.environment import build_task_environment
from agentlab.patches import count_patch_lines
from agentlab.scoring import CheckResult
from agentlab.scoring import Score
from agentlab.scoring import calculate_grader_outcome
from agentlab.tasks import EvalTask
from agentlab.workspace import capture_diff
from agentlab.workspace import prepare_workspace


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
    files_changed: list[str] = field(default_factory=list)
    lines_added: int = 0
    lines_deleted: int = 0
    diff_path: Path = Path("diff.patch")

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

    action_result = action(prepared.path, task_env)
    target_checks = run_commands(task.test, prepared.path, env=task_env)

    resolved_diff_path = _resolve_diff_path(diff_path, prepared.path)
    files_changed = capture_diff(
        prepared.path,
        resolved_diff_path,
        base_ref=diff_base_ref,
    )
    patch_stats = count_patch_lines(
        resolved_diff_path.read_text(encoding="utf-8")
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
        files_changed,
        agent_error=action_result.agent_error,
    )
    return TaskExecution(
        task=task,
        workspace=prepared.path,
        score=score,
        setup_checks=setup_checks,
        baseline_checks=baseline_checks,
        action_checks=action_result.checks,
        target_checks=target_checks,
        files_changed=files_changed,
        lines_added=patch_stats.lines_added,
        lines_deleted=patch_stats.lines_deleted,
        diff_path=resolved_diff_path,
    )


def _resolve_diff_path(
    diff_path: Path | DiffPathResolver,
    workspace: Path,
) -> Path:
    if isinstance(diff_path, Path):
        return diff_path
    return diff_path(workspace)
