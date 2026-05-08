import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.agents.codex_cli import (
    CodexCliAdapter,
    CodexCliConfig,
    run_codex_preflight,
)
from agentlab.runner import run_task
from agentlab.tasks import EvalTask


class CodexCliAdapterTest(unittest.TestCase):
    def test_codex_command_places_global_approval_before_exec(self):
        adapter = CodexCliAdapter(
            CodexCliConfig(command="codex-test", approval_policy="never")
        )

        command = adapter._build_command(
            Path("/workspace"),
            Path("/run/codex-last-message.md"),
            "prompt",
        )

        self.assertEqual(
            command[:4],
            ["codex-test", "--ask-for-approval", "never", "exec"],
        )
        self.assertLess(command.index("--ask-for-approval"), command.index("exec"))

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

    def test_codex_preflight_runs_version_and_exec_help_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            fake_codex = temp_path / "fake-codex"
            fake_codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_codex.chmod(0o755)
            commands = []

            def fake_runner(command, timeout_seconds):
                commands.append(command)
                if "--version" in command:
                    return subprocess.CompletedProcess(
                        args=command,
                        returncode=0,
                        stdout="codex 1.2.3\n",
                        stderr="",
                    )
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="Usage: codex exec [OPTIONS]\n",
                    stderr="",
                )

            result = run_codex_preflight(
                CodexCliConfig(
                    command=str(fake_codex),
                    model="gpt-test",
                    profile="agentlab",
                    sandbox="read-only",
                    approval_policy="never",
                ),
                timeout_seconds=3,
                command_runner=fake_runner,
            )

        self.assertTrue(result.passed)
        self.assertEqual(commands[0], [str(fake_codex), "--version"])
        exec_help_command = commands[1]
        self.assertLess(
            exec_help_command.index("--ask-for-approval"),
            exec_help_command.index("exec"),
        )
        self.assertIn("--json", exec_help_command)
        self.assertIn("--cd", exec_help_command)
        self.assertIn("--sandbox", exec_help_command)
        self.assertIn("--model", exec_help_command)
        self.assertIn("--profile", exec_help_command)
        self.assertEqual(exec_help_command[-1], "--help")

    def test_codex_preflight_missing_command_fails_fast(self):
        result = run_codex_preflight(
            CodexCliConfig(command="agentlab-codex-missing"),
            timeout_seconds=1,
        )

        self.assertFalse(result.passed)
        self.assertEqual(len(result.checks), 1)
        self.assertEqual(result.checks[0].name, "Codex executable")
        self.assertIn("Codex CLI not found", result.checks[0].message)

    def test_codex_preflight_reports_exec_help_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            fake_codex = temp_path / "fake-codex"
            fake_codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_codex.chmod(0o755)

            def fake_runner(command, timeout_seconds):
                if "--version" in command:
                    return subprocess.CompletedProcess(
                        args=command,
                        returncode=0,
                        stdout="codex 1.2.3\n",
                        stderr="",
                    )
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=2,
                    stdout="",
                    stderr="unexpected argument '--ask-for-approval'\n",
                )

            result = run_codex_preflight(
                CodexCliConfig(command=str(fake_codex)),
                timeout_seconds=3,
                command_runner=fake_runner,
            )

        self.assertFalse(result.passed)
        self.assertEqual(result.checks[-1].name, "Codex exec command shape")
        self.assertIn("unexpected argument", result.checks[-1].message)

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
            self.assertEqual(evaluation.agent_run.input_tokens, 10)
            self.assertEqual(evaluation.agent_run.cached_input_tokens, 4)
            self.assertEqual(evaluation.agent_run.output_tokens, 5)
            self.assertEqual(evaluation.agent_run.reasoning_output_tokens, 2)
            self.assertIsNone(evaluation.agent_run.cost_usd)
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["input_tokens"], 10)
            self.assertEqual(result["resource_usage"]["total_tokens"], 15)
            self.assertIsNone(result["resource_usage"]["cost_usd"])
            report = evaluation.report_path.read_text(encoding="utf-8")
            self.assertIn("- Input tokens: `10`", report)
            self.assertIn("- Cost USD: `unknown`", report)
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
            stdout=(
                '{"type":"turn.completed","usage":{"input_tokens":10,'
                '"cached_input_tokens":4,"output_tokens":5,'
                '"reasoning_output_tokens":2}}\n'
            ),
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
