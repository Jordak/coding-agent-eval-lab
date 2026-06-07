import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.agents.manual import ManualAgentAdapter
from agentlab.execution.runner import _run_id, run_task
from agentlab.tasks import EvalTask, SuccessCriteria


class RunnerTest(unittest.TestCase):
    def test_run_ids_are_unique_for_quick_repeated_trials(self):
        run_ids = {_run_id("fixture-task", "manual") for _ in range(100)}

        self.assertEqual(len(run_ids), 100)

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
            self.assertEqual(evaluation.agent_run.lines_added, 0)
            self.assertEqual(evaluation.agent_run.lines_deleted, 0)
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["task_repo"], str(repo))
            self.assertEqual(result["task_commit"], commit)
            self.assertEqual(
                result["run_surface"]["workspace_history_policy"],
                "base_only",
            )
            self.assertEqual(
                result["run_surface"]["workspace_base_ref"],
                evaluation.workspace_base_ref,
            )
            self.assertNotEqual(evaluation.workspace_base_ref, commit)

    def test_task_environment_path_is_used_by_graders(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            bin_dir = repo / "bin"
            bin_dir.mkdir()
            verifier = bin_dir / "verify-local-env"
            verifier.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
            verifier.chmod(0o755)
            self._git(["add", "bin/verify-local-env"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            task = EvalTask(
                id="env-path-task",
                title="Environment path task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
                environment_path=["bin"],
                test=["verify-local-env"],
            )

            evaluation = run_task(
                task,
                ManualAgentAdapter(pause=False),
                temp_path / "runs",
            )

            self.assertTrue(evaluation.score.tests_passed)

    def test_max_files_changed_is_enforced(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "a.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "a.txt"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            task = EvalTask(
                id="file-limit-task",
                title="File limit task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change too many files.",
                success=SuccessCriteria(max_files_changed=0),
            )

            class EditingManualAdapter(ManualAgentAdapter):
                def run(self, task, workspace, run_dir):
                    (workspace / "a.txt").write_text("after\n", encoding="utf-8")
                    return super().run(task, workspace, run_dir)

            evaluation = run_task(
                task,
                EditingManualAdapter(pause=False),
                temp_path / "runs",
            )

            self.assertFalse(evaluation.score.tests_passed)
            self.assertIn("changed 1 files", evaluation.score.notes[0])

    def test_records_line_diff_metrics(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("before\nsame\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            task = EvalTask(
                id="line-metrics-task",
                title="Line metrics task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change app.txt.",
                test=[
                    f"{sys.executable} -c "
                    "\"from pathlib import Path; "
                    "assert Path('app.txt').read_text() == 'after\\nsame\\nnew\\n'\""
                ],
            )

            class EditingManualAdapter(ManualAgentAdapter):
                def run(self, task, workspace, run_dir):
                    (workspace / "app.txt").write_text(
                        "after\nsame\nnew\n",
                        encoding="utf-8",
                    )
                    return super().run(task, workspace, run_dir)

            evaluation = run_task(
                task,
                EditingManualAdapter(pause=False),
                temp_path / "runs",
            )
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            report = evaluation.report_path.read_text(encoding="utf-8")

            self.assertTrue(evaluation.score.tests_passed)
            self.assertEqual(evaluation.agent_run.lines_added, 2)
            self.assertEqual(evaluation.agent_run.lines_deleted, 1)
            self.assertEqual(result["lines_added"], 2)
            self.assertEqual(result["lines_deleted"], 1)
            self.assertEqual(result["outcome"]["lines_added"], 2)
            self.assertEqual(result["outcome"]["lines_deleted"], 1)
            self.assertIn("- Lines added: `2`", report)
            self.assertIn("- Lines deleted: `1`", report)

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
