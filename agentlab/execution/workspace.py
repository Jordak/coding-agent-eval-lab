from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

from agentlab.execution.commands import run_git, run_git_bytes
from agentlab.tasks import EvalTask


WORKSPACE_HISTORY_POLICY = "base_only"
SYNTHETIC_COMMIT_NAME = "Agent Eval Lab"
SYNTHETIC_COMMIT_EMAIL = "agentlab@example.com"
SYNTHETIC_COMMIT_DATE = "2000-01-01T00:00:00+00:00"
SYNTHETIC_COMMIT_MESSAGE = "Synthetic task base"


@dataclass(frozen=True)
class PreparedWorkspace:
    task: EvalTask
    path: Path
    workspace_history_policy: str
    workspace_base_ref: str


@dataclass(frozen=True)
class _TreeEntry:
    mode: str
    object_type: str
    object_id: str
    path: str


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

        clone = run_git(["clone", task.repo, prep_repo.name], cwd=prep_root)
        if clone.returncode != 0:
            raise RuntimeError(f"git clone failed: {clone.stderr.strip()}")

        source_tree = run_git(
            ["rev-parse", f"{task.commit}^{{tree}}"],
            cwd=prep_repo,
        )
        if source_tree.returncode != 0:
            raise RuntimeError(f"git rev-parse failed: {source_tree.stderr.strip()}")

        workspace.mkdir(parents=True)
        entries = _source_tree_entries(prep_repo, task.commit)
        _materialize_source_tree(prep_repo, workspace, entries)
        _commit_synthetic_base(workspace, entries)
        _assert_tree_matches_source(
            workspace,
            source_tree.stdout.strip(),
        )

    base_ref = run_git(["rev-parse", "HEAD"], cwd=workspace)
    if base_ref.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {base_ref.stderr.strip()}")

    return PreparedWorkspace(
        task=task,
        path=workspace,
        workspace_history_policy=WORKSPACE_HISTORY_POLICY,
        workspace_base_ref=base_ref.stdout.strip(),
    )


def _safe_name(value: str) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in value)
    return safe.strip("-") or "task"


def _source_tree_entries(prep_repo: Path, commit: str) -> list[_TreeEntry]:
    tree = run_git(
        ["ls-tree", "-rz", "-r", "--full-tree", commit],
        cwd=prep_repo,
    )
    if tree.returncode != 0:
        raise RuntimeError(f"git ls-tree failed: {tree.stderr.strip()}")

    entries: list[_TreeEntry] = []
    for raw_entry in tree.stdout.split("\0"):
        if not raw_entry:
            continue
        header, separator, path = raw_entry.partition("\t")
        if separator != "\t":
            raise RuntimeError(f"unexpected git ls-tree entry: {raw_entry!r}")
        parts = header.split()
        if len(parts) != 3:
            raise RuntimeError(f"unexpected git ls-tree header: {header!r}")
        mode, object_type, object_id = parts
        entries.append(
            _TreeEntry(
                mode=mode,
                object_type=object_type,
                object_id=object_id,
                path=path,
            )
        )
    return entries


