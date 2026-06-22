from __future__ import annotations

from agentlab.tasks.environment import describe_task_environment
from agentlab.tasks import EvalTask


def build_agent_prompt(task: EvalTask) -> str:
    lines = [
        f"Task ID: {task.id}",
        f"Title: {task.title}",
        "",
        "You are running inside a clean checkout for this task.",
        "Modify the repository to satisfy the task prompt.",
        "Keep the patch focused. Do not commit changes.",
        "",
        "Task prompt:",
        task.prompt,
        "",
    ]
    if task.visible_validation:
        lines.extend(["Suggested validation commands:"])
        lines.extend(f"- {command}" for command in task.visible_validation)
        lines.append("")
    environment_lines = describe_task_environment(task)
    if environment_lines:
        lines.extend(
            [
                "Task-local environment used by setup, grader, and agent commands:",
            ]
        )
        lines.extend(f"- {line}" for line in environment_lines)
        lines.append("")
    if task.success.max_files_changed is not None:
        lines.append(f"Expected max files changed: {task.success.max_files_changed}")
    return "\n".join(lines)
