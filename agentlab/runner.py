from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from agentlab.agents.base import AgentAdapter
from agentlab.agents.base import AgentRun
from agentlab.commands import run_commands
from agentlab.environment import build_task_environment
from agentlab.patches import count_patch_lines
from agentlab.reporting import render_markdown_report
from agentlab.scoring import Score
from agentlab.scoring import calculate_grader_outcome
from agentlab.tasks import EvalTask
from agentlab.workspace import capture_diff, prepare_workspace


@dataclass(frozen=True)
class EvaluationRun:
    task: EvalTask
    agent_run: AgentRun
    score: Score
    run_dir: Path
    report_path: Path
    result_path: Path


def run_task(task: EvalTask, agent: AgentAdapter, runs_dir: Path) -> EvaluationRun:
    run_id = _run_id(task.id, agent.name)
    run_dir = (runs_dir / run_id).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)

    prepared = prepare_workspace(task, run_dir / "workspace")
    task_env = build_task_environment(task, prepared.path)
    setup_checks = run_commands(task.setup, prepared.path, env=task_env)
    baseline_checks = run_commands(task.baseline, prepared.path, env=task_env)

    agent_run = agent.run(task, prepared.path, run_dir)
    test_checks = run_commands(task.test, prepared.path, env=task_env)

    diff_path = run_dir / "diff.patch"
    files_changed = capture_diff(prepared.path, diff_path)
    patch_stats = count_patch_lines(diff_path.read_text(encoding="utf-8"))
    all_checks = setup_checks + baseline_checks + test_checks
    score = calculate_grader_outcome(
        task,
        all_checks,
        files_changed,
        agent_error=agent_run.error,
    )

    agent_run = replace(
        agent_run,
        diff_path=diff_path,
        files_changed=files_changed,
        commands_run=[check.command for check in all_checks],
        lines_added=patch_stats.lines_added,
        lines_deleted=patch_stats.lines_deleted,
        success=score.tests_passed,
    )

    report_path = run_dir / "report.md"
    result_path = run_dir / "result.json"
    evaluation = EvaluationRun(
        task=task,
        agent_run=agent_run,
        score=score,
        run_dir=run_dir,
        report_path=report_path,
        result_path=result_path,
    )
    report_path.write_text(render_markdown_report(evaluation), encoding="utf-8")
    from agentlab.results import write_result_json

    write_result_json(evaluation)
    return evaluation


def _run_id(task_id: str, agent_name: str) -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{task_id}-{agent_name}-{uuid.uuid4().hex[:8]}"
