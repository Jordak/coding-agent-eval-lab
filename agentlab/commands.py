from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List, Mapping, Optional

from agentlab.scoring import CheckResult


def run_command(
    command: str,
    cwd: Path,
    timeout_seconds: Optional[int] = None,
    env: Optional[Mapping[str, str]] = None,
) -> CheckResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        env=dict(env) if env is not None else None,
    )
    return CheckResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def run_commands(
    commands: Iterable[str],
    cwd: Path,
    timeout_seconds: Optional[int] = None,
    env: Optional[Mapping[str, str]] = None,
) -> List[CheckResult]:
    return [
        run_command(command, cwd, timeout_seconds, env)
        for command in commands
    ]


def run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
