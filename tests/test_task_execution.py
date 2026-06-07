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
from agentlab.tasks import EvalTask, SuccessCriteria
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
                git(["config", "user.email", "agentlab@example.com"], workspace)
                git(["config", "user.name", "Agent Lab"], workspace)
                git(["add", "forbidden.txt"], workspace)
                git(["commit", "-m", "agent change"], workspace)
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

    def _repo_with_file(self, root, contents, *, gitignore=None):
        repo = root / "repo"
        init_repo(repo)
        if gitignore is not None:
            (repo / ".gitignore").write_text(
                "".join(f"{pattern}\n" for pattern in gitignore),
                encoding="utf-8",
            )
            (repo / "app.txt").write_text(contents, encoding="utf-8")
            git(["add", ".gitignore", "app.txt"], repo)
            git(["commit", "-m", "initial"], repo)
            commit = git(["rev-parse", "HEAD"], repo).stdout.strip()
        else:
            commit = commit_file(repo, "app.txt", contents, message="initial")
        return repo, commit


if __name__ == "__main__":
    unittest.main()
