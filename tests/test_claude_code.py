import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentlab.agents.claude_code import (
    ClaudeCodeAdapter,
    ClaudeCodeConfig,
    ClaudeCodeRuntimeFacts,
    claude_code_agent_harness_config,
    run_claude_code_preflight,
)
from agentlab.runner import run_task
from agentlab.tasks import EvalTask


class ClaudeCodeAdapterTest(unittest.TestCase):
    def test_claude_command_uses_print_mode_and_permission_controls(self):
        adapter = ClaudeCodeAdapter(
            ClaudeCodeConfig(
                command="claude-test",
                model="sonnet",
                permission_mode="acceptEdits",
                output_format="stream-json",
                max_turns=6,
                allowed_tools=("Read", "Edit"),
                disallowed_tools=("Bash(git push *)",),
            )
        )

        command = adapter._build_command("prompt")

        self.assertEqual(command[:3], ["claude-test", "-p", "prompt"])
        self.assertIn("--output-format", command)
        self.assertIn("stream-json", command)
        self.assertIn("--verbose", command)
        self.assertIn("--permission-mode", command)
        self.assertIn("acceptEdits", command)
        self.assertIn("--model", command)
        self.assertIn("sonnet", command)
        self.assertIn("--max-turns", command)
        self.assertIn("6", command)
        self.assertIn("--allowedTools", command)
        self.assertIn("Read", command)
        self.assertIn("Edit", command)
        self.assertIn("--disallowedTools", command)
        self.assertIn("Bash(git push *)", command)
        self.assertIn("--no-session-persistence", command)

    def test_claude_agent_harness_config_keeps_runtime_facts_separate(self):
        config = claude_code_agent_harness_config(
            ClaudeCodeConfig(
                command="claude-test",
                model=None,
                permission_mode="acceptEdits",
                output_format="stream-json",
                max_turns=8,
                allowed_tools=("Read", "Edit"),
                disallowed_tools=("Bash(git push *)",),
                timeout_seconds=60,
            ),
            runtime_facts=ClaudeCodeRuntimeFacts(
                command_identity="/usr/local/bin/claude-test",
                cli_version="2.1.118",
                auth_status="logged in",
            ),
            cost_usd=0.0123,
        )

        self.assertEqual(config["agent_harness"], "claude_code")
        self.assertEqual(config["agent_adapter"], "claude_code_cli")
        self.assertEqual(config["command"], "claude-test")
        self.assertEqual(config["command_identity"], "/usr/local/bin/claude-test")
        self.assertIsNone(config["model_name"])
        self.assertEqual(config["model_source"], "unknown")
        self.assertEqual(config["permission_mode"], "acceptEdits")
        self.assertEqual(config["output_format"], "stream-json")
        self.assertEqual(config["max_turns"], 8)
        self.assertEqual(config["allowed_tools"], ["Read", "Edit"])
        self.assertEqual(config["disallowed_tools"], ["Bash(git push *)"])
        self.assertEqual(config["timeout_seconds"], 60)
        self.assertEqual(config["cli_version"], "2.1.118")
        self.assertEqual(config["auth_status"], "logged in")
        self.assertEqual(config["runtime_accountability"]["cost_usd"], 0.0123)

    def test_missing_claude_cli_error_points_to_portable_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            task = EvalTask(
                id="missing-claude",
                title="Missing Claude",
                repo=str(temp_path),
                commit="unused",
                language="text",
                prompt="No-op.",
            )
            adapter = ClaudeCodeAdapter(
                ClaudeCodeConfig(
                    command="agentlab-claude-missing",
                    timeout_seconds=1,
                )
            )

            agent_run = adapter.run(task, temp_path, temp_path / "run")

            assert agent_run.error is not None
            self.assertIn("Claude Code CLI not found", agent_run.error)
            self.assertIn("--claude-command", agent_run.error)

    def test_claude_preflight_runs_version_auth_and_print_help_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            fake_claude = temp_path / "fake-claude"
            fake_claude.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_claude.chmod(0o755)
            commands = []

            def fake_runner(command, timeout_seconds):
                commands.append(command)
                if "--version" in command:
                    return subprocess.CompletedProcess(
                        args=command,
                        returncode=0,
                        stdout="2.1.118\n",
                        stderr="",
                    )
                if command[1:3] == ["auth", "status"]:
                    return subprocess.CompletedProcess(
                        args=command,
                        returncode=0,
                        stdout=(
                            '{"loggedIn":true,"authMethod":"oauth",'
                            '"apiProvider":"firstParty"}\n'
                        ),
                        stderr="",
                    )
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="Usage: claude [options]\n",
                    stderr="",
                )

            result = run_claude_code_preflight(
                ClaudeCodeConfig(
                    command=str(fake_claude),
                    model="sonnet",
                    permission_mode="acceptEdits",
                    max_turns=3,
                ),
                timeout_seconds=3,
                command_runner=fake_runner,
            )

        self.assertTrue(result.passed)
        self.assertEqual(commands[0], [str(fake_claude), "--version"])
        self.assertEqual(commands[1], [str(fake_claude), "auth", "status"])
        print_help_command = commands[2]
        self.assertEqual(print_help_command[:3], [str(fake_claude), "-p", "__agentlab_preflight__"])
        self.assertIn("--output-format", print_help_command)
        self.assertIn("--verbose", print_help_command)
        self.assertIn("--permission-mode", print_help_command)
        self.assertIn("--model", print_help_command)
        self.assertIn("--max-turns", print_help_command)
        self.assertEqual(print_help_command[-1], "--help")
        self.assertEqual(result.agent_harness_config["agent_harness"], "claude_code")
        self.assertEqual(result.agent_harness_config["command"], str(fake_claude))
        self.assertEqual(
            result.agent_harness_config["command_identity"],
            str(fake_claude.resolve()),
        )
        self.assertEqual(result.agent_harness_config["model_name"], "sonnet")
        self.assertEqual(result.agent_harness_config["model_source"], "explicit")
        self.assertEqual(result.agent_harness_config["permission_mode"], "acceptEdits")
        self.assertEqual(result.agent_harness_config["cli_version"], "2.1.118")
        self.assertEqual(
            result.agent_harness_config["auth_status"],
            "loggedIn=true authMethod=oauth apiProvider=firstParty",
        )
        self.assertEqual(
            result.checks[2].message,
            "loggedIn=true authMethod=oauth apiProvider=firstParty",
        )

    def test_claude_adapter_runs_command_and_captures_patch(self):
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
                id="claude-fixture",
                title="Claude fixture",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Change answer.txt to contain after.",
                environment={"AGENTLAB_TEST_SENTINEL": "from-env"},
                test=[
                    (
                        f"{sys.executable} -c "
                        "\"from pathlib import Path; "
                        "assert Path('answer.txt').read_text() == 'after\\n'\""
                    )
                ],
            )
            adapter = ClaudeCodeAdapter(
                ClaudeCodeConfig(
                    command="claude-test",
                    model="requested-sonnet",
                    timeout_seconds=30,
                ),
                command_runner=self._fake_claude_runner,
            )

            evaluation = run_task(task, adapter, temp_path / "runs")

            self.assertTrue(evaluation.score.tests_passed)
            self.assertEqual(evaluation.agent_run.agent_name, "claude")
            self.assertEqual(evaluation.agent_run.files_changed, ["answer.txt"])
            self.assertTrue((evaluation.run_dir / "claude-events.jsonl").exists())
            self.assertTrue((evaluation.run_dir / "claude-final-message.md").exists())
            self.assertEqual(evaluation.agent_run.input_tokens, 10)
            self.assertEqual(evaluation.agent_run.cached_input_tokens, 4)
            self.assertEqual(evaluation.agent_run.output_tokens, 5)
            self.assertEqual(evaluation.agent_run.cost_usd, 0.0123)
            self.assertEqual(evaluation.agent_run.model_name, "claude-sonnet-4-6")
            result = json.loads(evaluation.result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["model_name"], "claude-sonnet-4-6")
            self.assertEqual(result["resource_usage"]["total_tokens"], 15)
            self.assertEqual(result["resource_usage"]["cost_usd"], 0.0123)
            harness_config = result["agent_harness_config"]
            self.assertEqual(harness_config["agent_harness"], "claude_code")
            self.assertEqual(harness_config["agent_adapter"], "claude_code_cli")
            self.assertEqual(harness_config["command"], "claude-test")
            self.assertIsNone(harness_config["command_identity"])
            self.assertEqual(harness_config["model_name"], "claude-sonnet-4-6")
            self.assertEqual(harness_config["model_source"], "events")
            self.assertEqual(harness_config["requested_model_name"], "requested-sonnet")
            self.assertEqual(harness_config["permission_mode"], "acceptEdits")
            self.assertEqual(harness_config["output_format"], "stream-json")
            self.assertIsNone(harness_config["cli_version"])
            report = evaluation.report_path.read_text(encoding="utf-8")
            self.assertIn("## Agent Harness Configuration", report)
            self.assertIn("- Command: `claude-test`", report)
            self.assertIn("- Model: `claude-sonnet-4-6`", report)
            self.assertIn("- Requested model: `requested-sonnet`", report)
            self.assertIn("- Cost USD: `0.0123`", report)
            transcript = evaluation.agent_run.transcript_path.read_text(
                encoding="utf-8"
            )
            self.assertIn("claude-test -p <prompt>", transcript)
            self.assertIn("## Final Message", transcript)
            self.assertIn("Done.", transcript)
            self.assertIn(
                "+after",
                evaluation.agent_run.diff_path.read_text(encoding="utf-8"),
            )

    def _fake_claude_runner(self, command, timeout_seconds, cwd, env):
        self.assertEqual(env.get("AGENTLAB_TEST_SENTINEL"), "from-env")
        (cwd / "answer.txt").write_text("after\n", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=(
                '{"type":"assistant","message":{"id":"msg_1",'
                '"model":"claude-sonnet-4-6",'
                '"usage":{"input_tokens":10,"cache_read_input_tokens":4,'
                '"output_tokens":5}}}\n'
                '{"type":"result","subtype":"success","result":"Done.",'
                '"usage":{"input_tokens":10,"cache_read_input_tokens":4,'
                '"output_tokens":5},"total_cost_usd":0.0123,'
                '"session_id":"session-1","num_turns":2}\n'
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
