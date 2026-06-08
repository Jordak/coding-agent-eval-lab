import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agentlab.execution.scoring import CheckResult
from agentlab.execution.phases import TaskActionResult
from agentlab.execution.phases import execute_task_phases
from agentlab.tasks import EvalTask
from tests.git_fixtures import commit_file
from tests.git_fixtures import git
from tests.git_fixtures import init_repo


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
                git(["rev-parse", "HEAD"], execution.workspace).stdout.strip(),
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
            git(["commit", "-am", "gold"], repo)
            gold_commit = git(["rev-parse", "HEAD"], repo).stdout.strip()
            git_guard = (
                f"{sys.executable} -c "
                "\"import subprocess; "
                "log = subprocess.check_output("
                "['git', 'log', '--all', '--format=%H'], text=True"
                ").splitlines(); "
                "remotes = subprocess.check_output("
                "['git', 'remote'], text=True"
                ").splitlines(); "
                f"assert {gold_commit!r} not in log, log; "
                "assert len(log) == 1, log; "
                "assert remotes == [], remotes\""
            )
            hostile_config = temp_path / "hostile.gitconfig"
            hostile_config.write_text(
                "\n".join(
                    [
                        '[remote "origin"]',
                        "    url = https://example.com/future.git",
                        "    fetch = +refs/heads/*:refs/remotes/origin/*",
                        "",
                    ]
                ),
                encoding="utf-8",
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
                environment={
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "remote.origin.url",
                    "GIT_CONFIG_VALUE_0": "https://example.com/task-future.git",
                    "GIT_DIR": "/task/hidden.git",
                    "GIT_WORK_TREE": "/task/worktree",
                    "GIT_GRAFT_FILE": "/task/grafts",
                    "GIT_PREFIX": "task-prefix/",
                    "GIT_REPLACE_REF_BASE": "refs/task-replace",
                    "GIT_SHALLOW_FILE": "/task/shallow",
                },
            )

            def action(_workspace, task_env):
                for key in [
                    "GIT_CONFIG_COUNT",
                    "GIT_CONFIG_KEY_0",
                    "GIT_CONFIG_VALUE_0",
                    "GIT_DIR",
                    "GIT_GRAFT_FILE",
                    "GIT_PREFIX",
                    "GIT_REPLACE_REF_BASE",
                    "GIT_SHALLOW_FILE",
                    "GIT_WORK_TREE",
                ]:
                    self.assertNotIn(key, task_env)
                self.assertEqual(task_env["GIT_CONFIG_GLOBAL"], os.devnull)
                self.assertEqual(task_env["GIT_CONFIG_NOSYSTEM"], "1")
                return TaskActionResult()

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_DIR": str(repo / ".git"),
                    "GIT_WORK_TREE": str(repo),
                    "GIT_CONFIG_GLOBAL": str(hostile_config),
                    "GIT_CONFIG_COUNT": "2",
                    "GIT_CONFIG_KEY_0": "remote.origin.url",
                    "GIT_CONFIG_VALUE_0": "https://example.com/future.git",
                    "GIT_CONFIG_KEY_1": "remote.origin.fetch",
                    "GIT_CONFIG_VALUE_1": "+refs/heads/*:refs/remotes/origin/*",
                    "GIT_GRAFT_FILE": str(temp_path / "grafts"),
                    "GIT_PREFIX": "host-prefix/",
                    "GIT_REPLACE_REF_BASE": "refs/host-replace",
                    "GIT_SHALLOW_FILE": str(temp_path / "shallow"),
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
        init_repo(repo)
        commit = commit_file(repo, "app.txt", contents, message="initial")
        return repo, commit


if __name__ == "__main__":
    unittest.main()
