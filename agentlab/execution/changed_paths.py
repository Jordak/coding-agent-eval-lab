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

from agentlab.execution.commands import isolated_git_env, run_git, run_git_bytes
from agentlab.tasks.boundaries import path_matches_boundary_glob


_MAX_GIT_PATHSPEC_ARG_BYTES = 32 * 1024


@dataclass(frozen=True)
class WorkspaceUntrackedBaseline:
    path: str
    fingerprint: str
    exact: bool = False


@dataclass(frozen=True)
class WorkspaceIndexBaseline:
    path: str
    setup_index_signature: str | None


@dataclass(frozen=True)
class WorkspaceChangeBaseline:
    tree_ref: str
    untracked_files: tuple[WorkspaceUntrackedBaseline, ...] = field(
        default_factory=tuple
    )
    reset_index_entries: tuple[WorkspaceIndexBaseline, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class CapturedDiff:
    files_changed: list[str]
    setup_created_untracked_changed_paths: list[str] = field(default_factory=list)
    setup_created_untracked_coverage_caveat_count: int = 0


@dataclass(frozen=True)
class _GitPathspecResult:
    returncode: int
    stdout: str
    stderr: str


def capture_change_baseline(
    workspace: Path,
    *,
    exact_untracked_patterns: Sequence[str] = (),
) -> WorkspaceChangeBaseline:
    workspace_env = isolated_git_env()
    with tempfile.TemporaryDirectory(prefix="agentlab-index-") as temp:
        index_env = isolated_git_env(
            {"GIT_INDEX_FILE": str(Path(temp) / "index")}
        )
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
            _reset_index_entries(
                workspace,
                tree_ref,
                diff_env=index_env,
                index_env=workspace_env,
            )
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
        reset_index_entries=reset_index_entries,
    )


def capture_diff(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
) -> list[str]:
    return capture_diff_details_preserving_index(
        workspace,
        diff_path,
        base_ref=base_ref,
        baseline_untracked=baseline_untracked,
        baseline_reset_index=baseline_reset_index,
    ).files_changed


def capture_diff_details_preserving_index(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
) -> CapturedDiff:
    return capture_diff_details(
        workspace,
        diff_path,
        base_ref=base_ref,
        baseline_untracked=baseline_untracked,
        baseline_reset_index=baseline_reset_index,
    )


def capture_diff_details(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
    env: Mapping[str, str] | None = None,
) -> CapturedDiff:
    git_env = isolated_git_env()
    if env is not None:
        git_env = env
    with _preserve_git_index(workspace, env=git_env):
        return _capture_diff_details_with_index_env(
            workspace,
            diff_path,
            base_ref=base_ref,
            baseline_untracked=baseline_untracked,
            baseline_reset_index=baseline_reset_index,
            env=git_env,
        )


