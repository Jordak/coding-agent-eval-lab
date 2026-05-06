import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.agents.manual import ManualAgentAdapter
from agentlab.runner import run_task
from agentlab.tasks import EvalTask


class RunnerTest(unittest.TestCase):
    def test_manual_run_against_local_git_repo(self):
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

            task = EvalTask(
                id="fixture-task",
                title="Fixture task",
                repo=str(repo),
                commit=commit,
                language="python",
                prompt="Do nothing.",
                test=[f"{sys.executable} -c \"print('ok')\""],
            )

            evaluation = run_task(
                task,
                ManualAgentAdapter(pause=False),
                temp_path / "runs",
            )

            self.assertTrue(evaluation.score.tests_passed)
            self.assertTrue(evaluation.report_path.exists())
            self.assertTrue(evaluation.result_path.exists())
            self.assertTrue(evaluation.agent_run.diff_path.exists())
            self.assertEqual(evaluation.agent_run.files_changed, [])

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
