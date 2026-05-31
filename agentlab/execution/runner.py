from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from agentlab.agents.base import AgentAdapter
from agentlab.agents.base import AgentRun
from agentlab.reports.trial_markdown import render_markdown_report
from agentlab.execution.scoring import Score
from agentlab.execution.phases import TaskActionResult
from agentlab.execution.phases import execute_task_phases
from agentlab.tasks import EvalTask


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

    agent_run: AgentRun | None = None

    def run_agent(workspace: Path, _task_env: object) -> TaskActionResult:
        nonlocal agent_run
        agent_run = agent.run(task, workspace, run_dir)
        return TaskActionResult(agent_error=agent_run.error)

    diff_path = run_dir / "diff.patch"
    execution = execute_task_phases(
        task,
        run_dir / "workspace",
        run_agent,
        diff_path,
    )
    if agent_run is None:
        raise RuntimeError("agent did not return a run result")

    agent_run = replace(
        agent_run,
        diff_path=execution.diff_path,
        files_changed=execution.files_changed,
        commands_run=[check.command for check in execution.all_checks],
        lines_added=execution.lines_added,
        lines_deleted=execution.lines_deleted,
        success=execution.score.tests_passed,
    )

    report_path = run_dir / "report.md"
    result_path = run_dir / "result.json"
    evaluation = EvaluationRun(
        task=task,
        agent_run=agent_run,
        score=execution.score,
        run_dir=run_dir,
        report_path=report_path,
        result_path=result_path,
    )
    report_path.write_text(render_markdown_report(evaluation), encoding="utf-8")
    from agentlab.evidence.results import write_result_json

    write_result_json(evaluation)
    return evaluation


def _run_id(task_id: str, agent_name: str) -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{task_id}-{agent_name}-{uuid.uuid4().hex[:8]}"
