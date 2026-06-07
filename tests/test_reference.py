import shutil
import os
import subprocess
import sys
import tempfile
import textwrap
import json
import unittest
from unittest import mock
from pathlib import Path

from agentlab.evidence.outcome import load_outcome_evidences
from agentlab.tasks.reference import ReferenceVerificationError, verify_reference
from agentlab.execution.scoring import calculate_grader_outcome
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
            self.assertEqual(verification.workspace_history_policy, "base_only")
            self._assert_base_only_repository(verification.workspace)

    def test_commit_reference_artifact_is_converted_to_patch(self):
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
            self._git(["commit", "-m", "base"], repo)
            base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("after\n", encoding="utf-8")
            self._git(["commit", "-am", "reference"], repo)
            reference_commit = (
                self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            )

            bundle = temp_path / "task"
            bundle.mkdir()
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    f"""
                    id: commit-reference-task
                    title: Commit reference task
                    repo: {repo}
                    commit: {base_commit}
                    language: text
                    prompt: Change before to after.
                    reference_artifact:
                      type: commit
                      commit: {reference_commit}
                    test:
                      - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)
            verification = verify_reference(task, temp_path / "work")

            self.assertTrue(verification.success)
            self.assertEqual(verification.files_changed, ["app.txt"])
            self._assert_base_only_repository(verification.workspace)
            self.assertNotIn(
                reference_commit,
                self._git(
                    ["log", "--all", "--format=%H"],
                    verification.workspace,
                ).stdout,
            )

    def test_commit_reference_prep_clone_does_not_checkout_filters(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for reference verification")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            home = temp_path / "home"
            xdg_config = temp_path / "xdg"
            template = temp_path / "template"
            sentinel = temp_path / "checkout-invoked"
            home.mkdir()
            xdg_config.mkdir()
            (template / "hooks").mkdir(parents=True)
            smudge = temp_path / "fail-smudge.sh"
            smudge.write_text(
                f"#!/bin/sh\necho smudge > {sentinel}\nexit 1\n",
                encoding="utf-8",
            )
            smudge.chmod(0o755)
            post_checkout = template / "hooks" / "post-checkout"
            post_checkout.write_text(
                f"#!/bin/sh\necho hook > {sentinel}\nexit 1\n",
                encoding="utf-8",
            )
            post_checkout.chmod(0o755)
            (home / ".gitconfig").write_text(
                "\n".join(
                    [
                        '[filter "block"]',
                        f"    smudge = {smudge}",
                        "    clean = cat",
                        "    required = true",
                        "[init]",
                        f"    templateDir = {template}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            repo = temp_path / "repo"
            repo.mkdir()

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                self._git(["init"], repo)
                self._git(["config", "user.email", "agentlab@example.com"], repo)
                self._git(["config", "user.name", "Agent Lab"], repo)
                (repo / ".gitattributes").write_text(
                    "app.txt filter=block\n",
                    encoding="utf-8",
                )
                (repo / "app.txt").write_text("before\n", encoding="utf-8")
                self._git(["add", ".gitattributes", "app.txt"], repo)
                self._git(["commit", "-m", "base"], repo)
                base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

                (repo / "app.txt").write_text("after\n", encoding="utf-8")
                self._git(["commit", "-am", "reference"], repo)
                reference_commit = (
                    self._git(["rev-parse", "HEAD"], repo).stdout.strip()
                )

                bundle = temp_path / "task"
                bundle.mkdir()
                (bundle / "task.yaml").write_text(
                    textwrap.dedent(
                        f"""
                        id: commit-reference-no-checkout-task
                        title: Commit reference no checkout task
                        repo: {repo}
                        commit: {base_commit}
                        language: text
                        prompt: Change before to after.
                        reference_artifact:
                          type: commit
                          commit: {reference_commit}
                        test:
                          - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"
                        """
                    ),
                    encoding="utf-8",
                )

                task = load_task(bundle)
                verification = verify_reference(task, temp_path / "work")

            self.assertTrue(verification.success)
            self.assertFalse(sentinel.exists())
            self.assertEqual(verification.files_changed, ["app.txt"])

    def test_commit_reference_ignores_clone_time_git_config(self):
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
            self._git(["commit", "-m", "base"], repo)
            base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("after\n", encoding="utf-8")
            self._git(["commit", "-am", "reference"], repo)
            reference_commit = (
                self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            )

            bundle = temp_path / "task"
            bundle.mkdir()
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    f"""
                    id: commit-reference-clone-config-task
                    title: Commit reference clone config task
                    repo: "{repo.as_uri()}"
                    commit: {base_commit}
                    language: text
                    prompt: Change before to after.
                    reference_artifact:
                      type: commit
                      commit: {reference_commit}
                    test:
                      - {sys.executable} -c "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"
                    """
                ),
                encoding="utf-8",
            )
            hostile_config = temp_path / "hostile.gitconfig"
            hostile_config.write_text(
                "\n".join(
                    [
                        '[protocol "file"]',
                        "    allow = never",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)
            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(hostile_config),
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "protocol.file.allow",
                    "GIT_CONFIG_VALUE_0": "never",
                },
            ):
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
            report = (bundle / "reference-report.md").read_text(encoding="utf-8")
            self.assertIn(f"- Task repository: `{repo}`", report)
            self.assertIn(f"- Task commit: `{commit}`", report)
            self.assertEqual(result["trial_kind"], "reference_verification")
            self.assertEqual(result["agent_name"], "reference")
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["lines_added"], 1)
            self.assertEqual(result["lines_deleted"], 1)
            self.assertEqual(result["outcome"]["lines_added"], 1)
            self.assertEqual(result["outcome"]["lines_deleted"], 1)
            self.assertEqual(result["run_dir"], ".")

    def test_load_outcome_evidences_excludes_reference_verification_results(self):
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

            self.assertEqual(load_outcome_evidences([result_path]), [])

    def test_checked_in_reference_results_do_not_embed_review_validity(self):
        for result_path in Path("tasks/starter").glob("*/reference-result.json"):
            with self.subTest(result=result_path.as_posix()):
                result = json.loads(result_path.read_text(encoding="utf-8"))

                self.assertNotIn("trial_validity", result)
                self.assertNotIn("exclusion_reason", result)

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

    def _assert_base_only_repository(self, workspace):
        self.assertEqual(
            self._git(["rev-list", "--count", "HEAD"], workspace).stdout.strip(),
            "1",
        )
        self.assertEqual(
            self._git(
                [
                    "for-each-ref",
                    "--format=%(refname)",
                    "refs/heads",
                    "refs/remotes",
                    "refs/tags",
                ],
                workspace,
            ).stdout.strip(),
            "",
        )
        self.assertFalse((workspace / ".git" / "logs").exists())


if __name__ == "__main__":
    unittest.main()
