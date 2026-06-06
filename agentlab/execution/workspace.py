from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

from agentlab.execution.commands import run_git
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
        pathspec_path = prep_root / "tracked-paths"

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
        checkout = run_git(
            [
                "--work-tree",
                str(workspace),
                "checkout",
                "-f",
                task.commit,
                "--",
                ".",
            ],
            cwd=prep_repo,
        )
        if checkout.returncode != 0:
            raise RuntimeError(f"git checkout failed: {checkout.stderr.strip()}")

        tracked_paths = run_git(
            ["ls-tree", "-rz", "--name-only", task.commit],
            cwd=prep_repo,
        )
        if tracked_paths.returncode != 0:
            raise RuntimeError(f"git ls-tree failed: {tracked_paths.stderr.strip()}")
        pathspec_path.write_text(tracked_paths.stdout, encoding="utf-8")

        _commit_synthetic_base(workspace, pathspec_path, bool(tracked_paths.stdout))
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


def _commit_synthetic_base(
    workspace: Path,
    pathspec_path: Path,
    has_tracked_paths: bool,
) -> None:
    init = run_git(["init"], cwd=workspace)
    if init.returncode != 0:
        raise RuntimeError(f"git init failed: {init.stderr.strip()}")

    if has_tracked_paths:
        add = run_git(
            [
                "add",
                "-f",
                "--pathspec-from-file",
                str(pathspec_path),
                "--pathspec-file-nul",
            ],
            cwd=workspace,
        )
        if add.returncode != 0:
            raise RuntimeError(f"git add failed: {add.stderr.strip()}")

    commit = run_git(
        [
            "-c",
            f"user.name={SYNTHETIC_COMMIT_NAME}",
            "-c",
            f"user.email={SYNTHETIC_COMMIT_EMAIL}",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "--no-gpg-sign",
            "-m",
            SYNTHETIC_COMMIT_MESSAGE,
        ],
        cwd=workspace,
        env=_synthetic_commit_env(),
    )
    if commit.returncode != 0:
        raise RuntimeError(f"git commit failed: {commit.stderr.strip()}")


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
