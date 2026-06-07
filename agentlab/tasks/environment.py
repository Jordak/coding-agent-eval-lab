from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from agentlab.execution.commands import git_context_isolated_env
from agentlab.tasks import EvalTask


WORKSPACE_TOKEN = "{workspace}"


def build_task_environment(
    task: EvalTask,
    workspace: Path,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = git_context_isolated_env(os.environ if base_env is None else base_env)
    workspace = workspace.resolve()

    path_entries = [
        _workspace_path(workspace, entry)
        for entry in task.environment_path
    ]
    if path_entries:
        existing_path = env.get("PATH", "")
        path_parts = path_entries + ([existing_path] if existing_path else [])
        env["PATH"] = os.pathsep.join(path_parts)

    for key, value in task.environment.items():
        env[key] = value.replace(WORKSPACE_TOKEN, str(workspace))

    return git_context_isolated_env(env)


def describe_task_environment(task: EvalTask) -> list[str]:
    lines: list[str] = []
    if task.environment_path:
        lines.append(
            "PATH prepends: "
            + ", ".join(f"`{entry}`" for entry in task.environment_path)
        )
    for key, value in sorted(task.environment.items()):
        lines.append(f"{key}={value}")
    return lines


def _workspace_path(workspace: Path, entry: str) -> str:
    return str((workspace / entry).resolve())
