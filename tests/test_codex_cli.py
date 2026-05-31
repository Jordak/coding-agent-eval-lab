import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agentlab.agents.codex_cli as codex_cli_module
from agentlab.agents.codex_cli import (
    CodexCliAdapter,
    CodexCliConfig,
    CodexRuntimeFacts,
    codex_agent_harness_config,
    run_codex_preflight,
)
from agentlab.execution.runner import run_task
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

    def test_codex_agent_harness_config_keeps_unknowns_explicit(self):
        config = codex_agent_harness_config(
            CodexCliConfig(
                command="codex-test",
                model=None,
                profile="agentlab",
                sandbox="workspace-write",
                approval_policy="never",
                timeout_seconds=60,
            ),
            runtime_facts=CodexRuntimeFacts(
                command_identity="/usr/local/bin/codex-test",
                cli_version="codex 1.2.3",
            ),
        )

        self.assertEqual(config["agent_harness"], "codex")
        self.assertEqual(config["agent_adapter"], "codex_cli")
        self.assertEqual(config["command"], "codex-test")
        self.assertEqual(config["command_identity"], "/usr/local/bin/codex-test")
        self.assertIsNone(config["model_name"])
        self.assertEqual(config["model_source"], "unknown")
        self.assertEqual(config["profile"], "agentlab")
        self.assertEqual(config["sandbox"], "workspace-write")
        self.assertEqual(config["approval_policy"], "never")
        self.assertEqual(config["timeout_seconds"], 60)
        self.assertEqual(config["cli_version"], "codex 1.2.3")
        self.assertIsNone(config["runtime_accountability"]["account"])
        self.assertIsNone(config["runtime_accountability"]["billing_context"])
        self.assertIsNone(config["runtime_accountability"]["cost_usd"])

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

    def test_codex_adapter_forwards_process_request_fields(self):
        captured_requests = []

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            task = EvalTask(
                id="codex-request",
                title="Codex request",
                repo=str(temp_path),
                commit="unused",
                language="text",
                prompt="No-op.",
                environment={"AGENTLAB_TEST_SENTINEL": "from-env"},
            )

            def fake_process_executor(request):
                captured_requests.append(request)
                request.stdout_path.write_text('{"type":"done"}\n', encoding="utf-8")
                last_message = Path(
                    request.command[
                        request.command.index("--output-last-message") + 1
                    ]
                )
                last_message.write_text("Done.", encoding="utf-8")
                return subprocess.CompletedProcess(
                    args=request.command,
                    returncode=0,
                    stdout='{"type":"done"}\n',
                    stderr="",
                )

            adapter = CodexCliAdapter(
                CodexCliConfig(
                    command="codex-test",
                    timeout_seconds=7,
                    show_progress=False,
                )
            )

            with patch.object(
                codex_cli_module,
                "run_agent_process",
                side_effect=fake_process_executor,
            ):
                agent_run = adapter.run(task, temp_path, temp_path / "run")

            self.assertIsNone(agent_run.error)
            self.assertEqual(len(captured_requests), 1)
            request = captured_requests[0]
            self.assertEqual(request.executable_name, "codex-test")
            self.assertEqual(request.timeout_seconds, 7)
            self.assertEqual(
                request.stdout_path,
                temp_path / "run" / "codex-events.jsonl",
            )
            self.assertEqual(request.progress_label, "Codex")
            self.assertFalse(request.show_progress)
            self.assertIsNone(request.cwd)
            assert request.env is not None
            self.assertEqual(request.env.get("AGENTLAB_TEST_SENTINEL"), "from-env")

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

    def test_codex_adapter_recovers_model_from_state_db_when_events_omit_model(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            state_db = temp_path / "state.sqlite"
            self._write_codex_state_db(state_db, thread_id="thread-1")
            task = EvalTask(
                id="codex-state-model",
                title="Codex state model",
                repo=str(temp_path),
                commit="unused",
                language="text",
                prompt="No-op.",
            )

            def fake_runner(command, timeout_seconds):
                last_message = Path(command[command.index("--output-last-message") + 1])
                last_message.write_text("Done.", encoding="utf-8")
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=(
                        '{"type":"thread.started","thread_id":"thread-1"}\n'
                        '{"type":"turn.completed","usage":{}}\n'
                    ),
                    stderr="",
                )

            adapter = CodexCliAdapter(
                CodexCliConfig(
                    command="codex-test",
                    timeout_seconds=5,
                    codex_state_db=state_db,
                ),
                command_runner=fake_runner,
            )

            agent_run = adapter.run(task, temp_path, temp_path / "run")

        self.assertEqual(agent_run.model_name, "gpt-5.5")
        config = agent_run.agent_harness_config
        self.assertEqual(config["model_name"], "gpt-5.5")
        self.assertEqual(config["model_source"], "local_codex_state")
        self.assertEqual(config["codex_thread_id"], "thread-1")
        self.assertEqual(config["reasoning_effort"], "xhigh")
        self.assertEqual(config["model_provider"], "openai")

    def test_codex_timeout_persists_partial_events(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            task = EvalTask(
                id="codex-timeout",
                title="Codex timeout",
                repo=str(temp_path),
                commit="unused",
                language="text",
                prompt="No-op.",
            )

            def timeout_runner(command, timeout_seconds):
                raise subprocess.TimeoutExpired(
                    command,
                    timeout_seconds,
                    output='{"type":"thread.started","thread_id":"thread-1"}\n',
                    stderr="still running",
                )

            adapter = CodexCliAdapter(
                CodexCliConfig(command="codex-test", timeout_seconds=1),
                command_runner=timeout_runner,
            )

            agent_run = adapter.run(task, temp_path, temp_path / "run")

            self.assertEqual(agent_run.error, "Codex CLI timed out after 1s")
            self.assertEqual(
                (temp_path / "run" / "codex-events.jsonl").read_text(
                    encoding="utf-8"
                ),
                '{"type":"thread.started","thread_id":"thread-1"}\n',
            )

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
        self.assertEqual(result.agent_harness_config["agent_harness"], "codex")
        self.assertEqual(result.agent_harness_config["command"], str(fake_codex))
        self.assertEqual(
            result.agent_harness_config["command_identity"],
            str(fake_codex.resolve()),
        )
        self.assertEqual(result.agent_harness_config["model_name"], "gpt-test")
        self.assertEqual(result.agent_harness_config["model_source"], "explicit")
        self.assertEqual(result.agent_harness_config["profile"], "agentlab")
        self.assertEqual(result.agent_harness_config["sandbox"], "read-only")
        self.assertEqual(result.agent_harness_config["cli_version"], "codex 1.2.3")

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
            self.assertEqual(evaluation.agent_run.model_name, "gpt-event")
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["model_name"], "gpt-event")
            self.assertEqual(result["input_tokens"], 10)
            self.assertEqual(result["resource_usage"]["total_tokens"], 15)
            self.assertIsNone(result["resource_usage"]["cost_usd"])
            harness_config = result["agent_harness_config"]
            self.assertEqual(harness_config["agent_harness"], "codex")
            self.assertEqual(harness_config["agent_adapter"], "codex_cli")
            self.assertEqual(harness_config["command"], "codex-test")
            self.assertIsNone(harness_config["command_identity"])
            self.assertEqual(harness_config["model_name"], "gpt-event")
            self.assertEqual(harness_config["model_source"], "events")
            self.assertIsNone(harness_config["requested_model_name"])
            self.assertEqual(harness_config["sandbox"], "workspace-write")
            self.assertEqual(harness_config["approval_policy"], "never")
            self.assertEqual(harness_config["timeout_seconds"], 30)
            self.assertIsNone(harness_config["cli_version"])
            self.assertIsNone(
                harness_config["runtime_accountability"]["account"]
            )
            self.assertIsNone(
                harness_config["runtime_accountability"]["billing_context"]
            )
            report = evaluation.report_path.read_text(encoding="utf-8")
            self.assertIn("## Agent Harness Configuration", report)
            self.assertIn("- Command: `codex-test`", report)
            self.assertIn("- Model: `gpt-event`", report)
            self.assertIn("- Account: `unknown`", report)
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
                '{"type":"turn.completed","model":"gpt-event",'
                '"usage":{"input_tokens":10,'
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

    def _write_codex_state_db(self, path, *, thread_id):
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                create table threads (
                  id text primary key,
                  model text,
                  reasoning_effort text,
                  model_provider text,
                  source text,
                  cli_version text
                )
                """
            )
            connection.execute(
                """
                insert into threads (
                  id,
                  model,
                  reasoning_effort,
                  model_provider,
                  source,
                  cli_version
                ) values (?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    "gpt-5.5",
                    "xhigh",
                    "openai",
                    "exec",
                    "0.130.0-alpha.5",
                ),
            )


if __name__ == "__main__":
    unittest.main()