def _capture_diff_details_with_index_env(
    workspace: Path,
    diff_path: Path,
    base_ref: str | None = None,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline] = (),
    baseline_reset_index: Sequence[WorkspaceIndexBaseline] = (),
    *,
    env: Mapping[str, str],
) -> CapturedDiff:
    git_env = env
    diff_ref = base_ref or "HEAD"
    changed_baseline_untracked = _changed_baseline_untracked(
        workspace,
        baseline_untracked,
        env=git_env,
    )
    unsuppressed_baseline_paths = {
        entry.path
        for entry in changed_baseline_untracked
        if entry.exact
    }
    suppressed_baseline_paths = [
        entry.path
        for entry in baseline_untracked
        if entry.path not in unsuppressed_baseline_paths
    ]
    _mark_untracked_for_diff(
        workspace,
        exclude_untracked=suppressed_baseline_paths,
        env=git_env,
    )
    name_args = ["diff", "--name-only", "-z", "--no-renames", diff_ref]
    cached_name_args = [
        "diff",
        "--cached",
        "--name-only",
        "-z",
        "--no-renames",
        diff_ref,
    ]

    worktree_paths = _diff_names(
        workspace,
        name_args,
        "git diff --name-only",
        env=git_env,
    )
    cached_paths = _diff_names(
        workspace,
        cached_name_args,
        "git diff --cached --name-only",
        env=git_env,
    )
    staged_changed_baseline_untracked = _changed_staged_baseline_untracked(
        workspace,
        baseline_untracked,
        cached_paths,
        changed_baseline_paths={entry.path for entry in changed_baseline_untracked},
        env=git_env,
    )
    if staged_changed_baseline_untracked:
        changed_baseline_untracked = _append_missing_untracked_entries(
            changed_baseline_untracked,
            staged_changed_baseline_untracked,
        )
        unsuppressed_baseline_paths.update(
            entry.path for entry in staged_changed_baseline_untracked
        )
        suppressed_baseline_paths = [
            entry.path
            for entry in baseline_untracked
            if entry.path not in unsuppressed_baseline_paths
        ]
    worktree_paths = _filter_suppressed_baseline_untracked_paths(
        worktree_paths,
        suppressed_baseline_paths,
    )
    cached_paths = _filter_suppressed_baseline_untracked_paths(
        cached_paths,
        suppressed_baseline_paths,
    )
    cached_paths = _filter_reset_baseline_cached_paths(
        workspace,
        cached_paths,
        worktree_paths,
        baseline_reset_index,
        env=git_env,
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
        setup_created_untracked_coverage_caveat_count=sum(
            1 for entry in baseline_untracked if not entry.exact
        ),
    )


@contextmanager
def _preserve_git_index(
    workspace: Path,
    *,
    env: Mapping[str, str],
) -> Iterator[None]:
    index_path = _git_index_path(workspace, env=env)
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


