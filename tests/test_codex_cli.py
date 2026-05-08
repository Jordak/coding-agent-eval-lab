import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.agents.codex_cli import CodexCliAdapter, CodexCliConfig
from agentlab.runner import run_task
from agentlab.tasks import EvalTask


class CodexCliAdapterTest(unittest.TestCase):
    def test_codex_adapter_popen_path_captures_output(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            fake_codex = temp_path / "fake-codex"
            fake_codex.write_text(
                "#!/bin/sh\n"
                "last=''\n"
                "while [ \"$#\" -gt 0 ]; do\n"
                "  if [ \"$1\" = '--output-last-message' ]; then\n"
                "    shift\n"
                "    last=\"$1\"\n"
                "  fi\n"
                "  shift\n"
                "done\n"
                "printf 'Done %s.\\n' \"$AGENTLAB_TEST_SENTINEL\" > \"$last\"\n"
                "printf '{\"type\":\"done\"}\\n'\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            task = EvalTask(
                id="popen-codex",
                title="Popen Codex",
                repo=str(temp_path),
                commit="unused",
                language="text",
                prompt="No-op.",
                environment={"AGENTLAB_TEST_SENTINEL": "from-env"},
            )
            adapter = CodexCliAdapter(
                CodexCliConfig(command=str(fake_codex), timeout_seconds=5)
            )

            agent_run = adapter.run(task, temp_path, temp_path / "run")

            self.assertIsNone(agent_run.error)
            self.assertEqual(
                (temp_path / "run" / "codex-events.jsonl").read_text(
                    encoding="utf-8"
                ),
                '{"type":"done"}\n',
            )
            self.assertEqual(
                (temp_path / "run" / "codex-last-message.md").read_text(
                    encoding="utf-8"
                ),
                "Done from-env.\n",
            )

    def test_missing_codex_cli_error_points_to_portable_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            task = EvalTask(
                id="missing-codex",
                title="Missing Codex",
                repo=str(temp_path),
                commit="unused",
                language="text",
                prompt="No-op.",
            )
            adapter = CodexCliAdapter(
                CodexCliConfig(command="agentlab-codex-missing", timeout_seconds=1)
            )

            agent_run = adapter.run(task, temp_path, temp_path / "run")

            assert agent_run.error is not None
            self.assertIn("Codex CLI not found", agent_run.error)
            self.assertIn("--codex-command", agent_run.error)

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
