from __future__ import annotations

import subprocess
from pathlib import Path

from agentlab.tasks import EvalTask


GIT_EMAIL = "agentlab@example.com"
GIT_NAME = "Agent Lab"


def git(args: list[str], cwd: Path, input_text: str | None = None):
    completed = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        text=True,
        input=input_text,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed


def init_repo(repo: Path) -> None:
    repo.mkdir()
    git(["init"], repo)
    git(["config", "user.email", GIT_EMAIL], repo)
    git(["config", "user.name", GIT_NAME], repo)


def commit_file(
    repo: Path,
    path: str,
    contents: str,
    *,
    message: str = "commit",
    force: bool = False,
) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents, encoding="utf-8")
    add_args = ["add"]
    if force:
        add_args.append("-f")
    git(add_args + [path], repo)
    git(["commit", "-m", message], repo)
    return head(repo)


def commit_all(repo: Path, message: str) -> str:
    git(["commit", "-am", message], repo)
    return head(repo)


def head(repo: Path) -> str:
    return git(["rev-parse", "HEAD"], repo).stdout.strip()


def eval_task(
    *,
    task_id: str,
    repo: Path | str,
    commit: str,
    title: str = "Fixture task",
    language: str = "text",
    prompt: str = "Do nothing.",
    **overrides,
) -> EvalTask:
    return EvalTask(
        id=task_id,
        title=title,
        repo=str(repo),
        commit=commit,
        language=language,
        prompt=prompt,
        **overrides,
    )


def assert_base_only_repository(testcase, workspace: Path) -> None:
    testcase.assertEqual(
        git(["rev-list", "--count", "HEAD"], workspace).stdout.strip(),
        "1",
    )
    testcase.assertEqual(
        git(
            [
                "for-each-ref",
                "--format=%(refname)",
                "refs/heads",
                "refs/remotes",
                "refs/tags",
            ],
            workspace,
        ).stdout.strip(),
        "",
    )
    testcase.assertFalse((workspace / ".git" / "logs").exists())
