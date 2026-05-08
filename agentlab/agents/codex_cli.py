from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from agentlab.agents.base import AgentRun
from agentlab.environment import build_task_environment
from agentlab.environment import describe_task_environment
from agentlab.terminal import ProgressBar
from agentlab.tasks import EvalTask


CommandRunner = Callable[[List[str], int], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CodexCliConfig:
    command: str = "codex"
    model: Optional[str] = None
    profile: Optional[str] = None
    sandbox: str = "workspace-write"
    approval_policy: str = "never"
    timeout_seconds: int = 1800
    show_progress: bool = True


class CodexCliAdapter:
    name = "codex"

    def __init__(
        self,
        config: CodexCliConfig | None = None,
        command_runner: CommandRunner | None = None,
    ):
        self.config = config or CodexCliConfig()
        self._command_runner = command_runner

    def run(self, task: EvalTask, workspace: Path, run_dir: Path) -> AgentRun:
        run_dir.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        transcript_path = run_dir / "transcript.md"
        diff_path = run_dir / "diff.patch"
        events_path = run_dir / "codex-events.jsonl"
        last_message_path = run_dir / "codex-last-message.md"

        prompt = _build_prompt(task)
        command = self._build_command(workspace, last_message_path, prompt)
        task_env = build_task_environment(task, workspace)

        error = None
        completed: subprocess.CompletedProcess[str] | None = None
        try:
            completed = self._run_command(
                command,
                self.config.timeout_seconds,
                env=task_env,
            )
        except FileNotFoundError:
            error = _missing_cli_message(self.config.command)
        except subprocess.TimeoutExpired as exc:
            error = f"Codex CLI timed out after {self.config.timeout_seconds}s"
            events_path.write_text(exc.stdout or "", encoding="utf-8")

        if completed is not None:
            events_path.write_text(completed.stdout, encoding="utf-8")
            if completed.returncode != 0:
                error = (
                    f"Codex CLI exited with status {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                ).strip()

        transcript_path.write_text(
            _render_transcript(
                task=task,
                workspace=workspace,
                command=command,
                events_path=events_path,
                last_message_path=last_message_path,
                stderr=completed.stderr if completed else "",
                error=error,
            ),
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
            model_name=self.config.model,
            error=error,
        )

    def _build_command(
        self,
        workspace: Path,
        last_message_path: Path,
        prompt: str,
    ) -> List[str]:
        command = [
            self.config.command,
            "--ask-for-approval",
            self.config.approval_policy,
            "exec",
            "--json",
            "--cd",
            str(workspace),
            "--sandbox",
            self.config.sandbox,
            "--output-last-message",
            str(last_message_path),
        ]
        if self.config.model:
            command.extend(["--model", self.config.model])
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        command.append(prompt)
        return command

    def _run_command(
        self,
        command: List[str],
        timeout_seconds: int,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if self._command_runner:
            return self._command_runner(command, timeout_seconds)

        executable = shutil.which(self.config.command)
        if executable is None:
            raise FileNotFoundError(self.config.command)
        command = [executable] + command[1:]

        progress = ProgressBar("Codex", enabled=self.config.show_progress)
        progress.update("starting agent process")
        try:
            process = subprocess.Popen(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
        except Exception:
            progress.clear()
            raise
        started_at = time.monotonic()

        while True:
            try:
                stdout, stderr = process.communicate(
                    timeout=progress.interval_seconds
                )
                progress.finish("agent process finished")
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                )
            except subprocess.TimeoutExpired:
                elapsed = time.monotonic() - started_at
                if elapsed >= timeout_seconds:
                    process.kill()
                    stdout, stderr = process.communicate()
                    progress.finish("agent process timed out")
                    raise subprocess.TimeoutExpired(
                        command,
                        timeout_seconds,
                        output=stdout,
                        stderr=stderr,
                    )
                progress.update("waiting for agent response")


def _missing_cli_message(command: str) -> str:
    return (
        f"Codex CLI not found: {command}. Make the executable discoverable on "
        "PATH, or pass --codex-command /path/to/codex for a nonstandard "
        "installation."
    )


def _build_prompt(task: EvalTask) -> str:
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
    if task.test:
        lines.extend(["Validation commands that will be run after you finish:"])
        lines.extend(f"- {command}" for command in task.test)
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


def _render_transcript(
    task: EvalTask,
    workspace: Path,
    command: List[str],
    events_path: Path,
    last_message_path: Path,
    stderr: str,
    error: str | None,
) -> str:
    last_message = ""
    if last_message_path.exists():
        last_message = last_message_path.read_text(encoding="utf-8").strip()

    lines = [
        f"# Codex CLI Run: {task.id}",
        "",
        f"Workspace: `{workspace}`",
        f"Events: `{events_path.name}`",
        f"Last message: `{last_message_path.name}`",
        "",
        "## Command",
        "",
        "```text",
        " ".join(command[:-1] + ["<prompt>"]),
        "```",
        "",
    ]
    if error:
        lines.extend(["## Error", "", "```text", error, "```", ""])
    if stderr.strip():
        lines.extend(["## Stderr", "", "```text", stderr.strip(), "```", ""])
    if last_message:
        lines.extend(["## Final Message", "", last_message, ""])
    return "\n".join(lines)
