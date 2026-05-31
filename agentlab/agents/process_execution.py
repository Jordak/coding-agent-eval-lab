from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from agentlab.terminal import ProgressBar


AgentProcessRunner = Callable[
    ["AgentProcessRequest"],
    subprocess.CompletedProcess[str],
]


@dataclass(frozen=True)
class AgentProcessRequest:
    """Common lifecycle settings for a command-based agent adapter."""

    command: List[str]
    executable_name: str
    timeout_seconds: int
    stdout_path: Path
    progress_label: str
    show_progress: bool = True
    cwd: Path | None = None
    env: dict[str, str] | None = None
    progress_interval_seconds: float = 0.5


def run_agent_process(
    request: AgentProcessRequest,
    *,
    runner: AgentProcessRunner | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run an agent command and persist captured stdout to its event artifact."""

    try:
        if runner is not None:
            completed = runner(request)
        else:
            completed = _run_subprocess(request)
    except subprocess.TimeoutExpired as exc:
        _write_stdout_artifact(request.stdout_path, timeout_stdout(exc))
        raise

    _write_stdout_artifact(request.stdout_path, completed.stdout)
    return completed


def timeout_stdout(exc: subprocess.TimeoutExpired) -> str:
    return _coerce_text(exc.stdout or exc.output or "")


def _run_subprocess(
    request: AgentProcessRequest,
) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(request.executable_name)
    if executable is None:
        raise FileNotFoundError(request.executable_name)
    command = [executable] + request.command[1:]

    progress = ProgressBar(
        request.progress_label,
        enabled=request.show_progress,
        interval_seconds=request.progress_interval_seconds,
    )
    progress.update("starting agent process")
    try:
        process = subprocess.Popen(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(request.cwd) if request.cwd is not None else None,
            env=request.env,
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
            if elapsed >= request.timeout_seconds:
                process.kill()
                stdout, stderr = process.communicate()
                progress.finish("agent process timed out")
                raise subprocess.TimeoutExpired(
                    command,
                    request.timeout_seconds,
                    output=stdout,
                    stderr=stderr,
                )
            progress.update("waiting for agent response")


def _write_stdout_artifact(path: Path, stdout: object) -> None:
    path.write_text(_coerce_text(stdout), encoding="utf-8")


def _coerce_text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""