def _git_index_path(workspace: Path, *, env: Mapping[str, str]) -> Path:
    index = run_git(["rev-parse", "--git-path", "index"], cwd=workspace, env=env)
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
    env: Mapping[str, str],
) -> None:
    excluded = tuple(exclude_untracked)
    paths = [
        path for path in _list_untracked(workspace, env=env)
        if not _is_excluded_untracked(path, excluded)
    ]
    if not paths:
        return
    marked = _run_git_pathspec(
        ["add", "--intent-to-add", "--force"],
        paths,
        cwd=workspace,
        env=env,
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


def _reset_index_entries(
    workspace: Path,
    tree_ref: str,
    *,
    diff_env: Mapping[str, str],
    index_env: Mapping[str, str],
) -> list[WorkspaceIndexBaseline]:
    paths = _diff_names(
        workspace,
        ["diff", "--cached", "--name-only", "-z", "--no-renames", tree_ref],
        "git diff --cached --name-only",
        env=diff_env,
    )
    return [
        WorkspaceIndexBaseline(
            path=path,
            setup_index_signature=_index_entry_signature(
                workspace,
                path,
                env=index_env,
            ),
        )
        for path in paths
    ]


def _filter_reset_baseline_cached_paths(
    workspace: Path,
    cached_paths: Sequence[str],
    worktree_paths: Sequence[str],
    baseline_reset_index: Sequence[WorkspaceIndexBaseline],
    *,
    env: Mapping[str, str],
) -> list[str]:
    if not baseline_reset_index:
        return list(cached_paths)

    worktree_path_set = set(worktree_paths)
    setup_index_by_path = {entry.path: entry for entry in baseline_reset_index}
    filtered: list[str] = []
    for path in cached_paths:
        baseline = setup_index_by_path.get(path)
        if path in worktree_path_set or baseline is None:
            filtered.append(path)
            continue
        if (
            _index_entry_signature(workspace, path, env=env)
            != baseline.setup_index_signature
        ):
            filtered.append(path)
    return filtered


def _filter_suppressed_baseline_untracked_paths(
    paths: Sequence[str],
    suppressed_baseline_paths: Sequence[str],
) -> list[str]:
    if not suppressed_baseline_paths:
        return list(paths)

    suppressed_path_set = set(suppressed_baseline_paths)
    return [path for path in paths if path not in suppressed_path_set]


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


def _cached_diff_for_paths(
    workspace: Path,
    diff_ref: str,
    paths: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> str:
    if not paths:
        return ""
    return _batched_git_diff(
        ["diff", "--binary", "--no-renames", "--cached", diff_ref],
        paths,
        "git diff --cached",
        cwd=workspace,
        env=env,
    )


def _worktree_diff_for_paths(
    workspace: Path,
    diff_ref: str,
    paths: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> str:
    if not paths:
        return ""
    return _batched_git_diff(
        ["diff", "--binary", "--no-renames", diff_ref],
        paths,
        "git diff",
        cwd=workspace,
        env=env,
    )


def _join_diffs(*diffs: str) -> str:
    chunks = [diff for diff in diffs if diff]
    if not chunks:
        return ""
    return "\n".join(diff.rstrip("\n") for diff in chunks) + "\n"


def _batched_git_diff(
    args: list[str],
    paths: Sequence[str],
    command_name: str,
    *,
    cwd: Path,
    env: Mapping[str, str] | None,
) -> str:
    diffs: list[str] = []
    for batch in _pathspec_arg_batches(args, paths):
        completed = run_git(args + ["--"] + batch, cwd=cwd, env=env)
        if completed.returncode != 0:
            raise RuntimeError(
                f"{command_name} failed: {completed.stderr.strip()}"
            )
        diffs.append(completed.stdout)
    return _join_diffs(*diffs)


def _pathspec_arg_batches(
    args: Sequence[str],
    paths: Sequence[str],
) -> Iterator[list[str]]:
    base_size = _argv_size(["git", *args, "--"])
    batch: list[str] = []
    batch_size = base_size
    for path in paths:
        path_size = _argv_size([path])
        if batch and batch_size + path_size > _MAX_GIT_PATHSPEC_ARG_BYTES:
            yield batch
            batch = []
            batch_size = base_size
        batch.append(path)
        batch_size += path_size
    if batch:
        yield batch


def _argv_size(args: Sequence[str]) -> int:
    return sum(len(arg.encode("utf-8", errors="surrogateescape")) + 1 for arg in args)


def _run_git_pathspec(
    args: list[str],
    paths: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None,
) -> _GitPathspecResult:
    completed = run_git_bytes(
        args + ["--pathspec-from-file=-", "--pathspec-file-nul"],
        cwd=cwd,
        env=env,
        input_bytes=_pathspec_input(paths),
    )
    return _GitPathspecResult(
        returncode=completed.returncode,
        stdout=completed.stdout.decode("utf-8", errors="surrogateescape"),
        stderr=completed.stderr.decode("utf-8", errors="replace"),
    )


def _pathspec_input(paths: Sequence[str]) -> bytes:
    return ("\0".join(paths) + "\0").encode("utf-8", errors="surrogateescape")


def _snapshot_untracked_files(
    workspace: Path,
    *,
    env: Mapping[str, str] | None = None,
    exact_patterns: Sequence[str] = (),
) -> list[WorkspaceUntrackedBaseline]:
    entries: list[WorkspaceUntrackedBaseline] = []
    for path in _list_untracked(workspace, env=env):
        exact = _matches_any_boundary_pattern(path, exact_patterns)
        fingerprint = _path_fingerprint(workspace / path, exact=exact)
        if fingerprint is not None:
            entries.append(
                WorkspaceUntrackedBaseline(
                    path=path,
                    fingerprint=fingerprint,
                    exact=exact,
                )
            )
    return entries


def _changed_baseline_untracked(
    workspace: Path,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline],
    *,
    env: Mapping[str, str],
) -> list[WorkspaceUntrackedBaseline]:
    changed: list[WorkspaceUntrackedBaseline] = []
    for entry in baseline_untracked:
        worktree_fingerprint = _path_fingerprint(
            workspace / entry.path,
            exact=entry.exact,
        )
        if worktree_fingerprint != entry.fingerprint:
            changed.append(entry)
            continue
        if entry.exact and _index_path_fingerprint(
            workspace,
            entry.path,
            env=env,
        ) not in {None, entry.fingerprint}:
            changed.append(entry)
    return changed


def _changed_staged_baseline_untracked(
    workspace: Path,
    baseline_untracked: Sequence[WorkspaceUntrackedBaseline],
    cached_paths: Sequence[str],
    *,
    changed_baseline_paths: set[str],
    env: Mapping[str, str],
) -> list[WorkspaceUntrackedBaseline]:
    if not baseline_untracked or not cached_paths:
        return []

    baseline_by_path = {entry.path: entry for entry in baseline_untracked}
    changed: list[WorkspaceUntrackedBaseline] = []
    for path in cached_paths:
        entry = baseline_by_path.get(path)
        if entry is None or path in changed_baseline_paths:
            continue
        index_fingerprint = _index_path_fingerprint(workspace, path, env=env)
        if index_fingerprint is None:
            continue
        if entry.exact:
            if index_fingerprint != entry.fingerprint:
                changed.append(entry)
            continue
        worktree_fingerprint = _path_fingerprint(
            workspace / entry.path,
            exact=False,
        )
        if worktree_fingerprint != entry.fingerprint:
            changed.append(entry)
            continue
        if _path_fingerprint(workspace / entry.path, exact=True) != index_fingerprint:
            changed.append(entry)
    return changed


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


def _index_path_fingerprint(
    workspace: Path,
    path: str,
    *,
    env: Mapping[str, str],
) -> str | None:
    entry = _index_entry(workspace, path, env=env)
    if entry is None:
        return None
    mode_text, object_id = entry
    blob = _git_blob(workspace, object_id, env=env)
    if mode_text == "120000":
        target = blob.decode("utf-8", errors="surrogateescape")
        return f"symlink:777:{target}"
    if mode_text not in {"100644", "100755"}:
        return f"other:{mode_text}:{object_id}"

    mode = int(mode_text[-3:], 8)
    digest = hashlib.sha256()
    digest.update(f"file:{mode:o}:".encode("utf-8"))
    digest.update(blob)
    return digest.hexdigest()


def _index_entry(
    workspace: Path,
    path: str,
    *,
    env: Mapping[str, str],
) -> tuple[str, str] | None:
    entry = run_git(["ls-files", "--stage", "-z", "--", path], cwd=workspace, env=env)
    if entry.returncode != 0:
        raise RuntimeError(f"git ls-files --stage failed: {entry.stderr.strip()}")
    entries = [part for part in entry.stdout.split("\0") if part]
    if not entries:
        return None
    metadata = entries[0].split("\t", 1)[0]
    mode_text, object_id, *_rest = metadata.split()
    return mode_text, object_id


def _git_blob(
    workspace: Path,
    object_id: str,
    *,
    env: Mapping[str, str],
) -> bytes:
    blob = run_git_bytes(
        ["cat-file", "blob", object_id],
        cwd=workspace,
        env=env,
    )
    if blob.returncode != 0:
        stderr = blob.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git cat-file failed: {stderr}")
    return blob.stdout


def _matches_any_boundary_pattern(path: str, patterns: Sequence[str]) -> bool:
    return any(path_matches_boundary_glob(path, pattern) for pattern in patterns)


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


def _append_missing_untracked_entries(
    entries: list[WorkspaceUntrackedBaseline],
    extra_entries: Sequence[WorkspaceUntrackedBaseline],
) -> list[WorkspaceUntrackedBaseline]:
    seen = {entry.path for entry in entries}
    for entry in extra_entries:
        if entry.path not in seen:
            entries.append(entry)
            seen.add(entry.path)
    return entries
