from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from agentlab.commands import run_commands
from agentlab.commands import run_git
from agentlab.scoring import CheckResult
from agentlab.tasks import EvalTask
from agentlab.workspace import capture_diff
from agentlab.workspace import prepare_workspace


class ReferenceVerificationError(RuntimeError):
    """Raised when a reference artifact cannot be verified."""


@dataclass(frozen=True)
class ReferenceVerification:
    task: EvalTask
    workspace: Path
    artifact_check: CheckResult
    setup_checks: list[CheckResult] = field(default_factory=list)
    baseline_checks: list[CheckResult] = field(default_factory=list)
    target_checks: list[CheckResult] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        checks = self.setup_checks + self.baseline_checks + [self.artifact_check]
        checks += self.target_checks
        return all(check.passed for check in checks) and not self.notes


def verify_reference(task: EvalTask, workspace_root: Path) -> ReferenceVerification:
    artifact = task.reference_artifact
    if artifact is None:
        raise ReferenceVerificationError(
            f"task has no reference_artifact: {task.id}"
        )

    prepared = prepare_workspace(task, workspace_root)
    setup_checks = run_commands(task.setup, prepared.path)
    baseline_checks = run_commands(task.baseline, prepared.path)

    if artifact.type == "patch":
        artifact_check = _apply_patch_artifact(task, prepared.path)
    elif artifact.type == "commit":
        artifact_check = _checkout_commit_artifact(task, prepared.path)
    else:
        raise ReferenceVerificationError(
            f"unsupported reference artifact type: {artifact.type}"
        )

    target_checks = run_commands(task.test, prepared.path)
    diff_path = workspace_root / f"{task.id}-reference.diff"
    files_changed = _reference_files_changed(task, prepared.path, diff_path)
    notes = _success_notes(task, files_changed)

    return ReferenceVerification(
        task=task,
        workspace=prepared.path,
        artifact_check=artifact_check,
        setup_checks=setup_checks,
        baseline_checks=baseline_checks,
        target_checks=target_checks,
        files_changed=files_changed,
        notes=notes,
    )


def _apply_patch_artifact(task: EvalTask, workspace: Path) -> CheckResult:
    artifact = task.reference_artifact
    assert artifact is not None
    if task.source_path is None:
        raise ReferenceVerificationError(
            "patch reference artifacts require task.source_path"
        )
    if not artifact.path:
        raise ReferenceVerificationError("patch reference artifact is missing path")

    patch_path = task.source_path.parent / artifact.path
    completed = run_git(["apply", str(patch_path.resolve())], cwd=workspace)
    return _git_check_result(completed, f"git apply {artifact.path}")


def _checkout_commit_artifact(task: EvalTask, workspace: Path) -> CheckResult:
    artifact = task.reference_artifact
    assert artifact is not None
    if not artifact.commit:
        raise ReferenceVerificationError("commit reference artifact is missing commit")

    completed = run_git(["checkout", artifact.commit], cwd=workspace)
    return _git_check_result(completed, f"git checkout {artifact.commit}")


def _reference_files_changed(
    task: EvalTask,
    workspace: Path,
    diff_path: Path,
) -> list[str]:
    if task.reference_artifact and task.reference_artifact.type == "commit":
        changed = run_git(["diff", "--name-only", task.commit], cwd=workspace)
        if changed.returncode != 0:
            raise ReferenceVerificationError(
                f"git diff --name-only failed: {changed.stderr.strip()}"
            )
        return [line for line in changed.stdout.splitlines() if line.strip()]
    return capture_diff(workspace, diff_path)


def _success_notes(task: EvalTask, files_changed: list[str]) -> list[str]:
    notes: list[str] = []
    max_files_changed = task.success.max_files_changed
    if max_files_changed is not None and len(files_changed) > max_files_changed:
        notes.append(
            "changed "
            f"{len(files_changed)} files; limit is {max_files_changed}"
        )
    return notes


def _git_check_result(
    completed: subprocess.CompletedProcess[str],
    command: str,
) -> CheckResult:
    return CheckResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
