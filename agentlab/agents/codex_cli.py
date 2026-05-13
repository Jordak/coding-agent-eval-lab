from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agentlab.agent_harness_config import normalize_agent_harness_config
from agentlab.agents.base import AgentRun
from agentlab.agents.prompts import build_agent_prompt
from agentlab.codex_runtime_metadata import (
    codex_model_identity_from_events_and_state,
    default_codex_state_db_path,
)
from agentlab.environment import build_task_environment
from agentlab.model_identity import ModelIdentity
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
    codex_state_db: Path | None = None


@dataclass(frozen=True)
class CodexRuntimeFacts:
    command_identity: str | None = None
    cli_version: str | None = None


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

        prompt = build_agent_prompt(task)
        command = self._build_command(workspace, last_message_path, prompt)
        task_env = build_task_environment(task, workspace)
        runtime_facts = self._collect_runtime_facts()

        error = None
        completed: subprocess.CompletedProcess[str] | None = None
        events_text = ""
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
            events_text = exc.stdout or ""
            events_path.write_text(events_text, encoding="utf-8")

        if completed is not None:
            events_text = completed.stdout
            events_path.write_text(events_text, encoding="utf-8")
            usage = parse_resource_usage_events(events_text)
            if completed.returncode != 0:
                error = (
                    f"Codex CLI exited with status {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                ).strip()
        else:
            usage = ResourceUsage()
        model_identity = codex_model_identity_from_events_and_state(
            events_text,
            requested_model_name=self.config.model,
            codex_state_db=self._codex_state_db_path(),
        )

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
            model_name=model_identity.model_name,
            agent_harness_config=codex_agent_harness_config(
                self.config,
                runtime_facts=runtime_facts,
                model_identity=model_identity,
                cost_usd=usage.cost_usd,
            ),
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

    def _collect_runtime_facts(self) -> CodexRuntimeFacts:
        if self._command_runner:
            return CodexRuntimeFacts()
        executable = shutil.which(self.config.command)
        if executable is None:
            return CodexRuntimeFacts()
        return CodexRuntimeFacts(
            command_identity=str(Path(executable).resolve()),
            cli_version=_codex_cli_version(executable),
        )

    def _codex_state_db_path(self) -> Path | None:
        if self.config.codex_state_db is not None:
            return Path(self.config.codex_state_db).expanduser()
        default_path = default_codex_state_db_path()
        if default_path.is_file():
            return default_path
        return None


def _missing_cli_message(command: str) -> str:
    return (
        f"Codex CLI not found: {command}. Make the executable discoverable on "
        "PATH, or pass --codex-command /path/to/codex for a nonstandard "
        "installation."
    )


def codex_agent_harness_config(
    config: CodexCliConfig,
    *,
    runtime_facts: CodexRuntimeFacts | None = None,
    model_identity: ModelIdentity | None = None,
    cost_usd: float | None = None,
) -> Dict[str, Any]:
    runtime_facts = runtime_facts or CodexRuntimeFacts()
    model_identity = model_identity or codex_model_identity_from_events_and_state(
        "",
        requested_model_name=config.model,
    )
    return normalize_agent_harness_config(
        {
            "agent_harness": "codex",
            "agent_adapter": "codex_cli",
            "command": config.command,
            "command_identity": runtime_facts.command_identity,
            "model_name": model_identity.model_name,
            "model_source": model_identity.model_source,
            "requested_model_name": model_identity.requested_model_name,
            "reasoning_effort": model_identity.reasoning_effort,
            "model_provider": model_identity.model_provider,
            "codex_thread_id": model_identity.codex_thread_id,
            "codex_thread_source": model_identity.codex_thread_source,
            "profile": config.profile,
            "sandbox": config.sandbox,
            "approval_policy": config.approval_policy,
            "timeout_seconds": config.timeout_seconds,
            "cli_version": runtime_facts.cli_version,
        },
        agent_name="codex",
        model_name=model_identity.model_name,
        cost_usd=cost_usd,
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
            agent_harness_config=codex_agent_harness_config(config),
        )

    checks = [
        PreflightCheck(
            name="Codex executable",
            passed=True,
            command=[config.command],
            message=f"found {executable}",
        )
    ]
    version_check = _run_preflight_command(
        name="Codex version",
        command=[executable, "--version"],
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
    )
    checks.append(version_check)
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
    return PreflightResult(
        agent_name="codex",
        checks=checks,
        agent_harness_config=codex_agent_harness_config(
            config,
            runtime_facts=CodexRuntimeFacts(
                command_identity=str(Path(executable).resolve()),
                cli_version=_preflight_cli_version(version_check),
            ),
        ),
    )


def _codex_cli_version(executable: str) -> str | None:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            text=True,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return _first_output_line(completed.stdout, completed.stderr) or None


def _preflight_cli_version(check: PreflightCheck) -> str | None:
    if not check.passed:
        return None
    return _first_output_line(check.stdout, check.stderr) or None


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
