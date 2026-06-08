from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from agentlab.execution.commands import (
    clone_no_checkout,
    isolated_git_env,
    run_git,
)
from agentlab.execution.synthetic_workspace import materialize_synthetic_base
from agentlab.tasks import EvalTask


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


def capture_diff(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
) -> list[str]:
    diff_args = ["diff", "--binary"]
    name_args = ["diff", "--name-only"]
    if base_ref is not None:
        diff_args.append(base_ref)
        name_args.append(base_ref)

    git_env = isolated_git_env()
    diff = run_git(diff_args, cwd=workspace, env=git_env)
    if diff.returncode != 0:
        raise RuntimeError(f"git diff failed: {diff.stderr.strip()}")
    diff_path.write_text(diff.stdout, encoding="utf-8")

    changed = run_git(name_args, cwd=workspace, env=git_env)
    if changed.returncode != 0:
        raise RuntimeError(f"git diff --name-only failed: {changed.stderr.strip()}")
    return [line for line in changed.stdout.splitlines() if line.strip()]
