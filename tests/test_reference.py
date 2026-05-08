import shutil
import subprocess
import sys
import tempfile
import textwrap
import json
import unittest
from pathlib import Path

from agentlab.reference import ReferenceVerificationError, verify_reference
from agentlab.results import load_results
from agentlab.scoring import calculate_grader_outcome
from agentlab.tasks import EvalTask, load_task


class ReferenceVerificationTest(unittest.TestCase):
    def test_verifies_patch_reference_artifact(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for reference verification")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("after\n", encoding="utf-8")
            patch = self._git(["diff"], repo).stdout
            self._git(["checkout", "--", "app.txt"], repo)

            bundle = temp_path / "task"
            bundle.mkdir()
            (bundle / "reference.patch").write_text(patch, encoding="utf-8")
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    f"""
                    id: reference-task
                    title: Reference task
                    repo: {repo}
                    commit: {commit}
                    language: text
                    prompt: Change before to after.
                    reference_artifact:
                      type: patch
                      path: reference.patch
                    baseline:
                      - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'before\\n'"
                    test:
                      - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"
                    success:
                      max_files_changed: 1
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)
            verification = verify_reference(task, temp_path / "work")

        self.assertTrue(verification.success)
        self.assertEqual(verification.files_changed, ["app.txt"])

    def test_reference_verification_uses_shared_grader_outcome(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for reference verification")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("after\n", encoding="utf-8")
            patch = self._git(["diff"], repo).stdout
            self._git(["checkout", "--", "app.txt"], repo)

            bundle = temp_path / "task"
            bundle.mkdir()
            (bundle / "reference.patch").write_text(patch, encoding="utf-8")
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    f"""
                    id: reference-task
                    title: Reference task
                    repo: {repo}
                    commit: {commit}
                    language: text
                    prompt: Change before to after.
                    reference_artifact:
                      type: patch
                      path: reference.patch
                    test:
                      - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"
                    success:
                      max_files_changed: 0
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)
            verification = verify_reference(task, temp_path / "work")

        expected_checks = (
            verification.setup_checks
            + verification.baseline_checks
            + [verification.artifact_check]
            + verification.target_checks
        )
        expected_score = calculate_grader_outcome(
            task,
            expected_checks,
            verification.files_changed,
        )

        self.assertEqual(verification.score, expected_score)
        self.assertFalse(verification.success)
        self.assertEqual(verification.notes, ["changed 1 files; limit is 0"])

    def test_requires_reference_artifact(self):
        task = EvalTask(
            id="missing-reference",
            title="Missing reference",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix it.",
        )

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ReferenceVerificationError):
                verify_reference(task, Path(temp))

    def test_writes_reference_report_and_result(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for reference verification")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("after\n", encoding="utf-8")
            patch = self._git(["diff"], repo).stdout
            self._git(["checkout", "--", "app.txt"], repo)

            bundle = temp_path / "task"
            bundle.mkdir()
            (bundle / "reference.patch").write_text(patch, encoding="utf-8")
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    f"""
                    id: reference-task
                    title: Reference task
                    repo: {repo}
                    commit: {commit}
                    language: text
                    prompt: Change before to after.
                    reference_artifact:
                      type: patch
                      path: reference.patch
                    test:
                      - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)
            verification = verify_reference(
                task,
                temp_path / "work",
                write_artifacts=True,
            )
            result = json.loads(
                (bundle / "reference-result.json").read_text(encoding="utf-8")
            )

            self.assertTrue(verification.success)
            self.assertTrue((bundle / "reference-report.md").exists())
            self.assertTrue((bundle / "reference-result.json").exists())
            self.assertTrue((bundle / "reference.diff").exists())
            self.assertEqual(result["trial_kind"], "reference_verification")
            self.assertEqual(result["agent_name"], "reference")
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["lines_added"], 1)
            self.assertEqual(result["lines_deleted"], 1)
            self.assertEqual(result["outcome"]["lines_added"], 1)
            self.assertEqual(result["outcome"]["lines_deleted"], 1)
            self.assertEqual(result["run_dir"], ".")

    def test_load_results_excludes_reference_verification_results(self):
        with tempfile.TemporaryDirectory() as temp:
            result_path = Path(temp) / "reference-result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "reference_verification",
                        "run_dir": temp,
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(load_results([result_path]), [])

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
