from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tarfile
import tempfile

from agentlab.execution.commands import run_git
from agentlab.tasks import EvalTask


WORKSPACE_HISTORY_POLICY = "base_only"
SYNTHETIC_COMMIT_NAME = "Agent Eval Lab"
SYNTHETIC_COMMIT_EMAIL = "agentlab@example.com"
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
        archive_path = prep_root / "base.tar"

        clone = run_git(["clone", task.repo, prep_repo.name], cwd=prep_root)
        if clone.returncode != 0:
            raise RuntimeError(f"git clone failed: {clone.stderr.strip()}")

        archive = run_git(
            [
                "archive",
                "--format=tar",
                f"--output={archive_path}",
                task.commit,
            ],
            cwd=prep_repo,
        )
        if archive.returncode != 0:
            raise RuntimeError(f"git archive failed: {archive.stderr.strip()}")

        workspace.mkdir(parents=True)
        _extract_archive(archive_path, workspace)

    init = run_git(["init"], cwd=workspace)
    if init.returncode != 0:
        raise RuntimeError(f"git init failed: {init.stderr.strip()}")

    add = run_git(["add", "-A"], cwd=workspace)
    if add.returncode != 0:
        raise RuntimeError(f"git add failed: {add.stderr.strip()}")

    commit = run_git(
        [
            "-c",
            f"user.name={SYNTHETIC_COMMIT_NAME}",
            "-c",
            f"user.email={SYNTHETIC_COMMIT_EMAIL}",
            "commit",
            "--allow-empty",
            "-m",
            SYNTHETIC_COMMIT_MESSAGE,
        ],
        cwd=workspace,
    )
    if commit.returncode != 0:
        raise RuntimeError(f"git commit failed: {commit.stderr.strip()}")

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


def _extract_archive(archive_path: Path, workspace: Path) -> None:
    workspace_root = workspace.resolve()
    with tarfile.open(archive_path, "r") as archive:
        for member in archive.getmembers():
            target = (workspace / member.name).resolve()
            try:
                target.relative_to(workspace_root)
            except ValueError as exc:
                raise RuntimeError(
                    f"git archive member escapes workspace: {member.name}"
                ) from exc
        archive.extractall(workspace)


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
