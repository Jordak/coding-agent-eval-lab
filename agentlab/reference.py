from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
import json
from pathlib import Path

from agentlab.commands import run_commands
from agentlab.commands import run_git
from agentlab.environment import build_task_environment
from agentlab.patches import count_patch_lines
from agentlab.reporting import render_reference_report
from agentlab.results import reference_verification_to_result_dict
from agentlab.scoring import CheckResult
from agentlab.scoring import Score
from agentlab.scoring import calculate_grader_outcome
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

    prepared = prepare_workspace(task, workspace_root)
    task_env = build_task_environment(task, prepared.path)
    setup_checks = run_commands(task.setup, prepared.path, env=task_env)
    baseline_checks = run_commands(task.baseline, prepared.path, env=task_env)

    if artifact.type == "patch":
        artifact_check = _apply_patch_artifact(task, prepared.path)
    elif artifact.type == "commit":
        artifact_check = _checkout_commit_artifact(task, prepared.path)
    else:
        raise ReferenceVerificationError(
            f"unsupported reference artifact type: {artifact.type}"
        )

    target_checks = run_commands(task.test, prepared.path, env=task_env)
    output_dir = _reference_output_dir(task, workspace_root, write_artifacts)
    diff_path = output_dir / "reference.diff"
    files_changed = _reference_files_changed(task, prepared.path, diff_path)
    patch_stats = count_patch_lines(diff_path.read_text(encoding="utf-8"))
    all_checks = setup_checks + baseline_checks + [artifact_check] + target_checks
    score = calculate_grader_outcome(task, all_checks, files_changed)

    verification = ReferenceVerification(
        task=task,
        workspace=prepared.path,
        artifact_check=artifact_check,
        score=score,
        setup_checks=setup_checks,
        baseline_checks=baseline_checks,
        target_checks=target_checks,
        files_changed=files_changed,
        lines_added=patch_stats.lines_added,
        lines_deleted=patch_stats.lines_deleted,
        diff_path=diff_path,
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


def _reference_files_changed(
    task: EvalTask,
    workspace: Path,
    diff_path: Path,
) -> list[str]:
    if task.reference_artifact and task.reference_artifact.type == "commit":
        return capture_diff(workspace, diff_path, base_ref=task.commit)
    return capture_diff(workspace, diff_path)


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
