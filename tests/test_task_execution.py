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
from agentlab.tasks import EvalTask, HiddenVerifier, SuccessCriteria
from tests.task_execution_helpers import TaskExecutionGitMixin


class TaskExecutionTest(TaskExecutionGitMixin, unittest.TestCase):
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

    def test_hidden_verifier_runs_after_model_diff_and_restores_workspace(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task_file = _hidden_task_file(
                temp_path,
                _new_file_patch(
                    "hidden_check.py",
                    [
                        "import subprocess",
                        "from pathlib import Path",
                        "subprocess.run(['git', 'config', 'hidden.verifier', 'true'], check=True)",
                        "assert Path('app.txt').read_text() == 'after\\n'",
                    ],
                ),
            )
            hidden_command = f"{sys.executable} hidden_check.py"
            task = EvalTask(
                id="hidden-success-task",
                title="Hidden success task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change app.txt.",
                hidden_verifier=HiddenVerifier(
                    patch="verifier.patch",
                    commands=[hidden_command],
                ),
                success=SuccessCriteria(tests_must_pass=False),
                source_path=task_file,
            )

            def action(workspace, _task_env):
                (workspace / "app.txt").write_text("after\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.files_changed, ["app.txt"])
            self.assertEqual(execution.lines_added, 1)
            self.assertEqual(execution.lines_deleted, 1)
            self.assertFalse((execution.workspace / "hidden_check.py").exists())
            config_check = self._git(
                ["config", "--get", "hidden.verifier"],
                execution.workspace,
                check=False,
            )
            self.assertNotEqual(config_check.returncode, 0)
            self.assertTrue(execution.hidden_verifier.configured)
            self.assertEqual(
                [check.command for check in execution.hidden_verifier.checks],
                [
                    "git apply hidden verifier patch: verifier.patch",
                    hidden_command,
                ],
            )
            self.assertEqual(execution.all_checks, [])

    def test_visible_test_tampering_cannot_substitute_for_hidden_verifier(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("broken\n", encoding="utf-8")
            (repo / "visible_test.py").write_text(
                "raise SystemExit('visible test still expects a fix')\n",
                encoding="utf-8",
            )
            self._git(["add", "."], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            task_file = _hidden_task_file(
                temp_path,
                _new_file_patch(
                    "hidden_check.py",
                    [
                        "from pathlib import Path",
                        "assert Path('app.txt').read_text() == 'fixed\\n'",
                    ],
                ),
            )
            visible_command = f"{sys.executable} visible_test.py"
            hidden_command = f"{sys.executable} hidden_check.py"
            task = EvalTask(
                id="hidden-fail-task",
                title="Hidden fail task",
                repo=str(repo),
                commit=commit,
                language="python",
                prompt="Fix app.txt.",
                test=[visible_command],
                hidden_verifier=HiddenVerifier(
                    patch="verifier.patch",
                    commands=[hidden_command],
                ),
                source_path=task_file,
            )

            def action(workspace, _task_env):
                (workspace / "visible_test.py").write_text(
                    "print('visible test bypassed')\n",
                    encoding="utf-8",
                )
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertFalse(execution.score.tests_passed)
            self.assertTrue(execution.target_checks[0].passed)
            self.assertFalse(execution.hidden_verifier.checks[1].passed)
            self.assertEqual(execution.files_changed, ["visible_test.py"])
            self.assertFalse((execution.workspace / "hidden_check.py").exists())

    def test_restore_failure_fails_hidden_verifier_and_skips_target_checks(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task_file = _hidden_task_file(
                temp_path,
                _new_file_patch(
                    "hidden_check.py",
                    ["print('hidden ok')"],
                ),
            )
            target_command = f"{sys.executable} -c \"print('target should skip')\""
            task = EvalTask(
                id="hidden-restore-fail-task",
                title="Hidden restore fail task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                test=[target_command],
                hidden_verifier=HiddenVerifier(
                    patch="verifier.patch",
                    commands=[f"{sys.executable} hidden_check.py"],
                ),
                source_path=task_file,
            )

            with mock.patch(
                "agentlab.execution.hidden_verifier._replace_worktree_contents",
                side_effect=OSError("boom"),
            ):
                execution = execute_task_phases(
                    task,
                    temp_path / "workspace",
                    lambda _workspace, _task_env: TaskActionResult(),
                    temp_path / "diff.patch",
                )

            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(execution.target_checks, [])
            self.assertEqual(
                execution.hidden_verifier.checks[-1].command,
                "restore hidden verifier workspace",
            )
            self.assertFalse(execution.hidden_verifier.checks[-1].passed)
            self.assertEqual(
                execution.hidden_verifier.restore_notes,
                ["failed to restore hidden verifier worktree: boom"],
            )

    def test_hidden_verifier_patch_apply_failure_fails_without_commands(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task_file = _hidden_task_file(
                temp_path,
                "\n".join(
                    [
                        "diff --git a/app.txt b/app.txt",
                        "--- a/app.txt",
                        "+++ b/app.txt",
                        "@@ -1 +1 @@",
                        "-missing",
                        "+hidden",
                        "",
                    ]
                ),
            )
            hidden_command = f"{sys.executable} -c \"raise SystemExit('no')\""
            task = EvalTask(
                id="hidden-apply-fail-task",
                title="Hidden apply fail task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                hidden_verifier=HiddenVerifier(
                    patch="verifier.patch",
                    commands=[hidden_command],
                ),
                source_path=task_file,
            )

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                lambda _workspace, _task_env: TaskActionResult(),
                temp_path / "diff.patch",
            )

            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(len(execution.hidden_verifier.checks), 1)
            self.assertFalse(execution.hidden_verifier.checks[0].passed)
            self.assertEqual(
                (execution.workspace / "app.txt").read_text(encoding="utf-8"),
                "before\n",
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


def _hidden_task_file(root: Path, verifier_patch: str) -> Path:
    bundle = root / "bundle"
    bundle.mkdir(exist_ok=True)
    task_file = bundle / "task.yaml"
    task_file.write_text("id: hidden-task\n", encoding="utf-8")
    (bundle / "verifier.patch").write_text(verifier_patch, encoding="utf-8")
    return task_file


def _new_file_patch(path: str, lines: list[str]) -> str:
    added = "\n".join(f"+{line}" for line in lines)
    return "\n".join(
        [
            f"diff --git a/{path} b/{path}",
            "new file mode 100644",
            "--- /dev/null",
            f"+++ b/{path}",
            f"@@ -0,0 +1,{len(lines)} @@",
            added,
            "",
        ]
    )


if __name__ == "__main__":
    unittest.main()
