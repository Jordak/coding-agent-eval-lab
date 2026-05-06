from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from agentlab.scoring import CheckResult


def run_command(command: str, cwd: Path, timeout_seconds: Optional[int] = None) -> CheckResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
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
) -> List[CheckResult]:
    return [run_command(command, cwd, timeout_seconds) for command in commands]


def run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
