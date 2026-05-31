import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.execution.scoring import CheckResult
from agentlab.execution.phases import TaskActionResult
from agentlab.execution.phases import execute_task_phases
from agentlab.tasks import EvalTask


class TaskExecutionTest(unittest.TestCase):
    def test_runs_task_phases_in_order_and_records_outcome_facts(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="phase-task",
                title="Phase task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change app.txt.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "assert Path('app.txt').read_text() == 'before\\\\n'\""
                ],
                baseline=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "assert Path('app.txt').read_text() == 'before\\\\n'\""
                ],
                test=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "assert Path('app.txt').read_text() == 'after\\\\nnew\\\\n'\""
                ],
            )

            def action(workspace, _task_env):
                (workspace / "app.txt").write_text(
                    "after\nnew\n",
                    encoding="utf-8",
                )
                return TaskActionResult(
                    checks=[CheckResult("apply reference", 0)]
                )

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(
                [check.command for check in execution.all_checks],
                task.setup + task.baseline + ["apply reference"] + task.test,
            )
            self.assertEqual(execution.files_changed, ["app.txt"])
            self.assertEqual(execution.lines_added, 2)
            self.assertEqual(execution.lines_deleted, 1)
            self.assertTrue(execution.diff_path.exists())

    def test_agent_error_makes_grader_outcome_fail(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="agent-error-task",
                title="Agent error task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                lambda _workspace, _task_env: TaskActionResult(
                    agent_error="agent failed"
                ),
                temp_path / "diff.patch",
            )

            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(execution.all_checks, [])
            self.assertEqual(execution.files_changed, [])

    def _repo_with_file(self, root, contents):
        repo = root / "repo"
        repo.mkdir()
        self._git(["init"], repo)
        self._git(["config", "user.email", "agentlab@example.com"], repo)
        self._git(["config", "user.name", "Agent Lab"], repo)
        (repo / "app.txt").write_text(contents, encoding="utf-8")
        self._git(["add", "app.txt"], repo)
        self._git(["commit", "-m", "initial"], repo)
        commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
        return repo, commit

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
