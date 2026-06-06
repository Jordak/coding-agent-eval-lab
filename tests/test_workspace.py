import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agentlab.tasks import EvalTask
from agentlab.execution.workspace import capture_diff, prepare_workspace


class WorkspaceTest(unittest.TestCase):
    def test_prepare_workspace_accepts_relative_root(self):
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

            original_cwd = Path.cwd()
            try:
                # Reproduce CLI behavior where runs-dir is provided as a relative path.
                import os

                os.chdir(temp_path)
                task = EvalTask(
                    id="fixture-task",
                    title="Fixture task",
                    repo=str(repo),
                    commit=commit,
                    language="python",
                    prompt="Do nothing.",
                )

                prepared = prepare_workspace(task, Path("runs/relative-root"))
            finally:
                os.chdir(original_cwd)

            self.assertTrue(prepared.path.exists())
            self.assertEqual(prepared.workspace_history_policy, "base_only")
            self.assertEqual(
                self._git(["rev-list", "--count", "--all"], prepared.path)
                .stdout.strip(),
                "1",
            )
            self.assertEqual(
                self._git(["rev-parse", "HEAD"], prepared.path).stdout.strip(),
                prepared.workspace_base_ref,
            )
            self.assertNotEqual(prepared.workspace_base_ref, commit)
            self.assertEqual(
                (prepared.path / "README.md").read_text(encoding="utf-8"),
                "# Fixture\n",
            )

    def test_prepare_workspace_hides_later_source_history(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("gold\n", encoding="utf-8")
            self._git(["commit", "-am", "gold"], repo)
            gold_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            self._git(["tag", "gold-fix"], repo)

            task = EvalTask(
                id="leakage-task",
                title="Leakage task",
                repo=str(repo),
                commit=base_commit,
                language="text",
                prompt="Do not inspect future commits.",
            )

            prepared = prepare_workspace(task, temp_path / "workspace")

            self.assertEqual(
                self._git(["rev-list", "--count", "--all"], prepared.path)
                .stdout.strip(),
                "1",
            )
            self.assertNotIn(
                gold_commit,
                self._git(["log", "--all", "--format=%H"], prepared.path).stdout,
            )
            self.assertEqual(
                self._git(["remote"], prepared.path).stdout.strip(),
                "",
            )
            self.assertEqual(
                self._git(["tag"], prepared.path).stdout.strip(),
                "",
            )
            self.assertEqual(
                (prepared.path / "app.txt").read_text(encoding="utf-8"),
                "base\n",
            )

    def test_capture_diff_uses_explicit_synthetic_base_ref(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            task = EvalTask(
                id="diff-base-task",
                title="Diff base task",
                repo=str(repo),
                commit=base_commit,
                language="text",
                prompt="Change the file.",
            )
            prepared = prepare_workspace(task, temp_path / "workspace")
            (prepared.path / "app.txt").write_text("after\n", encoding="utf-8")

            changed = capture_diff(
                prepared.path,
                temp_path / "diff.patch",
                base_ref=prepared.workspace_base_ref,
            )

            self.assertEqual(changed, ["app.txt"])
            self.assertIn(
                "-before",
                (temp_path / "diff.patch").read_text(encoding="utf-8"),
            )

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
