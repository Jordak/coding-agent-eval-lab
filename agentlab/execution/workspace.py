from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from agentlab.execution.changed_paths import CapturedDiff
from agentlab.execution.changed_paths import WorkspaceChangeBaseline
from agentlab.execution.changed_paths import WorkspaceIndexBaseline
from agentlab.execution.changed_paths import WorkspaceUntrackedBaseline
from agentlab.execution.changed_paths import capture_change_baseline
from agentlab.execution.changed_paths import capture_diff
from agentlab.execution.changed_paths import capture_diff_details
from agentlab.execution.changed_paths import capture_diff_details_preserving_index
from agentlab.execution.commands import clone_no_checkout
from agentlab.execution.synthetic_workspace import materialize_synthetic_base
from agentlab.tasks import EvalTask


__all__ = [
    "CapturedDiff",
    "PreparedWorkspace",
    "WorkspaceChangeBaseline",
    "WorkspaceIndexBaseline",
    "WorkspaceUntrackedBaseline",
    "capture_change_baseline",
    "capture_diff",
    "capture_diff_details",
    "capture_diff_details_preserving_index",
    "prepare_workspace",
]


WORKSPACE_HISTORY_POLICY = "base_only"


@dataclass(frozen=True)
class PreparedWorkspace:
    task: EvalTask
    path: Path
    workspace_history_policy: str
    workspace_base_ref: str


def prepare_workspace(task: EvalTask, root: Path) -> PreparedWorkspace:
    root = root.resolve()
    workspace = root / task.id
    workspace.parent.mkdir(parents=True, exist_ok=True)
    if workspace.exists():
        raise RuntimeError(f"workspace already exists: {workspace}")

    with tempfile.TemporaryDirectory(
        prefix=f"agentlab-prep-{_safe_name(task.id)}-"
    ) as prep_temp:
        prep_root = Path(prep_temp)
        prep_repo = prep_root / "repo"

        clone = clone_no_checkout(task.repo, prep_repo)
        if clone.returncode != 0:
            raise RuntimeError(f"git clone failed: {clone.stderr.strip()}")

        base_ref = materialize_synthetic_base(
            prep_repo,
            task.commit,
            workspace,
        )

    return PreparedWorkspace(
        task=task,
        path=workspace,
        workspace_history_policy=WORKSPACE_HISTORY_POLICY,
        workspace_base_ref=base_ref,
    )


def _safe_name(value: str) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in value)
    return safe.strip("-") or "task"
