from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agentlab.scoring import CheckResult


def write_result_json(run: Any) -> None:
    run.result_path.write_text(
        json.dumps(to_result_dict(run), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def to_result_dict(run: Any) -> Dict[str, Any]:
    return {
        "trial_id": run.run_dir.name,
        "run_id": run.run_dir.name,
        "task_id": run.task.id,
        "task_title": run.task.title,
        "eval_suite": run.task.suite,
        "eval_type": run.task.eval_type,
        "agent_name": run.agent_run.agent_name,
        "model_name": run.agent_run.model_name,
        "status": "passed" if run.score.tests_passed else "failed",
        "success": run.score.tests_passed,
        "outcome": {
            "status": "passed" if run.score.tests_passed else "failed",
            "files_changed": run.agent_run.files_changed,
            "n_files_changed": len(run.agent_run.files_changed),
            "diff_path": str(run.agent_run.diff_path),
        },
        "score_notes": run.score.notes,
        "duration_ms": run.agent_run.duration_ms,
        "error": run.agent_run.error,
        "cost_usd": run.agent_run.cost_usd,
        "files_changed": run.agent_run.files_changed,
        "commands_run": run.agent_run.commands_run,
        "checks": [_check_to_dict(check) for check in run.score.checks],
        "graders": [_check_to_grader_dict(check) for check in run.score.checks],
        "report_path": str(run.report_path),
        "transcript_path": str(run.agent_run.transcript_path),
        "diff_path": str(run.agent_run.diff_path),
        "run_dir": str(run.run_dir),
    }


def discover_result_files(runs_dir: Path) -> List[Path]:
    if not runs_dir.exists():
        return []
    return sorted(runs_dir.glob("*/result.json"))


def load_results(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for path in paths:
        try:
            results.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return results


def _check_to_dict(check: CheckResult) -> Dict[str, Any]:
    return {
        "command": check.command,
        "returncode": check.returncode,
        "passed": check.passed,
        "stdout": _trim(check.stdout),
        "stderr": _trim(check.stderr),
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
