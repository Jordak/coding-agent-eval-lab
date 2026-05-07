import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from agentlab.reference import ReferenceVerificationError, verify_reference
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
