import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agentlab.tasks import EvalTask
from agentlab.workspace import prepare_workspace


class WorkspaceTest(unittest.TestCase):
    def test_prepare_workspace_accepts_relative_root(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "README.md").write_text("# Fixture\n", encoding="utf-8")
            self._git(["add", "README.md"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            original_cwd = Path.cwd()
            try:
                # Reproduce CLI behavior where runs-dir is provided as a relative path.
                import os

                os.chdir(temp_path)
                task = EvalTask(
                    id="fixture-task",
                    title="Fixture task",
                    repo=str(repo),
                    commit=commit,
                    language="python",
                    prompt="Do nothing.",
                )

                prepared = prepare_workspace(task, Path("runs/relative-root"))
            finally:
                os.chdir(original_cwd)

            self.assertTrue(prepared.path.exists())
            self.assertEqual(
                self._git(["rev-parse", "HEAD"], prepared.path).stdout.strip(),
                commit,
            )

    def _git(self, args, cwd):
        completed = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return completed


if __name__ == "__main__":
    unittest.main()
