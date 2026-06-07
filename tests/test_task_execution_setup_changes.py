import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.execution.phases import TaskActionResult
from agentlab.execution.phases import execute_task_phases
from agentlab.tasks import EvalTask, SuccessCriteria
from tests.task_execution_helpers import TaskExecutionGitMixin


class TaskExecutionSetupChangeTest(TaskExecutionGitMixin, unittest.TestCase):
    def test_setup_created_untracked_files_are_not_counted_as_agent_changes(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-untracked-task",
                title="Setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["allowed/result.txt"])
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_staged_unchanged_setup_created_untracked_file_is_not_counted(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="staged-setup-untracked-task",
                title="Staged setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    forbidden_paths=["setup.log"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                self._git(["add", "."], workspace)
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["allowed/result.txt"])
            self.assertEqual(execution.lines_added, 1)
            self.assertEqual(execution.lines_deleted, 0)
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_setup_staged_new_file_is_not_counted_as_agent_change(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-staged-new-task",
                title="Setup staged new task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\"",
                    "git add setup.log",
                ],
                success=SuccessCriteria(
                    forbidden_paths=["setup.log"],
                    max_files_changed=0,
                ),
            )

            def action(workspace, _task_env):
                cached_paths = self._git(
                    ["diff", "--cached", "--name-only"],
                    workspace,
                ).stdout.splitlines()
                self.assertEqual(cached_paths, ["setup.log"])
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, [])
            self.assertEqual(execution.lines_added, 0)
            self.assertEqual(execution.lines_deleted, 0)
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_setup_staged_tracked_change_remains_visible_to_agent(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-staged-tracked-task",
                title="Setup staged tracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('app.txt').write_text('setup\\\\n')\"",
                    "git add app.txt",
                ],
                success=SuccessCriteria(
                    forbidden_paths=["app.txt"],
                    max_files_changed=0,
                ),
            )

            def action(workspace, _task_env):
                cached_paths = self._git(
                    ["diff", "--cached", "--name-only"],
                    workspace,
                ).stdout.splitlines()
                self.assertEqual(cached_paths, ["app.txt"])
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, [])
            self.assertEqual(execution.lines_added, 0)
            self.assertEqual(execution.lines_deleted, 0)
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_setup_staged_deletion_remains_visible_to_agent(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-staged-deletion-task",
                title="Setup staged deletion task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; Path('app.txt').unlink()\"",
                    "git add app.txt",
                ],
                success=SuccessCriteria(
                    forbidden_paths=["app.txt"],
                    max_files_changed=0,
                ),
            )

            def action(workspace, _task_env):
                cached_paths = self._git(
                    ["diff", "--cached", "--name-only"],
                    workspace,
                ).stdout.splitlines()
                self.assertEqual(cached_paths, ["app.txt"])
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, [])
            self.assertEqual(execution.lines_added, 0)
            self.assertEqual(execution.lines_deleted, 0)
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_setup_modified_tracked_file_is_not_counted_as_agent_change(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-tracked-task",
                title="Setup tracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('app.txt').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(
                    forbidden_paths=["app.txt"],
                    max_files_changed=0,
                ),
            )

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                lambda _workspace, _task_env: TaskActionResult(),
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, [])
            self.assertEqual(execution.lines_added, 0)
            self.assertEqual(execution.lines_deleted, 0)
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_staged_only_change_after_setup_tracked_change_counts(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="staged-after-setup-tracked-task",
                title="Staged after setup tracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change app.txt.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('app.txt').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(forbidden_paths=["app.txt"]),
            )

            def action(workspace, _task_env):
                app_path = workspace / "app.txt"
                app_path.write_text("agent staged\n", encoding="utf-8")
                self._git(["add", "app.txt"], workspace)
                app_path.write_text("setup\n", encoding="utf-8")
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

    def test_reset_after_setup_staged_tracked_change_counts(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="reset-after-setup-staged-tracked-task",
                title="Reset after setup staged tracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change app.txt.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('app.txt').write_text('setup\\\\n')\"",
                    "git add app.txt",
                ],
                success=SuccessCriteria(forbidden_paths=["app.txt"]),
            )

            def action(workspace, _task_env):
                cached_paths = self._git(
                    ["diff", "--cached", "--name-only"],
                    workspace,
                ).stdout.splitlines()
                self.assertEqual(cached_paths, ["app.txt"])
                self._git(["reset", "HEAD", "--", "app.txt"], workspace)
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["app.txt"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `app.txt` "
                    "matches forbidden_paths pattern `app.txt`"
                ],
            )

    def test_reset_after_setup_staged_deletion_counts(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="reset-after-setup-staged-deletion-task",
                title="Reset after setup staged deletion task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not change app.txt.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; Path('app.txt').unlink()\"",
                    "git add app.txt",
                ],
                success=SuccessCriteria(forbidden_paths=["app.txt"]),
            )

            def action(workspace, _task_env):
                cached_paths = self._git(
                    ["diff", "--cached", "--name-only"],
                    workspace,
                ).stdout.splitlines()
                self.assertEqual(cached_paths, ["app.txt"])
                self._git(["reset", "HEAD", "--", "app.txt"], workspace)
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["app.txt"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `app.txt` "
                    "matches forbidden_paths pattern `app.txt`"
                ],
            )

    def test_ignored_new_untracked_file_counts_against_boundaries(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(
                temp_path,
                "before\n",
                gitignore=["secrets/"],
            )
            task = EvalTask(
                id="ignored-new-untracked-task",
                title="Ignored new untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do not create secrets.",
                success=SuccessCriteria(forbidden_paths=["secrets/"]),
            )

            def action(workspace, _task_env):
                secret_dir = workspace / "secrets"
                secret_dir.mkdir()
                (secret_dir / "key.txt").write_text("secret\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["secrets/key.txt"])
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "scope boundary violation: `secrets/key.txt` "
                    "matches forbidden_paths pattern `secrets/`"
                ],
            )

    def test_ignored_setup_created_untracked_file_unchanged_is_not_counted(self):
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
                id="ignored-setup-untracked-task",
                title="Ignored setup untracked task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "Path('setup.log').write_text('setup\\\\n')\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["allowed/result.txt"])
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_setup_created_byproduct_tree_does_not_require_content_hashing(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-byproduct-task",
                title="Setup byproduct task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "path = Path('.agentlab/venv/unreadable.py'); "
                    "path.parent.mkdir(parents=True); "
                    "path.write_text('setup byproduct\\\\n'); "
                    "path.chmod(0)\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )
            (execution.workspace / ".agentlab/venv/unreadable.py").chmod(0o600)

            self.assertEqual(execution.files_changed, ["allowed/result.txt"])
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])

    def test_setup_created_byproduct_metadata_change_counts_against_allowed_paths(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="setup-byproduct-touch-task",
                title="Setup byproduct touch task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "path = Path('.agentlab/venv/cache.py'); "
                    "path.parent.mkdir(parents=True); "
                    "path.write_text('setup byproduct\\\\n')\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                (workspace / ".agentlab/venv/cache.py").write_text(
                    "setup byproduct\n",
                    encoding="utf-8",
                )
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(
                execution.files_changed,
                ["allowed/result.txt", ".agentlab/venv/cache.py"],
            )
            self.assertEqual(
                execution.setup_created_untracked_changed_paths,
                [".agentlab/venv/cache.py"],
            )
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "changed 2 files; limit is 1",
                    "scope boundary violation: `.agentlab/venv/cache.py` "
                    "is outside allowed_paths",
                ],
            )

    def test_deleted_setup_created_byproduct_counts_against_allowed_paths(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(temp_path, "before\n")
            task = EvalTask(
                id="deleted-setup-byproduct-task",
                title="Deleted setup byproduct task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                setup=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "path = Path('.agentlab/venv/cache.py'); "
                    "path.parent.mkdir(parents=True); "
                    "path.write_text('setup byproduct\\\\n')\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                (workspace / ".agentlab/venv/cache.py").unlink()
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(
                execution.files_changed,
                ["allowed/result.txt", ".agentlab/venv/cache.py"],
            )
            self.assertEqual(
                execution.setup_created_untracked_changed_paths,
                [".agentlab/venv/cache.py"],
            )
            self.assertFalse(execution.score.tests_passed)
            self.assertEqual(
                execution.score.notes,
                [
                    "changed 2 files; limit is 1",
                    "scope boundary violation: `.agentlab/venv/cache.py` "
                    "is outside allowed_paths",
                ],
            )

    def test_target_created_files_are_not_counted_as_agent_changes(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for task execution")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo, commit = self._repo_with_file(
                temp_path,
                "before\n",
                gitignore=[".pytest_cache/"],
            )
            task = EvalTask(
                id="target-byproduct-task",
                title="Target byproduct task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Create the allowed result file.",
                test=[
                    f"{sys.executable} -c "
                    "\"import subprocess; from pathlib import Path; "
                    "others = subprocess.check_output("
                    "['git', 'ls-files', '--others', '--exclude-standard'], "
                    "text=True).splitlines(); "
                    "assert others == ['allowed/result.txt'], others; "
                    "Path('.pytest_cache').mkdir(); "
                    "Path('.pytest_cache/cache').write_text('grader\\\\n')\""
                ],
                success=SuccessCriteria(
                    allowed_paths=["allowed/"],
                    forbidden_paths=[".pytest_cache/"],
                    max_files_changed=1,
                ),
            )

            def action(workspace, _task_env):
                output_dir = workspace / "allowed"
                output_dir.mkdir()
                (output_dir / "result.txt").write_text("ok\n", encoding="utf-8")
                return TaskActionResult()

            execution = execute_task_phases(
                task,
                temp_path / "workspace",
                action,
                temp_path / "diff.patch",
            )

            self.assertEqual(execution.files_changed, ["allowed/result.txt"])
            self.assertTrue((execution.workspace / ".pytest_cache/cache").exists())
            self.assertTrue(execution.score.tests_passed)
            self.assertEqual(execution.score.notes, [])


if __name__ == "__main__":
    unittest.main()
