import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
            self.assertEqual(execution.workspace_history_policy, "base_only")
            self.assertEqual(
                self._git(["rev-parse", "HEAD"], execution.workspace).stdout.strip(),
                execution.workspace_base_ref,
            )

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

    def test_task_environment_strips_repo_context_git_env(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, base_commit = self._repo_with_file(temp_path, "base\n")
            (repo / "app.txt").write_text("gold\n", encoding="utf-8")
            self._git(["commit", "-am", "gold"], repo)
            gold_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            git_guard = (
                f"{sys.executable} -c "
                "\"import subprocess; "
                "log = subprocess.check_output("
                "['git', 'log', '--all', '--format=%H'], text=True"
                ").splitlines(); "
                f"assert {gold_commit!r} not in log, log; "
                "assert len(log) == 1, log\""
            )
            task = EvalTask(
                id="git-env-task",
                title="Git env task",
                repo=str(repo),
                commit=base_commit,
                language="text",
                prompt="Do nothing.",
                setup=[git_guard],
                baseline=[git_guard],
                test=[git_guard],
            )

            def action(_workspace, task_env):
                self.assertNotIn("GIT_DIR", task_env)
                self.assertNotIn("GIT_WORK_TREE", task_env)
                return TaskActionResult()

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_DIR": str(repo / ".git"),
                    "GIT_WORK_TREE": str(repo),
                },
            ):
                execution = execute_task_phases(
                    task,
                    temp_path / "workspace",
                    action,
                    temp_path / "diff.patch",
                )

            self.assertTrue(execution.score.tests_passed)
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
