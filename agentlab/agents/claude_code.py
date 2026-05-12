from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from agentlab.agent_harness_config import normalize_agent_harness_config
from agentlab.agents.base import AgentRun
from agentlab.agents.prompts import build_agent_prompt
from agentlab.environment import build_task_environment
from agentlab.model_identity import ModelIdentity, model_identity_from_events
from agentlab.preflight import PreflightCheck, PreflightResult
from agentlab.resource_usage import ResourceUsage
from agentlab.terminal import ProgressBar
from agentlab.tasks import EvalTask


CommandRunner = Callable[
    [List[str], int, Path, dict[str, str]],
    subprocess.CompletedProcess[str],
]
PreflightRunner = Callable[[List[str], int], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ClaudeCodeConfig:
    command: str = "claude"
    model: Optional[str] = None
    permission_mode: str = "acceptEdits"
    output_format: str = "stream-json"
    max_turns: Optional[int] = None
    allowed_tools: tuple[str, ...] = ()
    disallowed_tools: tuple[str, ...] = ()
    timeout_seconds: int = 1800
    show_progress: bool = True
    no_session_persistence: bool = True


@dataclass(frozen=True)
class ClaudeCodeRuntimeFacts:
    command_identity: str | None = None
    cli_version: str | None = None
    auth_status: str | None = None


class ClaudeCodeAdapter:
    name = "claude"

    def __init__(
        self,
        config: ClaudeCodeConfig | None = None,
        command_runner: CommandRunner | None = None,
    ):
        self.config = config or ClaudeCodeConfig()
        self._command_runner = command_runner

    def run(self, task: EvalTask, workspace: Path, run_dir: Path) -> AgentRun:
        run_dir.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        transcript_path = run_dir / "transcript.md"
        diff_path = run_dir / "diff.patch"
        events_path = run_dir / "claude-events.jsonl"
        final_message_path = run_dir / "claude-final-message.md"

        prompt = build_agent_prompt(task)
        command = self._build_command(prompt)
        task_env = build_task_environment(task, workspace)
        runtime_facts = self._collect_runtime_facts()

        error = None
        completed: subprocess.CompletedProcess[str] | None = None
        final_message = ""
        usage = ResourceUsage()
        events_text = ""
        try:
            completed = self._run_command(
                command,
                self.config.timeout_seconds,
                workspace=workspace,
                env=task_env,
            )
        except FileNotFoundError:
            error = _missing_cli_message(self.config.command)
        except subprocess.TimeoutExpired as exc:
            error = f"Claude Code CLI timed out after {self.config.timeout_seconds}s"
            events_text = _coerce_text(exc.stdout or exc.output or "")
            events_path.write_text(events_text, encoding="utf-8")

        if completed is not None:
            events_text = completed.stdout
            events_path.write_text(events_text, encoding="utf-8")
            final_message = _extract_final_message(
                events_text,
                output_format=self.config.output_format,
            )
            usage = _parse_claude_resource_usage(events_text)
            if completed.returncode != 0:
                detail = _first_output_line(completed.stderr, completed.stdout)
                error = (
                    f"Claude Code CLI exited with status {completed.returncode}: "
                    f"{detail}"
                ).strip()
        elif not events_path.exists():
            events_path.write_text("", encoding="utf-8")
        model_identity = model_identity_from_events(
            events_text,
            requested_model_name=self.config.model,
        )

        final_message_path.write_text(final_message, encoding="utf-8")
        transcript_path.write_text(
            _render_transcript(
                task=task,
                workspace=workspace,
                command=command,
                events_path=events_path,
                final_message_path=final_message_path,
                stderr=completed.stderr if completed else "",
                error=error,
                final_message=final_message,
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
            agent_harness_config=claude_code_agent_harness_config(
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

    def _build_command(self, prompt: str) -> List[str]:
        command = [
            self.config.command,
            "-p",
            prompt,
            "--output-format",
            self.config.output_format,
            "--permission-mode",
            self.config.permission_mode,
        ]
        if self.config.output_format == "stream-json":
            command.append("--verbose")
        if self.config.model:
            command.extend(["--model", self.config.model])
        if self.config.max_turns is not None:
            command.extend(["--max-turns", str(self.config.max_turns)])
        for tool in self.config.allowed_tools:
            command.extend(["--allowedTools", tool])
        for tool in self.config.disallowed_tools:
            command.extend(["--disallowedTools", tool])
        if self.config.no_session_persistence:
            command.append("--no-session-persistence")
        return command

    def _run_command(
        self,
        command: List[str],
        timeout_seconds: int,
        *,
        workspace: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        if self._command_runner:
            return self._command_runner(command, timeout_seconds, workspace, env)

        executable = shutil.which(self.config.command)
        if executable is None:
            raise FileNotFoundError(self.config.command)
        command = [executable] + command[1:]

        progress = ProgressBar("Claude", enabled=self.config.show_progress)
        progress.update("starting agent process")
        try:
            process = subprocess.Popen(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(workspace),
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

    def _collect_runtime_facts(self) -> ClaudeCodeRuntimeFacts:
        if self._command_runner:
            return ClaudeCodeRuntimeFacts()
        executable = shutil.which(self.config.command)
        if executable is None:
            return ClaudeCodeRuntimeFacts()
        version = _claude_cli_version(executable)
        auth_status = _claude_auth_status(executable)
        return ClaudeCodeRuntimeFacts(
            command_identity=str(Path(executable).resolve()),
            cli_version=version,
            auth_status=auth_status,
        )


def _missing_cli_message(command: str) -> str:
    return (
        f"Claude Code CLI not found: {command}. Make the executable discoverable "
        "on PATH, or pass --claude-command /path/to/claude for a nonstandard "
        "installation."
    )


def claude_code_agent_harness_config(
    config: ClaudeCodeConfig,
    *,
    runtime_facts: ClaudeCodeRuntimeFacts | None = None,
    model_identity: ModelIdentity | None = None,
    cost_usd: float | None = None,
) -> Dict[str, Any]:
    runtime_facts = runtime_facts or ClaudeCodeRuntimeFacts()
    model_identity = model_identity or model_identity_from_events(
        "",
        requested_model_name=config.model,
    )
    return normalize_agent_harness_config(
        {
            "agent_harness": "claude_code",
            "agent_adapter": "claude_code_cli",
            "command": config.command,
            "command_identity": runtime_facts.command_identity,
            "model_name": model_identity.model_name,
            "model_source": model_identity.model_source,
            "requested_model_name": model_identity.requested_model_name,
            "permission_mode": config.permission_mode,
            "output_format": config.output_format,
            "max_turns": config.max_turns,
            "allowed_tools": list(config.allowed_tools),
            "disallowed_tools": list(config.disallowed_tools),
            "timeout_seconds": config.timeout_seconds,
            "no_session_persistence": config.no_session_persistence,
            "cli_version": runtime_facts.cli_version,
            "auth_status": runtime_facts.auth_status,
        },
        agent_name="claude",
        model_name=model_identity.model_name,
        cost_usd=cost_usd,
    )


def run_claude_code_preflight(
    config: ClaudeCodeConfig,
    timeout_seconds: int = 15,
    command_runner: PreflightRunner | None = None,
) -> PreflightResult:
    executable = shutil.which(config.command)
    if executable is None:
        return PreflightResult(
            agent_name="claude",
            checks=[
                PreflightCheck(
                    name="Claude Code executable",
                    passed=False,
                    command=[config.command],
                    message=_missing_cli_message(config.command),
                )
            ],
            agent_harness_config=claude_code_agent_harness_config(config),
        )

    checks = [
        PreflightCheck(
            name="Claude Code executable",
            passed=True,
            command=[config.command],
            message=f"found {executable}",
        )
    ]
    version_check = _run_preflight_command(
        name="Claude Code version",
        command=[executable, "--version"],
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
    )
    checks.append(version_check)
    auth_check = _run_preflight_command(
        name="Claude Code auth",
        command=[executable, "auth", "status"],
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
    )
    auth_check = _with_message(auth_check, _format_claude_auth_status(auth_check))
    checks.append(auth_check)
    checks.append(
        _run_preflight_command(
            name="Claude Code print command shape",
            command=_build_preflight_print_help_command(config, executable),
            timeout_seconds=timeout_seconds,
            command_runner=command_runner,
        )
    )

    return PreflightResult(
        agent_name="claude",
        checks=checks,
        agent_harness_config=claude_code_agent_harness_config(
            config,
            runtime_facts=ClaudeCodeRuntimeFacts(
                command_identity=str(Path(executable).resolve()),
                cli_version=_preflight_cli_version(version_check),
                auth_status=_preflight_auth_status(auth_check),
            ),
        ),
    )


def _build_preflight_print_help_command(
    config: ClaudeCodeConfig,
    executable: str,
) -> List[str]:
    adapter = ClaudeCodeAdapter(config)
    command = adapter._build_command("__agentlab_preflight__")
    return [executable] + command[1:] + ["--help"]


def _claude_cli_version(executable: str) -> str | None:
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


def _claude_auth_status(executable: str) -> str | None:
    try:
        completed = subprocess.run(
            [executable, "auth", "status"],
            text=True,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return _format_claude_auth_status(
        PreflightCheck(
            name="Claude Code auth",
            passed=True,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    )


def _preflight_cli_version(check: PreflightCheck) -> str | None:
    if not check.passed:
        return None
    return _first_output_line(check.stdout, check.stderr) or None


def _preflight_auth_status(check: PreflightCheck) -> str | None:
    if not check.passed:
        return None
    return _format_claude_auth_status(check) or "ok"


def _format_claude_auth_status(check: PreflightCheck) -> str:
    if not check.passed:
        return check.message
    output = (check.stdout or "").strip()
    if not output:
        return _first_output_line(check.stdout, check.stderr) or "ok"
    try:
        status = json.loads(output)
    except json.JSONDecodeError:
        return _first_output_line(check.stdout, check.stderr) or "ok"
    if not isinstance(status, dict):
        return "ok"
    fields = []
    if "loggedIn" in status:
        fields.append(f"loggedIn={str(status.get('loggedIn')).lower()}")
    if status.get("authMethod"):
        fields.append(f"authMethod={status.get('authMethod')}")
    if status.get("apiProvider"):
        fields.append(f"apiProvider={status.get('apiProvider')}")
    return " ".join(fields) or "ok"


def _with_message(check: PreflightCheck, message: str) -> PreflightCheck:
    return PreflightCheck(
        name=check.name,
        passed=check.passed,
        command=check.command,
        message=message,
        returncode=check.returncode,
        stdout=check.stdout,
        stderr=check.stderr,
    )


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
            stdout=_coerce_text(exc.stdout or exc.output or ""),
            stderr=_coerce_text(exc.stderr or ""),
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


def _extract_final_message(output: str, *, output_format: str) -> str:
    if output_format == "text":
        return output.strip()

    final_message = ""
    for event in _iter_json_messages(output):
        if event.get("type") == "result":
            result = event.get("result")
            if isinstance(result, str):
                final_message = result.strip()
        elif event.get("type") == "assistant":
            text = _assistant_text(event)
            if text:
                final_message = text
    return final_message


def _assistant_text(event: dict[str, Any]) -> str:
    message = event.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    parts = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    return "\n".join(part for part in parts if part).strip()


def _parse_claude_resource_usage(output: str) -> ResourceUsage:
    assistant_totals: dict[str, int] = {}
    seen_message_ids: set[str] = set()
    result_usage: dict[str, Any] | None = None
    cost_usd: float | None = None

    for event in _iter_json_messages(output):
        if event.get("type") == "result":
            usage = event.get("usage")
            if isinstance(usage, dict):
                result_usage = usage
            value = event.get("total_cost_usd", event.get("cost_usd"))
            if isinstance(value, (int, float)):
                cost_usd = float(value)
            continue

        if event.get("type") != "assistant":
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        message_id = message.get("id")
        if isinstance(message_id, str):
            if message_id in seen_message_ids:
                continue
            seen_message_ids.add(message_id)
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        for key in [
            "input_tokens",
            "cache_read_input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
        ]:
            value = usage.get(key)
            if isinstance(value, int):
                assistant_totals[key] = assistant_totals.get(key, 0) + value

    usage = result_usage or assistant_totals
    return ResourceUsage(
        input_tokens=_int_value(usage, "input_tokens"),
        cached_input_tokens=(
            _int_value(usage, "cached_input_tokens")
            or _int_value(usage, "cache_read_input_tokens")
        ),
        output_tokens=_int_value(usage, "output_tokens"),
        reasoning_output_tokens=_int_value(usage, "reasoning_output_tokens"),
        cost_usd=cost_usd,
    )


def _iter_json_messages(output: str) -> Iterable[dict[str, Any]]:
    stripped = output.strip()
    if not stripped:
        return

    if "\n" not in stripped:
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            return
        if isinstance(event, dict):
            yield event
        return

    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def _int_value(values: dict[str, Any], key: str) -> int | None:
    value = values.get(key)
    if isinstance(value, int):
        return value
    return None


def _first_output_line(stdout: str, stderr: str) -> str:
    output = (stdout or "").strip() or (stderr or "").strip()
    if not output:
        return ""
    return output.splitlines()[0]


def _coerce_text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""


def _redacted_command(command: List[str]) -> List[str]:
    if len(command) >= 3 and command[1] in {"-p", "--print"}:
        return command[:2] + ["<prompt>"] + command[3:]
    return command


def _render_transcript(
    task: EvalTask,
    workspace: Path,
    command: List[str],
    events_path: Path,
    final_message_path: Path,
    stderr: str,
    error: str | None,
    final_message: str,
) -> str:
    lines = [
        f"# Claude Code Run: {task.id}",
        "",
        f"Workspace: `{workspace}`",
        f"Events: `{events_path.name}`",
        f"Final message: `{final_message_path.name}`",
        "",
        "## Command",
        "",
        "```text",
        " ".join(_redacted_command(command)),
        "```",
        "",
    ]
    if error:
        lines.extend(["## Error", "", "```text", error, "```", ""])
    if stderr.strip():
        lines.extend(["## Stderr", "", "```text", stderr.strip(), "```", ""])
    if final_message:
        lines.extend(["## Final Message", "", final_message, ""])
    return "\n".join(lines)
