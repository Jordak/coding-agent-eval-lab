import subprocess
from pathlib import Path


class TaskExecutionGitMixin:
    def _repo_with_file(self, root, contents, *, gitignore=None):
        repo = Path(root) / "repo"
        repo.mkdir()
        self._git(["init"], repo)
        self._git(["config", "user.email", "agentlab@example.com"], repo)
        self._git(["config", "user.name", "Agent Lab"], repo)
        if gitignore is not None:
            (repo / ".gitignore").write_text(
                "".join(f"{pattern}\n" for pattern in gitignore),
                encoding="utf-8",
            )
        (repo / "app.txt").write_text(contents, encoding="utf-8")
        self._git(["add", "."], repo)
        self._git(["commit", "-m", "initial"], repo)
        commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
        return repo, commit

    def _git(self, args, cwd, *, input_text=None):
        completed = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            input=input_text,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return completed
