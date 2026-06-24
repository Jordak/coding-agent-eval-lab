import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.agents.manual import ManualAgentAdapter
from agentlab.agents.base import AgentRun
from agentlab.execution.runner import _run_id, run_task
from agentlab.tasks import EvalTask, HiddenVerifier, SuccessCriteria
from tests.git_fixtures import commit_file
from tests.git_fixtures import git
from tests.git_fixtures import head
from tests.git_fixtures import init_repo


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
            init_repo(repo)
            commit = commit_file(repo, "README.md", "# Fixture\n", message="initial")

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
            init_repo(repo)
            bin_dir = repo / "bin"
            bin_dir.mkdir()
            verifier = bin_dir / "verify-local-env"
            verifier.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
            verifier.chmod(0o755)
            git(["add", "bin/verify-local-env"], repo)
            git(["commit", "-m", "initial"], repo)
            commit = head(repo)

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

    def test_visible_validation_is_not_executed_or_serialized_as_grader(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "README.md", "# Fixture\n", message="initial")
            visible_command = (
                f"{sys.executable} -c "
                "\"raise SystemExit('visible validation should not run')\""
            )
            target_command = f"{sys.executable} -c \"print('target ok')\""

            task = EvalTask(
                id="visible-validation-task",
                title="Visible validation task",
                repo=str(repo),
                commit=commit,
                language="python",
                prompt="Do nothing.",
                visible_validation=[visible_command],
                test=[target_command],
            )

            evaluation = run_task(
                task,
                ManualAgentAdapter(pause=False),
                temp_path / "runs",
            )
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            report = evaluation.report_path.read_text(encoding="utf-8")

            self.assertTrue(evaluation.score.tests_passed)
            self.assertEqual(
                [check.command for check in evaluation.score.checks],
                [target_command],
            )
            self.assertEqual(evaluation.agent_run.commands_run, [target_command])
            self.assertEqual(
                [check["command"] for check in result["checks"]],
                [target_command],
            )
            self.assertEqual(
                [grader["assertion"] for grader in result["graders"]],
                [target_command],
            )
            self.assertIn(target_command, report)
            self.assertNotIn(visible_command, report)
            self.assertNotIn(visible_command, json.dumps(result))

    def test_hidden_verifier_is_serialized_separately_from_public_graders(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "before\n", message="initial")
            bundle = temp_path / "bundle"
            bundle.mkdir()
            task_file = bundle / "task.yaml"
            task_file.write_text("id: hidden-task\n", encoding="utf-8")
            (bundle / "verifier.patch").write_text(
                "\n".join(
                    [
                        "diff --git a/hidden_check.py b/hidden_check.py",
                        "new file mode 100644",
                        "--- /dev/null",
                        "+++ b/hidden_check.py",
                        "@@ -0,0 +1,2 @@",
                        "+from pathlib import Path",
                        "+assert Path('app.txt').read_text() == 'after\\n'",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            public_command = f"{sys.executable} -c \"print('public ok')\""
            hidden_command = f"{sys.executable} hidden_check.py"

            task = EvalTask(
                id="hidden-serialization-task",
                title="Hidden serialization task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change app.txt.",
                test=[public_command],
                hidden_verifier=HiddenVerifier(
                    patch="verifier.patch",
                    commands=[hidden_command],
                ),
                source_path=task_file,
            )

            class EditingAdapter:
                name = "editing"

                def run(self, task, workspace, run_dir):
                    (workspace / "app.txt").write_text("after\n", encoding="utf-8")
                    transcript_path = run_dir / "transcript.txt"
                    transcript_path.write_text("edited\n", encoding="utf-8")
                    return AgentRun(
                        agent_name=self.name,
                        task_id=task.id,
                        transcript_path=transcript_path,
                        diff_path=run_dir / "diff.patch",
                    )

            evaluation = run_task(task, EditingAdapter(), temp_path / "runs")
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            report = evaluation.report_path.read_text(encoding="utf-8")

            self.assertTrue(evaluation.score.tests_passed)
            self.assertEqual(evaluation.agent_run.commands_run, [public_command])
            self.assertEqual(
                [check["command"] for check in result["checks"]],
                [public_command],
            )
            self.assertEqual(
                [grader["assertion"] for grader in result["graders"]],
                [public_command],
            )
            self.assertEqual(result["hidden_verifier"]["patch"], "verifier.patch")
            self.assertEqual(
                [check["command"] for check in result["hidden_verifier"]["checks"]],
                [
                    "git apply hidden verifier patch: verifier.patch",
                    hidden_command,
                ],
            )
            self.assertIn("## Public Graders", report)
            self.assertIn(public_command, report)
            self.assertIn("## Hidden Verifier", report)
            self.assertIn(hidden_command, report)
            self.assertFalse(
                (
                    evaluation.run_dir
                    / "workspace"
                    / "hidden-serialization-task"
                    / "hidden_check.py"
                ).exists()
            )

    def test_max_files_changed_is_enforced(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "a.txt", "before\n", message="initial")

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
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "before\nsame\n", message="initial")

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

if __name__ == "__main__":
    unittest.main()
