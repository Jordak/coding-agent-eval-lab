import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentlab.agents.codex_cli import (
    CodexCliAdapter,
    CodexCliConfig,
    _resolve_executable,
)
from agentlab.runner import run_task
from agentlab.tasks import EvalTask


class CodexCliAdapterTest(unittest.TestCase):
    def test_resolves_codex_from_macos_app_bundle_when_not_on_path(self):
        with tempfile.TemporaryDirectory() as temp:
            bundled_codex = Path(temp) / "Codex.app" / "Contents" / "Resources" / "codex"
            bundled_codex.parent.mkdir(parents=True)
            bundled_codex.write_text("#!/bin/sh\n", encoding="utf-8")
            bundled_codex.chmod(0o755)

            with patch("agentlab.agents.codex_cli.shutil.which", return_value=None):
                self.assertEqual(
                    _resolve_executable("codex", fallback_paths=[bundled_codex]),
                    str(bundled_codex),
                )

    def test_codex_adapter_runs_command_and_captures_patch(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "answer.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "answer.txt"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            task = EvalTask(
                id="codex-fixture",
                title="Codex fixture",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change answer.txt to contain after.",
                test=[
                    (
                        f"{sys.executable} -c "
                        "\"from pathlib import Path; "
                        "assert Path('answer.txt').read_text() == 'after\\n'\""
                    )
                ],
            )
            adapter = CodexCliAdapter(
                CodexCliConfig(command="codex-test", timeout_seconds=30),
                command_runner=self._fake_codex_runner,
            )

            evaluation = run_task(task, adapter, temp_path / "runs")

            self.assertTrue(evaluation.score.tests_passed)
            self.assertEqual(evaluation.agent_run.agent_name, "codex")
            self.assertEqual(evaluation.agent_run.files_changed, ["answer.txt"])
            self.assertTrue((evaluation.run_dir / "codex-events.jsonl").exists())
            self.assertTrue((evaluation.run_dir / "codex-last-message.md").exists())
            transcript = evaluation.agent_run.transcript_path.read_text(
                encoding="utf-8"
            )
            self.assertIn("codex-test --ask-for-approval never exec", transcript)
            self.assertIn(
                "+after",
                evaluation.agent_run.diff_path.read_text(encoding="utf-8"),
            )

    def _fake_codex_runner(self, command, timeout_seconds):
        workspace = Path(command[command.index("--cd") + 1])
        (workspace / "answer.txt").write_text("after\n", encoding="utf-8")
        last_message = Path(command[command.index("--output-last-message") + 1])
        last_message.write_text("Done.", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"type":"done"}\n',
            stderr="",
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
