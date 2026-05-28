from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
import json
from pathlib import Path

from agentlab.commands import run_git
from agentlab.reporting import render_reference_report
from agentlab.results import reference_verification_to_result_dict
from agentlab.scoring import CheckResult
from agentlab.scoring import Score
from agentlab.task_execution import TaskActionResult
from agentlab.task_execution import execute_task_phases
from agentlab.tasks import EvalTask


class ReferenceVerificationError(RuntimeError):
    """Raised when a reference artifact cannot be verified."""


@dataclass(frozen=True)
class ReferenceVerification:
    task: EvalTask
    workspace: Path
    artifact_check: CheckResult
    score: Score
    setup_checks: list[CheckResult] = field(default_factory=list)
    baseline_checks: list[CheckResult] = field(default_factory=list)
    target_checks: list[CheckResult] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    lines_added: int = 0
    lines_deleted: int = 0
    diff_path: Path = Path("reference.diff")
    report_path: Path = Path("reference-report.md")
    result_path: Path = Path("reference-result.json")

    @property
    def success(self) -> bool:
        return self.score.tests_passed

    @property
    def notes(self) -> list[str]:
        return self.score.notes

    @property
    def all_checks(self) -> list[CheckResult]:
        return self.score.checks


def verify_reference(
    task: EvalTask,
    workspace_root: Path,
    write_artifacts: bool = False,
) -> ReferenceVerification:
    artifact = task.reference_artifact
    if artifact is None:
        raise ReferenceVerificationError(
            f"task has no reference_artifact: {task.id}"
        )

    artifact_check: CheckResult | None = None

    def apply_reference_artifact(
        workspace: Path,
        _task_env: object,
    ) -> TaskActionResult:
        nonlocal artifact_check
        if artifact.type == "patch":
            artifact_check = _apply_patch_artifact(task, workspace)
        elif artifact.type == "commit":
            artifact_check = _checkout_commit_artifact(task, workspace)
        else:
            raise ReferenceVerificationError(
                f"unsupported reference artifact type: {artifact.type}"
            )
        return TaskActionResult(checks=[artifact_check])

    output_dir: Path | None = None

    def reference_diff_path(_workspace: Path) -> Path:
        nonlocal output_dir
        output_dir = _reference_output_dir(task, workspace_root, write_artifacts)
        return output_dir / "reference.diff"

    execution = execute_task_phases(
        task,
        workspace_root,
        apply_reference_artifact,
        reference_diff_path,
        diff_base_ref=_reference_diff_base_ref(task),
    )
    if artifact_check is None:
        raise RuntimeError("reference artifact did not produce a check")
    if output_dir is None:
        output_dir = execution.diff_path.parent

    verification = ReferenceVerification(
        task=task,
        workspace=execution.workspace,
        artifact_check=artifact_check,
        score=execution.score,
        setup_checks=execution.setup_checks,
        baseline_checks=execution.baseline_checks,
        target_checks=execution.target_checks,
        files_changed=execution.files_changed,
        lines_added=execution.lines_added,
        lines_deleted=execution.lines_deleted,
        diff_path=execution.diff_path,
        report_path=output_dir / "reference-report.md",
        result_path=output_dir / "reference-result.json",
    )
    if write_artifacts:
        write_reference_artifacts(verification)
    return verification


def write_reference_artifacts(verification: ReferenceVerification) -> None:
    verification.report_path.write_text(
        render_reference_report(verification),
        encoding="utf-8",
    )
    verification.result_path.write_text(
        json.dumps(
            reference_verification_to_result_dict(verification),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
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


def _reference_diff_base_ref(task: EvalTask) -> str | None:
    if task.reference_artifact and task.reference_artifact.type == "commit":
        return task.commit
    return None


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


def _reference_output_dir(
    task: EvalTask,
    workspace_root: Path,
    write_artifacts: bool,
) -> Path:
    if write_artifacts:
        if task.source_path is None:
            raise ReferenceVerificationError(
                "writing reference artifacts requires task.source_path"
            )
        return task.source_path.parent
    return workspace_root
