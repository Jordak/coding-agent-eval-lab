from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from agentlab.runtime.agent_harness_config import normalize_agent_harness_config
from agentlab.runtime.resource_usage import (
    ResourceUsage,
    resource_usage_to_dict,
)
from agentlab.runtime.run_surface import normalize_run_surface
from agentlab.execution.scoring import CheckResult
from agentlab.tasks.boundaries import scope_oracle_metadata


def write_result_json(run: Any) -> None:
    run.result_path.write_text(
        json.dumps(to_result_dict(run), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def to_result_dict(run: Any) -> Dict[str, Any]:
    status = "passed" if run.score.tests_passed else "failed"
    setup_created_untracked_changed_paths = (
        _setup_created_untracked_changed_paths(run.agent_run)
    )
    agent_harness_config = normalize_agent_harness_config(
        getattr(run.agent_run, "agent_harness_config", {}),
        agent_name=run.agent_run.agent_name,
        model_name=run.agent_run.model_name,
        cost_usd=run.agent_run.cost_usd,
    )
    run_surface = normalize_run_surface(
        _workspace_run_surface(run),
        agent_harness_config=agent_harness_config,
        agent_name=run.agent_run.agent_name,
        status=status,
        success=run.score.tests_passed,
        error=run.agent_run.error,
    )
    outcome = {
        "status": status,
        "files_changed": run.agent_run.files_changed,
        "n_files_changed": len(run.agent_run.files_changed),
        "lines_added": run.agent_run.lines_added,
        "lines_deleted": run.agent_run.lines_deleted,
        "diff_path": str(run.agent_run.diff_path),
    }
    if setup_created_untracked_changed_paths:
        outcome["setup_created_untracked_changed_paths"] = (
            setup_created_untracked_changed_paths
        )
    result = {
        "trial_kind": "agent_trial",
        "trial_id": run.run_dir.name,
        "run_id": run.run_dir.name,
        "task_id": run.task.id,
        "task_title": run.task.title,
        "task_repo": run.task.repo,
        "task_commit": run.task.commit,
        "eval_suite": run.task.suite,
        "eval_type": run.task.eval_type,
        "reference_artifact": _reference_artifact_to_dict(
            run.task.reference_artifact
        ),
        "agent_name": run.agent_run.agent_name,
        "model_name": run.agent_run.model_name,
        "agent_harness_config": agent_harness_config,
        "run_surface": run_surface,
        "status": status,
        "success": run.score.tests_passed,
        "outcome": outcome,
        "score_notes": run.score.notes,
        "duration_ms": run.agent_run.duration_ms,
        "error": run.agent_run.error,
        "cost_usd": run.agent_run.cost_usd,
        "input_tokens": run.agent_run.input_tokens,
        "cached_input_tokens": run.agent_run.cached_input_tokens,
        "output_tokens": run.agent_run.output_tokens,
        "reasoning_output_tokens": run.agent_run.reasoning_output_tokens,
        "resource_usage": resource_usage_to_dict(
            ResourceUsage(
                input_tokens=run.agent_run.input_tokens,
                cached_input_tokens=run.agent_run.cached_input_tokens,
                output_tokens=run.agent_run.output_tokens,
                reasoning_output_tokens=run.agent_run.reasoning_output_tokens,
                cost_usd=run.agent_run.cost_usd,
            )
        ),
        "files_changed": run.agent_run.files_changed,
        "lines_added": run.agent_run.lines_added,
        "lines_deleted": run.agent_run.lines_deleted,
        "commands_run": run.agent_run.commands_run,
        "checks": [_check_to_dict(check) for check in run.score.checks],
        "graders": [_check_to_grader_dict(check) for check in run.score.checks],
        "report_path": str(run.report_path),
        "transcript_path": str(run.agent_run.transcript_path),
        "diff_path": str(run.agent_run.diff_path),
        "run_dir": str(run.run_dir),
    }
    if setup_created_untracked_changed_paths:
        result["setup_created_untracked_changed_paths"] = (
            setup_created_untracked_changed_paths
        )
    metadata = _scope_oracle_to_dict(run.task)
    if metadata:
        result["scope_oracle"] = metadata
    return result


def reference_verification_to_result_dict(verification: Any) -> Dict[str, Any]:
    status = "passed" if verification.success else "failed"
    output_dir = verification.result_path.parent
    setup_created_untracked_changed_paths = (
        _setup_created_untracked_changed_paths(verification)
    )
    agent_harness_config = normalize_agent_harness_config(
        {},
        agent_name="reference",
        model_name=None,
        cost_usd=None,
    )
    run_surface = normalize_run_surface(
        _workspace_run_surface(verification),
        agent_harness_config=agent_harness_config,
        agent_name="reference",
        status=status,
        success=verification.success,
        error=None,
    )
    outcome = {
        "status": status,
        "files_changed": verification.files_changed,
        "n_files_changed": len(verification.files_changed),
        "lines_added": verification.lines_added,
        "lines_deleted": verification.lines_deleted,
        "diff_path": _display_path(verification.diff_path, output_dir),
    }
    if setup_created_untracked_changed_paths:
        outcome["setup_created_untracked_changed_paths"] = (
            setup_created_untracked_changed_paths
        )
    result = {
        "trial_kind": "reference_verification",
        "trial_id": f"{verification.task.id}-reference",
        "run_id": f"{verification.task.id}-reference",
        "task_id": verification.task.id,
        "task_title": verification.task.title,
        "task_repo": verification.task.repo,
        "task_commit": verification.task.commit,
        "eval_suite": verification.task.suite,
        "eval_type": verification.task.eval_type,
        "reference_artifact": _reference_artifact_to_dict(
            verification.task.reference_artifact
        ),
        "agent_name": "reference",
        "model_name": None,
        "agent_harness_config": agent_harness_config,
        "run_surface": run_surface,
        "status": status,
        "success": verification.success,
        "outcome": outcome,
        "score_notes": verification.notes,
        "duration_ms": 0,
        "error": None,
        "cost_usd": None,
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_output_tokens": None,
        "resource_usage": resource_usage_to_dict(ResourceUsage()),
        "files_changed": verification.files_changed,
        "lines_added": verification.lines_added,
        "lines_deleted": verification.lines_deleted,
        "commands_run": [check.command for check in verification.all_checks],
        "checks": [_check_to_dict(check) for check in verification.all_checks],
        "graders": [
            _check_to_grader_dict(check) for check in verification.all_checks
        ],
        "report_path": _display_path(verification.report_path, output_dir),
        "transcript_path": None,
        "diff_path": _display_path(verification.diff_path, output_dir),
        "run_dir": _display_path(output_dir, output_dir),
    }
    if setup_created_untracked_changed_paths:
        result["setup_created_untracked_changed_paths"] = (
            setup_created_untracked_changed_paths
        )
    metadata = _scope_oracle_to_dict(verification.task)
    if metadata:
        result["scope_oracle"] = metadata
    return result


def discover_result_files(runs_dir: Path) -> List[Path]:
    if not runs_dir.exists():
        return []
    return sorted(runs_dir.glob("*/result.json"))


def _workspace_run_surface(run: Any) -> Dict[str, Any]:
    return {
        "workspace_history_policy": getattr(
            run,
            "workspace_history_policy",
            None,
        ),
        "workspace_base_ref": getattr(run, "workspace_base_ref", None),
    }


def _check_to_dict(check: CheckResult) -> Dict[str, Any]:
    return {
        "command": check.command,
        "returncode": check.returncode,
        "passed": check.passed,
        "stdout": _trim(check.stdout),
        "stderr": _trim(check.stderr),
    }


def _reference_artifact_to_dict(artifact: Any) -> Dict[str, Any] | None:
    if artifact is None:
        return None
    return {
        "type": artifact.type,
        "path": artifact.path,
        "commit": artifact.commit,
    }


def _scope_oracle_to_dict(task: Any) -> Dict[str, object]:
    return scope_oracle_metadata(
        consent_style=getattr(task, "consent_style", None),
        allowed_paths=getattr(task.success, "allowed_paths", None),
        forbidden_paths=getattr(task.success, "forbidden_paths", []),
    )


def _setup_created_untracked_changed_paths(value: Any) -> list[str]:
    paths = getattr(value, "setup_created_untracked_changed_paths", [])
    return [str(path) for path in paths]


def _check_to_grader_dict(check: CheckResult) -> Dict[str, Any]:
    return {
        "type": "code",
        "assertion": check.command,
        "passed": check.passed,
        "returncode": check.returncode,
    }


def _trim(value: str, max_chars: int = 4000) -> str:
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]


def _display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)
