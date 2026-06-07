from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List, Mapping, Optional

from agentlab.execution.scoring import CheckResult


_REPO_CONTEXT_ENV_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
}

_GIT_CONFIG_ENV_KEYS = {
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_SYSTEM",
}


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


def run_git(
    args: List[str],
    cwd: Path,
    env: Optional[Mapping[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=dict(env) if env is not None else None,
    )


def run_git_bytes(
    args: List[str],
    cwd: Path,
    env: Optional[Mapping[str, str]] = None,
    input_bytes: Optional[bytes] = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        env=dict(env) if env is not None else None,
        input=input_bytes,
    )


def isolated_git_env(extra: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    if extra:
        env.update(dict(extra))
    return env


def without_repo_context_git_env(env: Mapping[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in env.items()
        if key not in _REPO_CONTEXT_ENV_KEYS
    }


def clone_no_checkout(repo: str, destination: Path) -> subprocess.CompletedProcess[str]:
    env = {
        key: value
        for key, value in without_repo_context_git_env(os.environ).items()
        if not _is_git_config_env_key(key)
    }
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    with tempfile.TemporaryDirectory(prefix="agentlab-empty-template-") as template:
        return run_git(
            [
                "clone",
                "--no-checkout",
                f"--template={template}",
                repo,
                destination.name,
            ],
            cwd=destination.parent,
            env=env,
        )


def _is_git_config_env_key(key: str) -> bool:
    return (
        key in _GIT_CONFIG_ENV_KEYS
        or key.startswith("GIT_CONFIG_KEY_")
        or key.startswith("GIT_CONFIG_VALUE_")
    )
