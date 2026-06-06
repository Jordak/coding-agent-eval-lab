from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Mapping, Sequence

from agentlab.execution.commands import (
    clone_no_checkout,
    isolated_git_env,
    run_git,
)
from agentlab.execution.synthetic_workspace import materialize_synthetic_base
from agentlab.tasks import EvalTask
from agentlab.tasks.boundaries import path_matches_boundary_glob


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
    fingerprint: str


@dataclass(frozen=True)
class WorkspaceIndexBaseline:
    path: str
    index_signature: str | None


@dataclass(frozen=True)
class WorkspaceChangeBaseline:
    tree_ref: str
    untracked_files: tuple[WorkspaceUntrackedBaseline, ...] = field(
        default_factory=tuple
    )
    setup_index_entries: tuple[WorkspaceIndexBaseline, ...] = field(
        default_factory=tuple
    )
    reset_index_entries: tuple[WorkspaceIndexBaseline, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class CapturedDiff:
    files_changed: list[str]
    setup_created_untracked_changed_paths: list[str] = field(default_factory=list)


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


def capture_change_baseline(
    workspace: Path,
    *,
    exact_untracked_patterns: Sequence[str] = (),
) -> WorkspaceChangeBaseline:
    setup_index_entries = tuple(_setup_index_entries(workspace))

    with tempfile.TemporaryDirectory(prefix="agentlab-index-") as temp:
        index_env = {"GIT_INDEX_FILE": str(Path(temp) / "index")}
        reset_existing_index = run_git(
            ["read-tree", "--reset", "HEAD"],
            cwd=workspace,
            env=index_env,
        )
        if reset_existing_index.returncode != 0:
            raise RuntimeError(
                f"git read-tree failed: {reset_existing_index.stderr.strip()}"
            )

        staged = run_git(["add", "-u", "--", "."], cwd=workspace, env=index_env)
        if staged.returncode != 0:
            raise RuntimeError(f"git add -u failed: {staged.stderr.strip()}")

        tree = run_git(["write-tree"], cwd=workspace, env=index_env)
        if tree.returncode != 0:
            raise RuntimeError(f"git write-tree failed: {tree.stderr.strip()}")
        tree_ref = tree.stdout.strip()

        reset = run_git(
            ["read-tree", "--reset", "HEAD"],
            cwd=workspace,
            env=index_env,
        )
        if reset.returncode != 0:
            raise RuntimeError(f"git read-tree failed: {reset.stderr.strip()}")

        reset_index_entries = tuple(
            _reset_index_entries(workspace, tree_ref, env=index_env)
        )
        untracked_files = tuple(
            _snapshot_untracked_files(
                workspace,
                env=index_env,
                exact_patterns=exact_untracked_patterns,
            )
        )

    return WorkspaceChangeBaseline(
        tree_ref=tree_ref,
        untracked_files=untracked_files,
        setup_index_entries=setup_index_entries,
        reset_index_entries=reset_index_entries,
    )


def capture_diff(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_setup_index: Sequence[WorkspaceIndexBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
) -> list[str]:
    return capture_diff_details_preserving_index(
        workspace,
        diff_path,
        base_ref=base_ref,
        baseline_untracked=baseline_untracked,
        baseline_setup_index=baseline_setup_index,
        baseline_reset_index=baseline_reset_index,
    ).files_changed


def capture_diff_details_preserving_index(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_setup_index: Sequence[WorkspaceIndexBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
) -> CapturedDiff:
    with _preserve_git_index(workspace):
        return capture_diff_details(
            workspace,
            diff_path,
            base_ref=base_ref,
            baseline_untracked=baseline_untracked,
            baseline_setup_index=baseline_setup_index,
            baseline_reset_index=baseline_reset_index,
        )


def capture_diff_details(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_setup_index: Sequence[WorkspaceIndexBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
) -> CapturedDiff:
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
    name_args = ["diff", "--name-only", "-z", "--no-renames", diff_ref]
    cached_name_args = [
        "diff",
        "--cached",
        "--name-only",
        "-z",
        "--no-renames",
        diff_ref,
    ]

    git_env = isolated_git_env()
    worktree_paths = _diff_names(
        workspace,
        name_args,
        "git diff --name-only",
        env=git_env,
    )
    worktree_paths = _filter_unchanged_setup_index_paths(
        workspace,
        worktree_paths,
        unchanged_baseline_paths,
        baseline_setup_index,
    )
    cached_paths = _diff_names(
        workspace,
        cached_name_args,
        "git diff --cached --name-only",
        env=git_env,
    )
    cached_paths = _filter_unchanged_setup_index_paths(
        workspace,
        cached_paths,
        unchanged_baseline_paths,
        baseline_setup_index,
    )
    worktree_paths = _filter_unchanged_baseline_untracked_paths(
        workspace,
        worktree_paths,
        unchanged_baseline_paths,
    )
    cached_paths = _filter_unchanged_baseline_untracked_paths(
        workspace,
        cached_paths,
        unchanged_baseline_paths,
    )
    cached_paths = _filter_reset_baseline_cached_paths(
        workspace,
        cached_paths,
        worktree_paths,
        baseline_reset_index,
    )
    worktree_path_set = set(worktree_paths)
    cached_only_paths = [
        path for path in cached_paths if path not in worktree_path_set
    ]
    diff_path.write_text(
        _join_diffs(
            _worktree_diff_for_paths(
                workspace,
                diff_ref,
                worktree_paths,
                env=git_env,
            ),
            _cached_diff_for_paths(
                workspace,
                diff_ref,
                cached_only_paths,
                env=git_env,
            ),
        ),
        encoding="utf-8",
    )

    changed_paths = _append_missing_paths(worktree_paths, cached_paths)
    files_changed = _append_missing_paths(
        changed_paths,
        [entry.path for entry in changed_baseline_untracked],
    )
    return CapturedDiff(
        files_changed=files_changed,
        setup_created_untracked_changed_paths=[
            entry.path for entry in changed_baseline_untracked
        ],
    )


@contextmanager
def _preserve_git_index(workspace: Path) -> Iterator[None]:
    index_path = _git_index_path(workspace)
    with tempfile.TemporaryDirectory(prefix="agentlab-index-backup-") as temp:
        backup_path = Path(temp) / "index"
        index_existed = index_path.exists()
        if index_existed:
            shutil.copy2(index_path, backup_path)

        try:
            yield
        finally:
            if index_existed:
                index_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, index_path)
            else:
                try:
                    index_path.unlink()
                except FileNotFoundError:
                    pass


def _git_index_path(workspace: Path) -> Path:
    index = run_git(["rev-parse", "--git-path", "index"], cwd=workspace)
    if index.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {index.stderr.strip()}")
    index_path = Path(index.stdout.strip())
    if index_path.is_absolute():
        return index_path
    return workspace / index_path


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
    marked = run_git(
        ["add", "--intent-to-add", "--force", "--"] + paths,
        cwd=workspace,
    )
    if marked.returncode != 0:
        raise RuntimeError(f"git add --intent-to-add failed: {marked.stderr.strip()}")


def _list_untracked(
    workspace: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> list[str]:
    untracked = run_git(
        ["ls-files", "--others", "-z"],
        cwd=workspace,
        env=env,
    )
    if untracked.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {untracked.stderr.strip()}")
    return [path for path in untracked.stdout.split("\0") if path]


def _diff_names(
    workspace: Path,
    args: list[str],
    command_name: str,
    *,
    env: Mapping[str, str] | None = None,
) -> list[str]:
    changed = run_git(args, cwd=workspace, env=env)
    if changed.returncode != 0:
        raise RuntimeError(f"{command_name} failed: {changed.stderr.strip()}")
    return [path for path in changed.stdout.split("\0") if path]


def _setup_index_entries(workspace: Path) -> list[WorkspaceIndexBaseline]:
    paths = _diff_names(
        workspace,
        ["diff", "--cached", "--name-only", "-z", "--no-renames", "HEAD"],
        "git diff --cached --name-only",
    )
    return [
        WorkspaceIndexBaseline(
            path=path,
            index_signature=_index_entry_signature(workspace, path),
        )
        for path in paths
    ]


def _reset_index_entries(
    workspace: Path,
    tree_ref: str,
    *,
    env: Mapping[str, str] | None = None,
) -> list[WorkspaceIndexBaseline]:
    paths = _diff_names(
        workspace,
        ["diff", "--cached", "--name-only", "-z", "--no-renames", tree_ref],
        "git diff --cached --name-only",
        env=env,
    )
    return [
        WorkspaceIndexBaseline(
            path=path,
            index_signature=_index_entry_signature(workspace, path, env=env),
        )
        for path in paths
    ]


def _filter_reset_baseline_cached_paths(
    workspace: Path,
    cached_paths: Sequence[str],
    worktree_paths: Sequence[str],
    baseline_reset_index: Sequence[WorkspaceIndexBaseline],
) -> list[str]:
    if not baseline_reset_index:
        return list(cached_paths)

    worktree_path_set = set(worktree_paths)
    reset_signatures = {
        entry.path: entry.index_signature for entry in baseline_reset_index
    }
    filtered: list[str] = []
    for path in cached_paths:
        if path in worktree_path_set or path not in reset_signatures:
            filtered.append(path)
            continue
        if _index_entry_signature(workspace, path) != reset_signatures[path]:
            filtered.append(path)
    return filtered


def _filter_unchanged_setup_index_paths(
    workspace: Path,
    paths: Sequence[str],
    unchanged_baseline_paths: Sequence[str],
    baseline_setup_index: Sequence[WorkspaceIndexBaseline],
) -> list[str]:
    if not baseline_setup_index or not unchanged_baseline_paths:
        return list(paths)

    unchanged_path_set = set(unchanged_baseline_paths)
    setup_signatures = {
        entry.path: entry.index_signature for entry in baseline_setup_index
    }
    filtered: list[str] = []
    for path in paths:
        if path not in unchanged_path_set or path not in setup_signatures:
            filtered.append(path)
            continue
        if _index_entry_signature(workspace, path) != setup_signatures[path]:
            filtered.append(path)
    return filtered


def _filter_unchanged_baseline_untracked_paths(
    workspace: Path,
    paths: Sequence[str],
    unchanged_baseline_paths: Sequence[str],
) -> list[str]:
    if not unchanged_baseline_paths:
        return list(paths)

    unchanged_path_set = set(unchanged_baseline_paths)
    filtered: list[str] = []
    for path in paths:
        if path not in unchanged_path_set or not _index_matches_worktree(
            workspace,
            path,
        ):
            filtered.append(path)
    return filtered


def _index_entry_signature(
    workspace: Path,
    path: str,
    *,
    env: Mapping[str, str] | None = None,
) -> str | None:
    entry = run_git(["ls-files", "--stage", "-z", "--", path], cwd=workspace, env=env)
    if entry.returncode != 0:
        raise RuntimeError(f"git ls-files --stage failed: {entry.stderr.strip()}")
    entries = [part for part in entry.stdout.split("\0") if part]
    if not entries:
        return None
    return "\0".join(part.split("\t", 1)[0] for part in entries)


def _index_matches_worktree(workspace: Path, path: str) -> bool:
    diff = run_git(["diff", "--quiet", "--", path], cwd=workspace)
    if diff.returncode == 0:
        return True
    if diff.returncode == 1:
        return False
    raise RuntimeError(f"git diff --quiet failed: {diff.stderr.strip()}")


def _cached_diff_for_paths(
    workspace: Path,
    diff_ref: str,
    paths: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> str:
    if not paths:
        return ""
    cached_diff = run_git(
        ["diff", "--binary", "--no-renames", "--cached", diff_ref, "--"]
        + list(paths),
        cwd=workspace,
        env=env,
    )
    if cached_diff.returncode != 0:
        raise RuntimeError(f"git diff --cached failed: {cached_diff.stderr.strip()}")
    return cached_diff.stdout


def _worktree_diff_for_paths(
    workspace: Path,
    diff_ref: str,
    paths: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> str:
    if not paths:
        return ""
    diff = run_git(
        ["diff", "--binary", "--no-renames", diff_ref, "--"] + list(paths),
        cwd=workspace,
        env=env,
    )
    if diff.returncode != 0:
        raise RuntimeError(f"git diff failed: {diff.stderr.strip()}")
    return diff.stdout


def _join_diffs(*diffs: str) -> str:
    chunks = [diff for diff in diffs if diff]
    if not chunks:
        return ""
    return "\n".join(diff.rstrip("\n") for diff in chunks) + "\n"


def _snapshot_untracked_files(
    workspace: Path,
    *,
    env: Mapping[str, str] | None = None,
    exact_patterns: Sequence[str] = (),
) -> list[WorkspaceUntrackedBaseline]:
    return [
        WorkspaceUntrackedBaseline(path=path, fingerprint=fingerprint)
        for path in _list_untracked(workspace, env=env)
        if (
            fingerprint := _path_fingerprint(
                workspace / path,
                exact=_matches_any_boundary_pattern(path, exact_patterns),
            )
        )
        is not None
    ]


def _changed_baseline_untracked(
    workspace: Path,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline],
) -> list[WorkspaceUntrackedBaseline]:
    return [
        entry
        for entry in baseline_untracked
        if _path_fingerprint(
            workspace / entry.path,
            exact=_is_exact_fingerprint(entry.fingerprint),
        )
        != entry.fingerprint
    ]


def _path_fingerprint(path: Path, *, exact: bool) -> str | None:
    try:
        file_stat = path.lstat()
    except FileNotFoundError:
        return None

    mode = stat.S_IMODE(file_stat.st_mode)
    if stat.S_ISLNK(file_stat.st_mode):
        return f"symlink:{mode:o}:{os.readlink(path)}"
    if not stat.S_ISREG(file_stat.st_mode):
        return f"other:{mode:o}:{file_stat.st_size}:{file_stat.st_mtime_ns}"
    if not exact:
        return (
            "file-stat:"
            f"{mode:o}:{file_stat.st_size}:"
            f"{file_stat.st_mtime_ns}:{file_stat.st_ctime_ns}"
        )

    digest = hashlib.sha256()
    digest.update(f"file:{mode:o}:".encode("utf-8"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matches_any_boundary_pattern(path: str, patterns: Sequence[str]) -> bool:
    return any(path_matches_boundary_glob(path, pattern) for pattern in patterns)


def _is_exact_fingerprint(fingerprint: str) -> bool:
    return not fingerprint.startswith("file-stat:")


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
