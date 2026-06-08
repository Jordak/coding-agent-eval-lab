import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agentlab.execution.phases import TaskActionResult
from agentlab.execution.phases import execute_task_phases
from agentlab.tasks import EvalTask, SuccessCriteria
from tests.task_execution_helpers import TaskExecutionGitMixin


class TaskExecutionBoundaryChangeTest(TaskExecutionGitMixin, unittest.TestCase):
    def test_host_git_env_does_not_hide_untracked_boundary_violation(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="host-git-env-boundary-task",
                title="Host git env boundary task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not create forbidden.txt.",
                success=SuccessCriteria(forbidden_paths=["forbidden.txt"]),
            )

            def action(workspace, _task_env):
                (workspace / "forbidden.txt").write_text(
                    "secret\n",
                    encoding="utf-8",
                )
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

            self.assertEqual(execution.files_changed, ["forbidden.txt"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `forbidden.txt` "
                    "matches forbidden_paths pattern `forbidden.txt`"
                ],
            )

    def test_modified_setup_created_untracked_file_counts_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="modified-setup-untracked-task",
                title="Modified setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change setup.log.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(forbidden_paths=["setup.log"]),
            )

            def action(workspace, _task_env):
                (workspace / "setup.log").write_text(
                    "setup\nagent change\n",
                    encoding="utf-8",
                )
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["setup.log"])
            self.assertEqual(
                execution.setup_created_untracked_changed_paths,
                ["setup.log"],
            )
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `setup.log` "
                    "matches forbidden_paths pattern `setup.log`"
                ],
            )

    def test_staged_only_setup_created_untracked_change_counts_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="staged-setup-created-untracked-change-task",
                title="Staged setup-created untracked change task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change setup.log.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(forbidden_paths=["setup.log"]),
            )

            def action(workspace, _task_env):
                setup_log = workspace / "setup.log"
                setup_log.write_text(
                    "setup\nagent staged change\n",
                    encoding="utf-8",
                )
                self._git(["add", "setup.log"], workspace)
                setup_log.write_text("setup\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["setup.log"])
            self.assertEqual(
                execution.setup_created_untracked_changed_paths,
                ["setup.log"],
            )
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `setup.log` "
                    "matches forbidden_paths pattern `setup.log`"
                ],
            )

    def test_modified_ignored_setup_created_untracked_file_counts(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(
                temp_path,
                "before\n",
                gitignore=["setup.log"],
            )
            task = EvalTask(
                id="modified-ignored-setup-untracked-task",
                title="Modified ignored setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change setup.log.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(forbidden_paths=["setup.log"]),
            )

            def action(workspace, _task_env):
                (workspace / "setup.log").write_text(
                    "setup\nagent change\n",
                    encoding="utf-8",
                )
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["setup.log"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `setup.log` "
                    "matches forbidden_paths pattern `setup.log`"
                ],
            )

    def test_deleted_setup_created_untracked_file_counts_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="deleted-setup-untracked-task",
                title="Deleted setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not delete setup.log.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(forbidden_paths=["setup.log"]),
            )

            def action(workspace, _task_env):
                (workspace / "setup.log").unlink()
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["setup.log"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `setup.log` "
                    "matches forbidden_paths pattern `setup.log`"
                ],
            )

    def test_deleted_ignored_setup_created_untracked_file_counts(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(
                temp_path,
                "before\n",
                gitignore=["setup.log"],
            )
            task = EvalTask(
                id="deleted-ignored-setup-untracked-task",
                title="Deleted ignored setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not delete setup.log.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(forbidden_paths=["setup.log"]),
            )

            def action(workspace, _task_env):
                (workspace / "setup.log").unlink()
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["setup.log"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `setup.log` "
                    "matches forbidden_paths pattern `setup.log`"
                ],
            )

    def test_committed_agent_changes_are_counted_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="committed-boundary-task",
                title="Committed boundary task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change forbidden.txt.",
                success=SuccessCriteria(forbidden_paths=["forbidden.txt"]),
            )

            def action(workspace, _task_env):
                (workspace / "forbidden.txt").write_text(
                    "secret\n",
                    encoding="utf-8",
                )
                self._git(["config", "user.email", "agentlab@example.com"], workspace)
                self._git(["config", "user.name", "Agent Lab"], workspace)
                self._git(["add", "forbidden.txt"], workspace)
                self._git(["commit", "-m", "agent change"], workspace)
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["forbidden.txt"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `forbidden.txt` "
                    "matches forbidden_paths pattern `forbidden.txt`"
                ],
            )

    def test_staged_only_tracked_change_counts_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="staged-only-boundary-task",
                title="Staged only boundary task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change app.txt.",
                success=SuccessCriteria(forbidden_paths=["app.txt"]),
            )

            def action(workspace, _task_env):
                app_path = workspace / "app.txt"
                app_path.write_text("staged change\n", encoding="utf-8")
                self._git(["add", "app.txt"], workspace)
                app_path.write_text("before\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["app.txt"])
            self.assertEqual(execution.lines_added, 1)
            self.assertEqual(execution.lines_deleted, 1)
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `app.txt` "
                    "matches forbidden_paths pattern `app.txt`"
                ],
            )

    def test_renamed_tracked_file_counts_both_paths_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="renamed-boundary-task",
                title="Renamed boundary task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Move app.txt into the allowed path.",
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    forbidden_paths=["allowed/app.txt"],
                ),
            )

            def action(workspace, _task_env):
                (workspace / "allowed").mkdir()
                self._git(["mv", "app.txt", "allowed/app.txt"], workspace)
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertCountEqual(
                execution.files_changed,
                ["app.txt", "allowed/app.txt"],
            )
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `allowed/app.txt` "
                    "matches forbidden_paths pattern `allowed/app.txt`",
                    "scope boundary violation: `app.txt` is outside allowed_paths",
                ],
            )


if __name__ == "__main__":
    unittest.main()
