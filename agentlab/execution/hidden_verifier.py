from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from agentlab.execution.commands import isolated_git_env
from agentlab.execution.commands import run_commands
from agentlab.execution.commands import run_git
from agentlab.execution.scoring import CheckResult
from agentlab.tasks import EvalTask


@dataclass(frozen=True)
class HiddenVerifierResult:
    configured: bool = False
    patch: str | None = None
    checks: list[CheckResult] = field(default_factory=list)
    restore_notes: list[str] = field(default_factory=list)


def run_hidden_verifier(
    task: EvalTask,
    workspace: Path,
    env: Mapping[str, str],
) -> HiddenVerifierResult:
    verifier = task.hidden_verifier
    if verifier is None:
        return HiddenVerifierResult()
    if task.source_path is None:
        return HiddenVerifierResult(
            configured=True,
            patch=verifier.patch,
            checks=[
                CheckResult(
                    command=f"hidden verifier patch: {verifier.patch}",
                    returncode=1,
                    stderr="hidden verifier requires task.source_path",
                )
            ],
        )

    patch_path = task.source_path.parent / verifier.patch
    with _workspace_snapshot(workspace) as snapshot:
        checks: list[CheckResult] = []
        restore_notes: list[str] = []
        try:
            apply_check = _apply_hidden_patch(workspace, patch_path, verifier.patch)
            checks.append(apply_check)
            if apply_check.passed:
                checks.extend(run_commands(verifier.commands, workspace, env=env))
        finally:
            restore_notes.extend(snapshot.restore())
        if restore_notes:
            checks.append(
                CheckResult(
                    command="restore hidden verifier workspace",
                    returncode=1,
                    stderr="\n".join(restore_notes),
                )
            )

    return HiddenVerifierResult(
        configured=True,
        patch=verifier.patch,
        checks=checks,
        restore_notes=restore_notes,
    )


def _apply_hidden_patch(
    workspace: Path,
    patch_path: Path,
    display_path: str,
) -> CheckResult:
    completed = run_git(
        ["apply", str(patch_path.resolve())],
        cwd=workspace,
        env=isolated_git_env(),
    )
    return CheckResult(
        command=f"git apply hidden verifier patch: {display_path}",
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


class _WorkspaceSnapshot:
    def __init__(self, workspace: Path, snapshot: Path):
        self._workspace = workspace
        self._snapshot = snapshot

    def restore(self) -> list[str]:
        notes: list[str] = []
        try:
            _replace_worktree_contents(self._snapshot, self._workspace)
        except OSError as exc:
            notes.append(f"failed to restore hidden verifier worktree: {exc}")
        return notes


class _workspace_snapshot:
    def __init__(self, workspace: Path):
        self._workspace = workspace
        self._temp: tempfile.TemporaryDirectory[str] | None = None
        self._snapshot: _WorkspaceSnapshot | None = None

    def __enter__(self) -> _WorkspaceSnapshot:
        self._temp = tempfile.TemporaryDirectory(prefix="agentlab-hidden-verifier-")
        root = Path(self._temp.name)
        snapshot_path = root / "worktree"
        _copy_worktree_contents(self._workspace, snapshot_path)
        self._snapshot = _WorkspaceSnapshot(self._workspace, snapshot_path)
        return self._snapshot

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._temp is not None:
            self._temp.cleanup()


def _copy_worktree_contents(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, symlinks=True)
        else:
            shutil.copy2(child, target, follow_symlinks=False)


def _replace_worktree_contents(snapshot: Path, workspace: Path) -> None:
    for child in workspace.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    _copy_worktree_contents(snapshot, workspace)
