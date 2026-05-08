from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from agentlab.agents.base import AgentRun
from agentlab.environment import build_task_environment
from agentlab.environment import describe_task_environment
from agentlab.preflight import PreflightCheck, PreflightResult
from agentlab.resource_usage import ResourceUsage, parse_resource_usage_events
from agentlab.terminal import ProgressBar
from agentlab.tasks import EvalTask


CommandRunner = Callable[[List[str], int], subprocess.CompletedProcess[str]]
PreflightRunner = Callable[[List[str], int], subprocess.CompletedProcess[str]]


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
            usage = parse_resource_usage_events(completed.stdout)
            if completed.returncode != 0:
                error = (
                    f"Codex CLI exited with status {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                ).strip()
        else:
            usage = ResourceUsage()

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
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            output_tokens=usage.output_tokens,
            reasoning_output_tokens=usage.reasoning_output_tokens,
            cost_usd=usage.cost_usd,
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


def run_codex_preflight(
    config: CodexCliConfig,
    timeout_seconds: int = 15,
    command_runner: PreflightRunner | None = None,
) -> PreflightResult:
    executable = shutil.which(config.command)
    if executable is None:
        return PreflightResult(
            agent_name="codex",
            checks=[
                PreflightCheck(
                    name="Codex executable",
                    passed=False,
                    command=[config.command],
                    message=_missing_cli_message(config.command),
                )
            ],
        )

    checks = [
        PreflightCheck(
            name="Codex executable",
            passed=True,
            command=[config.command],
            message=f"found {executable}",
        )
    ]
    checks.append(
        _run_preflight_command(
            name="Codex version",
            command=[executable, "--version"],
            timeout_seconds=timeout_seconds,
            command_runner=command_runner,
        )
    )
    with tempfile.TemporaryDirectory(prefix="agentlab-codex-preflight-") as temp:
        temp_path = Path(temp)
        checks.append(
            _run_preflight_command(
                name="Codex exec command shape",
                command=_build_preflight_exec_help_command(
                    config,
                    executable,
                    temp_path,
                ),
                timeout_seconds=timeout_seconds,
                command_runner=command_runner,
            )
        )
    return PreflightResult(agent_name="codex", checks=checks)


def _build_preflight_exec_help_command(
    config: CodexCliConfig,
    executable: str,
    workspace: Path,
) -> List[str]:
    adapter = CodexCliAdapter(config)
    trial_command = adapter._build_command(
        workspace,
        workspace / "codex-last-message.md",
        "__agentlab_preflight__",
    )
    return [executable] + trial_command[1:-1] + ["--help"]


def _run_preflight_command(
    name: str,
    command: List[str],
    timeout_seconds: int,
    command_runner: PreflightRunner | None,
) -> PreflightCheck:
    try:
        if command_runner:
            completed = command_runner(command, timeout_seconds)
        else:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
    except subprocess.TimeoutExpired as exc:
        return PreflightCheck(
            name=name,
            passed=False,
            command=command,
            message=f"timed out after {timeout_seconds}s",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        )
    except OSError as exc:
        return PreflightCheck(
            name=name,
            passed=False,
            command=command,
            message=str(exc),
        )

    output = _first_output_line(completed.stdout, completed.stderr)
    if completed.returncode == 0:
        return PreflightCheck(
            name=name,
            passed=True,
            command=command,
            message=output or "ok",
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    detail = output or "no output"
    return PreflightCheck(
        name=name,
        passed=False,
        command=command,
        message=f"exited with status {completed.returncode}: {detail}",
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _first_output_line(stdout: str, stderr: str) -> str:
    output = (stdout or "").strip() or (stderr or "").strip()
    if not output:
        return ""
    return output.splitlines()[0]


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
