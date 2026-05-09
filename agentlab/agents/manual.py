from __future__ import annotations

import time
from pathlib import Path

from agentlab.agents.base import AgentRun
from agentlab.environment import describe_task_environment
from agentlab.tasks import EvalTask


class ManualAgentAdapter:
    """Human-in-the-loop adapter for proving the eval harness before SDK integration."""

    name = "manual"

    def __init__(self, pause: bool = True):
        self.pause = pause

    def run(self, task: EvalTask, workspace: Path, run_dir: Path) -> AgentRun:
        run_dir.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        transcript_path = run_dir / "transcript.md"
        diff_path = run_dir / "diff.patch"
        events = [
            f"# Manual Run: {task.id}",
            "",
            f"Workspace: `{workspace}`",
            "",
            "## Prompt",
            "",
            task.prompt,
            "",
        ]

        if self.pause:
            _print_manual_instructions(task, workspace)
            try:
                input("Press Enter here when your edits are finished...")
                events.append("Human edit pause completed.")
            except EOFError:
                events.append("Input stream closed; continuing without a manual pause.")
        else:
            events.append("Manual pause disabled; continuing without edits.")

        transcript_path.write_text(
            "\n".join(events),
            encoding="utf-8",
        )
        diff_path.write_text("", encoding="utf-8")

        duration_ms = int((time.monotonic() - start) * 1000)
        return AgentRun(
            agent_name=self.name,
            task_id=task.id,
            transcript_path=transcript_path,
            diff_path=diff_path,
            duration_ms=duration_ms,
        )


def _print_manual_instructions(task: EvalTask, workspace: Path) -> None:
    print("")
    print("Manual agent pause")
    print("==================")
    print(f"Task: {task.id} - {task.title}")
    print(f"Workspace: {workspace}")
    print("")
    print("Prompt:")
    print(task.prompt)
    print("")
    print("Edit files in the workspace above. When done, return here and press Enter.")
    environment_lines = describe_task_environment(task)
    if environment_lines:
        print("")
        print("Task-local environment used by setup, grader, and agent commands:")
        for line in environment_lines:
            print(f"- {line}")
    if task.test:
        print("")
        print("Code-based grader assertions that will run after you continue:")
        for command in task.test:
            print(f"- {command}")
    print("")
