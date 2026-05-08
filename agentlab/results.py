from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agentlab.agent_harness_config import normalize_agent_harness_config
from agentlab.outcome_evidence import load_outcome_evidence
from agentlab.resource_usage import (
    ResourceUsage,
    resource_usage_to_dict,
)
from agentlab.scoring import CheckResult
from agentlab.validity import DEFAULT_TRIAL_VALIDITY


def write_result_json(run: Any) -> None:
    run.result_path.write_text(
        json.dumps(to_result_dict(run), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def to_result_dict(run: Any) -> Dict[str, Any]:
    return {
        "trial_kind": "agent_trial",
        "trial_id": run.run_dir.name,
        "run_id": run.run_dir.name,
        "task_id": run.task.id,
        "task_title": run.task.title,
        "eval_suite": run.task.suite,
        "eval_type": run.task.eval_type,
        "reference_artifact": _reference_artifact_to_dict(
            run.task.reference_artifact
        ),
        "agent_name": run.agent_run.agent_name,
        "model_name": run.agent_run.model_name,
        "agent_harness_config": normalize_agent_harness_config(
            getattr(run.agent_run, "agent_harness_config", {}),
            agent_name=run.agent_run.agent_name,
            model_name=run.agent_run.model_name,
            cost_usd=run.agent_run.cost_usd,
        ),
        "status": "passed" if run.score.tests_passed else "failed",
        "success": run.score.tests_passed,
        "trial_validity": DEFAULT_TRIAL_VALIDITY,
        "exclusion_reason": None,
        "outcome": {
            "status": "passed" if run.score.tests_passed else "failed",
            "files_changed": run.agent_run.files_changed,
            "n_files_changed": len(run.agent_run.files_changed),
            "lines_added": run.agent_run.lines_added,
            "lines_deleted": run.agent_run.lines_deleted,
            "diff_path": str(run.agent_run.diff_path),
        },
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


def reference_verification_to_result_dict(verification: Any) -> Dict[str, Any]:
    status = "passed" if verification.success else "failed"
    output_dir = verification.result_path.parent
    return {
        "trial_kind": "reference_verification",
        "trial_id": f"{verification.task.id}-reference",
        "run_id": f"{verification.task.id}-reference",
        "task_id": verification.task.id,
        "task_title": verification.task.title,
        "eval_suite": verification.task.suite,
        "eval_type": verification.task.eval_type,
        "reference_artifact": _reference_artifact_to_dict(
            verification.task.reference_artifact
        ),
        "agent_name": "reference",
        "model_name": None,
        "status": status,
        "success": verification.success,
        "trial_validity": DEFAULT_TRIAL_VALIDITY,
        "exclusion_reason": None,
        "outcome": {
            "status": status,
            "files_changed": verification.files_changed,
            "n_files_changed": len(verification.files_changed),
            "lines_added": verification.lines_added,
            "lines_deleted": verification.lines_deleted,
            "diff_path": _display_path(verification.diff_path, output_dir),
        },
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


def discover_result_files(runs_dir: Path) -> List[Path]:
    if not runs_dir.exists():
        return []
    return sorted(runs_dir.glob("*/result.json"))


def load_results(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for path in paths:
        evidence = load_outcome_evidence(path)
        if evidence is not None:
            results.append(evidence.to_result_dict())
    return results


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
