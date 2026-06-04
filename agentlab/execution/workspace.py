from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

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


@dataclass(frozen=True)
class WorkspaceUntrackedBaseline:
    path: str
    digest: str


@dataclass(frozen=True)
class WorkspaceChangeBaseline:
    tree_ref: str
    untracked_files: tuple[WorkspaceUntrackedBaseline, ...] = field(
        default_factory=tuple
    )


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


def capture_change_baseline(workspace: Path) -> WorkspaceChangeBaseline:
    untracked_files = tuple(_snapshot_untracked_files(workspace))
    staged = run_git(["add", "-u", "--", "."], cwd=workspace)
    if staged.returncode != 0:
        raise RuntimeError(f"git add -u failed: {staged.stderr.strip()}")

    tree = run_git(["write-tree"], cwd=workspace)
    reset = run_git(["reset", "--mixed", "HEAD"], cwd=workspace)
    if reset.returncode != 0:
        raise RuntimeError(f"git reset failed: {reset.stderr.strip()}")
    if tree.returncode != 0:
        raise RuntimeError(f"git write-tree failed: {tree.stderr.strip()}")

    return WorkspaceChangeBaseline(
        tree_ref=tree.stdout.strip(),
        untracked_files=untracked_files,
    )


def capture_diff(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
) -> list[str]:
    diff_ref = base_ref or "HEAD"
    changed_baseline_untracked = _changed_baseline_untracked(
        workspace,
        baseline_untracked,
    )
    changed_baseline_paths = {entry.path for entry in changed_baseline_untracked}
    unchanged_baseline_paths = [
        entry.path
        for entry in baseline_untracked
        if entry.path not in changed_baseline_paths
    ]
    _mark_untracked_for_diff(workspace, exclude_untracked=unchanged_baseline_paths)
    diff_args = ["diff", "--binary", "--no-renames", diff_ref]
    name_args = ["diff", "--name-only", "-z", "--no-renames", diff_ref]

    git_env = isolated_git_env()
    diff = run_git(diff_args, cwd=workspace, env=git_env)
    if diff.returncode != 0:
        raise RuntimeError(f"git diff failed: {diff.stderr.strip()}")
    diff_path.write_text(diff.stdout, encoding="utf-8")

    changed = run_git(name_args, cwd=workspace, env=git_env)
    if changed.returncode != 0:
        raise RuntimeError(f"git diff --name-only failed: {changed.stderr.strip()}")
    return _append_missing_paths(
        [path for path in changed.stdout.split("\0") if path],
        [entry.path for entry in changed_baseline_untracked],
    )


def _mark_untracked_for_diff(
    workspace: Path,
    *,
    exclude_untracked: Sequence[str],
) -> None:
    excluded = tuple(exclude_untracked)
    paths = [
        path for path in _list_untracked(workspace)
        if not _is_excluded_untracked(path, excluded)
    ]
    if not paths:
        return
    marked = run_git(["add", "--intent-to-add", "--"] + paths, cwd=workspace)
    if marked.returncode != 0:
        raise RuntimeError(f"git add --intent-to-add failed: {marked.stderr.strip()}")


def _list_untracked(workspace: Path) -> list[str]:
    untracked = run_git(
        ["ls-files", "--others", "--exclude-standard", "-z"],
        cwd=workspace,
    )
    if untracked.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {untracked.stderr.strip()}")
    return [path for path in untracked.stdout.split("\0") if path]


def _snapshot_untracked_files(workspace: Path) -> list[WorkspaceUntrackedBaseline]:
    return [
        WorkspaceUntrackedBaseline(path=path, digest=digest)
        for path in _list_untracked(workspace)
        if (digest := _path_digest(workspace / path)) is not None
    ]


def _changed_baseline_untracked(
    workspace: Path,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline],
) -> list[WorkspaceUntrackedBaseline]:
    return [
        entry
        for entry in baseline_untracked
        if _path_digest(workspace / entry.path) != entry.digest
    ]


def _path_digest(path: Path) -> str | None:
    try:
        file_stat = path.lstat()
    except FileNotFoundError:
        return None

    mode = stat.S_IMODE(file_stat.st_mode)
    if stat.S_ISLNK(file_stat.st_mode):
        return f"symlink:{mode:o}:{os.readlink(path)}"
    if not stat.S_ISREG(file_stat.st_mode):
        return f"other:{mode:o}:{file_stat.st_size}:{file_stat.st_mtime_ns}"

    digest = hashlib.sha256()
    digest.update(f"file:{mode:o}:".encode("utf-8"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_excluded_untracked(path: str, excluded: Sequence[str]) -> bool:
    for candidate in excluded:
        if candidate.endswith("/"):
            if path.startswith(candidate):
                return True
        elif path == candidate:
            return True
    return False


def _append_missing_paths(paths: list[str], extra_paths: Sequence[str]) -> list[str]:
    seen = set(paths)
    for path in extra_paths:
        if path not in seen:
            paths.append(path)
            seen.add(path)
    return paths
