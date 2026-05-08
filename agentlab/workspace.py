from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentlab.commands import run_git
from agentlab.tasks import EvalTask


@dataclass(frozen=True)
class PreparedWorkspace:
    task: EvalTask
    path: Path


def prepare_workspace(task: EvalTask, root: Path) -> PreparedWorkspace:
    root = root.resolve()
    workspace = root / task.id
    workspace.parent.mkdir(parents=True, exist_ok=True)
    if workspace.exists():
        raise RuntimeError(f"workspace already exists: {workspace}")

    clone = run_git(["clone", task.repo, workspace.name], cwd=workspace.parent)
    if clone.returncode != 0:
        raise RuntimeError(f"git clone failed: {clone.stderr.strip()}")

    checkout = run_git(["checkout", task.commit], cwd=workspace)
    if checkout.returncode != 0:
        raise RuntimeError(f"git checkout failed: {checkout.stderr.strip()}")

    return PreparedWorkspace(task=task, path=workspace)


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

    diff = run_git(diff_args, cwd=workspace)
    if diff.returncode != 0:
        raise RuntimeError(f"git diff failed: {diff.stderr.strip()}")
    diff_path.write_text(diff.stdout, encoding="utf-8")

    changed = run_git(name_args, cwd=workspace)
    if changed.returncode != 0:
        raise RuntimeError(f"git diff --name-only failed: {changed.stderr.strip()}")
    return [line for line in changed.stdout.splitlines() if line.strip()]