def _materialize_source_tree(
    prep_repo: Path,
    workspace: Path,
    entries: list[_TreeEntry],
) -> None:
    for entry in entries:
        destination = _workspace_entry_path(workspace, entry.path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if entry.object_type == "commit" and entry.mode == "160000":
            destination.mkdir(exist_ok=True)
            continue

        if entry.object_type != "blob":
            raise RuntimeError(
                f"unsupported tree entry {entry.mode} {entry.object_type} {entry.path}"
            )

        blob = _cat_blob(prep_repo, entry.object_id)
        if entry.mode == "120000":
            os.symlink(os.fsdecode(blob), destination)
            continue
        if entry.mode not in {"100644", "100755"}:
            raise RuntimeError(f"unsupported blob mode {entry.mode}: {entry.path}")

        destination.write_bytes(blob)
        if entry.mode == "100755":
            destination.chmod(0o755)
        else:
            destination.chmod(0o644)


def _workspace_entry_path(workspace: Path, path: str) -> Path:
    if path.startswith("/"):
        raise RuntimeError(f"unsafe absolute tree path: {path}")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeError(f"unsafe tree path: {path}")
    return workspace.joinpath(*parts)


def _cat_blob(prep_repo: Path, object_id: str) -> bytes:
    blob = run_git_bytes(["cat-file", "blob", object_id], cwd=prep_repo)
    if blob.returncode != 0:
        raise RuntimeError(f"git cat-file failed: {blob.stderr.decode().strip()}")
    return blob.stdout


def _commit_synthetic_base(workspace: Path, entries: list[_TreeEntry]) -> None:
    git_env = _synthetic_git_env()
    with tempfile.TemporaryDirectory(prefix="agentlab-empty-template-") as template:
        init = run_git(["init", f"--template={template}"], cwd=workspace, env=git_env)
    if init.returncode != 0:
        raise RuntimeError(f"git init failed: {init.stderr.strip()}")

    _disable_local_git_features(workspace, git_env)
    for entry in entries:
        _stage_tree_entry(workspace, entry, git_env)

    tree = run_git(["write-tree"], cwd=workspace, env=git_env)
    if tree.returncode != 0:
        raise RuntimeError(f"git write-tree failed: {tree.stderr.strip()}")

    commit = run_git(
        ["commit-tree", tree.stdout.strip(), "-m", SYNTHETIC_COMMIT_MESSAGE],
        cwd=workspace,
        env=_synthetic_commit_env(),
    )
    if commit.returncode != 0:
        raise RuntimeError(f"git commit-tree failed: {commit.stderr.strip()}")

    update_ref = run_git(
        ["update-ref", "HEAD", commit.stdout.strip()],
        cwd=workspace,
        env=git_env,
    )
    if update_ref.returncode != 0:
        raise RuntimeError(f"git update-ref failed: {update_ref.stderr.strip()}")


def _disable_local_git_features(workspace: Path, git_env: dict[str, str]) -> None:
    config = run_git(
        ["config", "core.hooksPath", ".git/hooks"],
        cwd=workspace,
        env=git_env,
    )
    if config.returncode != 0:
        raise RuntimeError(f"git config failed: {config.stderr.strip()}")
    attributes = workspace / ".git" / "info" / "attributes"
    attributes.parent.mkdir(parents=True, exist_ok=True)
    attributes.write_text("* -filter -text -ident\n", encoding="utf-8")


def _stage_tree_entry(
    workspace: Path,
    entry: _TreeEntry,
    git_env: dict[str, str],
) -> None:
    object_id = entry.object_id
    if entry.object_type == "blob":
        object_id = _store_workspace_blob(workspace, entry)
    elif not (entry.object_type == "commit" and entry.mode == "160000"):
        raise RuntimeError(
            f"unsupported tree entry {entry.mode} {entry.object_type} {entry.path}"
        )

    update_index = run_git(
        ["update-index", "--add", "--cacheinfo", entry.mode, object_id, entry.path],
        cwd=workspace,
        env=git_env,
    )
    if update_index.returncode != 0:
        raise RuntimeError(f"git update-index failed: {update_index.stderr.strip()}")


def _store_workspace_blob(workspace: Path, entry: _TreeEntry) -> str:
    source = _workspace_entry_path(workspace, entry.path)
    if entry.mode == "120000":
        blob = os.fsencode(os.readlink(source))
    else:
        blob = source.read_bytes()
    stored = run_git_bytes(
        ["hash-object", "-w", "--stdin"],
        cwd=workspace,
        input_bytes=blob,
    )
    if stored.returncode != 0:
        raise RuntimeError(f"git hash-object failed: {stored.stderr.decode().strip()}")
    object_id = stored.stdout.decode().strip()
    if object_id != entry.object_id:
        raise RuntimeError(f"materialized blob does not match source: {entry.path}")
    return object_id


def _synthetic_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }


def _synthetic_commit_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update(
        {
            "GIT_AUTHOR_NAME": SYNTHETIC_COMMIT_NAME,
            "GIT_AUTHOR_EMAIL": SYNTHETIC_COMMIT_EMAIL,
            "GIT_AUTHOR_DATE": SYNTHETIC_COMMIT_DATE,
            "GIT_COMMITTER_NAME": SYNTHETIC_COMMIT_NAME,
            "GIT_COMMITTER_EMAIL": SYNTHETIC_COMMIT_EMAIL,
            "GIT_COMMITTER_DATE": SYNTHETIC_COMMIT_DATE,
        }
    )
    return env


def _assert_tree_matches_source(workspace: Path, source_tree: str) -> None:
    synthetic_tree = run_git(["rev-parse", "HEAD^{tree}"], cwd=workspace)
    if synthetic_tree.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {synthetic_tree.stderr.strip()}")
    if synthetic_tree.stdout.strip() != source_tree:
        raise RuntimeError("synthetic workspace tree does not match task commit tree")


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
