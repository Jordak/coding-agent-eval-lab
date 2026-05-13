import contextlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agentlab.cli import (
    handle_doctor,
    handle_recover_codex_runtime_metadata,
    handle_run,
    handle_trials_summarize,
    _claude_code_config_from_args,
    _codex_config_from_args,
    handle_runs_list,
    _print_run_summaries,
    build_parser,
    handle_task_smoke_test,
)
from agentlab.preflight import PreflightCheck, PreflightResult


class CliOutputTest(unittest.TestCase):
    def test_module_entrypoint_returns_cli_status(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "agentlab",
                "doctor",
                "--agent",
                "claude",
                "--claude-command",
                "agentlab-claude-missing",
            ],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Claude Code CLI not found", completed.stderr)

    def test_run_parser_accepts_jobs(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "run",
                "--agent",
                "codex",
                "--task",
                "tasks/starter/example",
                "--trials",
                "5",
                "--jobs",
                "3",
            ]
        )

        self.assertEqual(args.trials, 5)
        self.assertEqual(args.jobs, 3)

    def test_top_level_help_keeps_existing_command_families(self):
        parser = build_parser()

        help_text = parser.format_help()

        for command in [
            "task",
            "doctor",
            "run",
            "runs",
            "trials",
            "report",
            "review",
            "recover",
        ]:
            self.assertIn(command, help_text)

    def test_documented_command_examples_continue_to_parse(self):
        parser = build_parser()

        commands = [
            ["run", "--agent", "manual", "--task", "tasks/starter/example"],
            ["doctor", "--agent", "codex"],
            ["doctor", "--agent", "claude"],
            [
                "task",
                "smoke-test",
                "--task",
                "tasks/starter/example",
                "--agent",
                "codex",
            ],
            ["trials", "list"],
            ["trials", "summarize"],
            [
                "review",
                "--trial",
                "latest",
                "--label",
                "success_clean",
                "--note",
                "Focused one-line fix; graders pass.",
            ],
            ["report", "capability-evidence-digest"],
            [
                "recover",
                "codex-runtime-metadata",
                "--evidence-set",
                "evidence-sets/example.json",
                "--codex-state-db",
                "state.sqlite",
                "--dry-run",
            ],
        ]

        for command in commands:
            with self.subTest(command=command):
                args = parser.parse_args(command)
                self.assertTrue(hasattr(args, "handler"))

    def test_review_parser_accepts_excluded_trial_validity(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "review",
                "--run",
                "runs/example",
                "--label",
                "dependency_issue",
                "--note",
                "Task setup failed before the agent acted.",
                "--exclude",
                "--exclusion-reason",
                "setup_error",
            ]
        )

        self.assertTrue(args.exclude)
        self.assertEqual(args.exclusion_reason, "setup_error")

    def test_report_parser_accepts_capability_evidence_digest_output(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "report",
                "capability-evidence-digest",
                "--runs-dir",
                "runs",
                "--evidence-set",
                "reports/codex-click-evidence.json",
                "--output",
                "reports/evidence-digest.md",
            ]
        )

        self.assertEqual(args.runs_dir, "runs")
        self.assertEqual(args.evidence_set, "reports/codex-click-evidence.json")
        self.assertEqual(args.output, "reports/evidence-digest.md")

    def test_report_parser_keeps_evidence_appendix_alias(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "report",
                "evidence-appendix",
                "--output",
                "reports/legacy.md",
            ]
        )

        self.assertEqual(args.output, "reports/legacy.md")

    def test_recover_parser_accepts_codex_runtime_metadata_options(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "recover",
                "codex-runtime-metadata",
                "--runs-dir",
                "runs",
                "--evidence-set",
                "evidence-sets/codex.json",
                "--codex-state-db",
                "~/.codex/state_5.sqlite",
                "--dry-run=false",
            ]
        )

        self.assertEqual(args.runs_dir, "runs")
        self.assertEqual(args.evidence_set, "evidence-sets/codex.json")
        self.assertEqual(args.codex_state_db, "~/.codex/state_5.sqlite")
        self.assertFalse(args.dry_run)

    def test_recover_parser_defaults_to_dry_run(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "recover",
                "codex-runtime-metadata",
                "--evidence-set",
                "evidence-sets/codex.json",
                "--codex-state-db",
                "~/.codex/state_5.sqlite",
            ]
        )

        self.assertTrue(args.dry_run)

    def test_task_smoke_test_parser_uses_one_agent_trial(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "task",
                "smoke-test",
                "--task",
                "tasks/starter/example",
                "--agent",
                "codex",
            ]
        )

        self.assertEqual(args.task, "tasks/starter/example")
        self.assertEqual(args.agent, "codex")
        self.assertFalse(hasattr(args, "trials"))
        self.assertFalse(hasattr(args, "jobs"))

    def test_trials_archive_excluded_parser_defaults_to_dry_run(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "trials",
                "archive-excluded",
                "--runs-dir",
                "runs",
                "--exclusion-reason",
                "setup_error",
            ]
        )

        self.assertEqual(args.runs_dir, "runs")
        self.assertEqual(args.exclusion_reason, ["setup_error"])
        self.assertFalse(args.apply)

    def test_doctor_parser_accepts_codex_preflight_options(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "doctor",
                "--agent",
                "codex",
                "--codex-command",
                "codex-test",
                "--codex-approval",
                "never",
                "--codex-timeout-seconds",
                "3",
            ]
        )

        self.assertEqual(args.agent, "codex")
        self.assertEqual(args.codex_command, "codex-test")
        self.assertEqual(args.codex_approval, "never")
        self.assertEqual(args.codex_timeout_seconds, 3)

    def test_run_parser_accepts_claude_options(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "run",
                "--agent",
                "claude",
                "--task",
                "tasks/starter/example",
                "--claude-command",
                "claude-test",
                "--claude-model",
                "sonnet",
                "--claude-permission-mode",
                "acceptEdits",
                "--claude-max-turns",
                "6",
                "--claude-allowed-tool",
                "Read",
                "--claude-allowed-tool",
                "Edit",
                "--claude-disallowed-tool",
                "Bash(git push *)",
                "--claude-timeout-seconds",
                "9",
            ]
        )

        self.assertEqual(args.agent, "claude")
        self.assertEqual(args.claude_command, "claude-test")
        self.assertEqual(args.claude_model, "sonnet")
        self.assertEqual(args.claude_permission_mode, "acceptEdits")
        self.assertEqual(args.claude_max_turns, 6)
        self.assertEqual(args.claude_allowed_tool, ["Read", "Edit"])
        self.assertEqual(args.claude_disallowed_tool, ["Bash(git push *)"])
        self.assertEqual(args.claude_timeout_seconds, 9)

    def test_handle_doctor_runs_codex_preflight(self):
        args = SimpleNamespace(
            agent="codex",
            codex_command="codex-test",
            codex_model="gpt-test",
            codex_profile="agentlab",
            codex_sandbox="read-only",
            codex_approval="never",
            codex_timeout_seconds=3,
        )
        result = PreflightResult(
            agent_name="codex",
            checks=[
                PreflightCheck(
                    name="Codex executable",
                    passed=True,
                    message="found /tmp/codex-test",
                )
            ],
        )
        stdout = io.StringIO()

        with patch(
            "agentlab.cli.doctor.run_codex_preflight",
            return_value=result,
        ) as preflight:
            with contextlib.redirect_stdout(stdout):
                status = handle_doctor(args)

        self.assertEqual(status, 0)
        self.assertEqual(preflight.call_count, 1)
        config = preflight.call_args.args[0]
        self.assertEqual(config.command, "codex-test")
        self.assertEqual(config.model, "gpt-test")
        self.assertEqual(config.profile, "agentlab")
        self.assertEqual(config.sandbox, "read-only")
        self.assertEqual(config.approval_policy, "never")
        self.assertEqual(config.timeout_seconds, 3)
        self.assertFalse(config.show_progress)
        self.assertIn("Doctor: codex", stdout.getvalue())
        self.assertIn("Preflight passed.", stdout.getvalue())

    def test_handle_recover_codex_runtime_metadata_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs_dir = root / "runs"
            run_dir = runs_dir / "trial-1"
            run_dir.mkdir(parents=True)
            state_db = root / "state.sqlite"
            self._write_codex_state_db(state_db, thread_id="thread-1")
            (run_dir / "codex-events.jsonl").write_text(
                '{"type":"thread.started","thread_id":"thread-1"}\n',
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "trial_id": "trial-1",
                        "run_id": "trial-1",
                        "run_dir": str(run_dir),
                        "agent_name": "codex",
                        "model_name": None,
                        "agent_harness_config": {
                            "agent_harness": "codex",
                            "agent_adapter": "codex_cli",
                            "model_source": "unknown",
                        },
                    }
                ),
                encoding="utf-8",
            )
            before = result_path.read_text(encoding="utf-8")
            evidence_set = root / "evidence.json"
            evidence_set.write_text(
                json.dumps({"name": "codex evidence", "trials": ["trial-1"]}),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                status = handle_recover_codex_runtime_metadata(
                    SimpleNamespace(
                        evidence_set=str(evidence_set),
                        runs_dir=str(runs_dir),
                        codex_state_db=str(state_db),
                        dry_run=True,
                    )
                )

            self.assertEqual(result_path.read_text(encoding="utf-8"), before)

        self.assertEqual(status, 0)
        self.assertIn("would_update", stdout.getvalue())
        self.assertIn("Dry run only", stdout.getvalue())

    def test_handle_recover_codex_runtime_metadata_hints_when_runs_dir_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_db = root / "state.sqlite"
            self._write_codex_state_db(state_db, thread_id="thread-1")
            evidence_set = root / "evidence.json"
            evidence_set.write_text(
                json.dumps({"name": "codex evidence", "trials": ["trial-1"]}),
                encoding="utf-8",
            )
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                status = handle_recover_codex_runtime_metadata(
                    SimpleNamespace(
                        evidence_set=str(evidence_set),
                        runs_dir=str(root / "missing-runs"),
                        codex_state_db=str(state_db),
                        dry_run=True,
                    )
                )

        self.assertEqual(status, 1)
        self.assertIn("evidence set trial result not found", stderr.getvalue())
        self.assertIn("--runs-dir does not exist", stderr.getvalue())

    def test_handle_doctor_runs_claude_preflight(self):
        args = SimpleNamespace(
            agent="claude",
            claude_command="claude-test",
            claude_model="sonnet",
            claude_permission_mode="acceptEdits",
            claude_output_format="stream-json",
            claude_max_turns=3,
            claude_allowed_tool=["Read"],
            claude_disallowed_tool=["Bash(git push *)"],
            claude_timeout_seconds=3,
            claude_session_persistence=True,
        )
        result = PreflightResult(
            agent_name="claude",
            checks=[
                PreflightCheck(
                    name="Claude Code executable",
                    passed=True,
                    message="found /tmp/claude-test",
                )
            ],
        )
        stdout = io.StringIO()

        with patch(
            "agentlab.cli.doctor.run_claude_code_preflight",
            return_value=result,
        ) as preflight:
            with contextlib.redirect_stdout(stdout):
                status = handle_doctor(args)

        self.assertEqual(status, 0)
        self.assertEqual(preflight.call_count, 1)
        config = preflight.call_args.args[0]
        self.assertEqual(config.command, "claude-test")
        self.assertEqual(config.model, "sonnet")
        self.assertEqual(config.permission_mode, "acceptEdits")
        self.assertEqual(config.output_format, "stream-json")
        self.assertEqual(config.max_turns, 3)
        self.assertEqual(config.allowed_tools, ("Read",))
        self.assertEqual(config.disallowed_tools, ("Bash(git push *)",))
        self.assertEqual(config.timeout_seconds, 3)
        self.assertFalse(config.show_progress)
        self.assertFalse(config.no_session_persistence)
        self.assertIn("Doctor: claude", stdout.getvalue())
        self.assertIn("Preflight passed.", stdout.getvalue())

    def test_codex_config_builder_centralizes_cli_options(self):
        args = SimpleNamespace(
            codex_command="codex-test",
            codex_model="gpt-test",
            codex_profile="agentlab",
            codex_sandbox="workspace-write",
            codex_approval="on-failure",
            codex_timeout_seconds=42,
        )

        config = _codex_config_from_args(args, show_progress=False)

        self.assertEqual(config.command, "codex-test")
        self.assertEqual(config.model, "gpt-test")
        self.assertEqual(config.profile, "agentlab")
        self.assertEqual(config.sandbox, "workspace-write")
        self.assertEqual(config.approval_policy, "on-failure")
        self.assertEqual(config.timeout_seconds, 42)
        self.assertFalse(config.show_progress)

    def test_claude_config_builder_centralizes_cli_options(self):
        args = SimpleNamespace(
            claude_command="claude-test",
            claude_model="sonnet",
            claude_permission_mode="acceptEdits",
            claude_output_format="stream-json",
            claude_max_turns=6,
            claude_allowed_tool=["Read", "Edit"],
            claude_disallowed_tool=["Bash(git push *)"],
            claude_timeout_seconds=42,
            claude_session_persistence=True,
        )

        config = _claude_code_config_from_args(args, show_progress=False)

        self.assertEqual(config.command, "claude-test")
        self.assertEqual(config.model, "sonnet")
        self.assertEqual(config.permission_mode, "acceptEdits")
        self.assertEqual(config.output_format, "stream-json")
        self.assertEqual(config.max_turns, 6)
        self.assertEqual(config.allowed_tools, ("Read", "Edit"))
        self.assertEqual(config.disallowed_tools, ("Bash(git push *)",))
        self.assertEqual(config.timeout_seconds, 42)
        self.assertFalse(config.show_progress)
        self.assertFalse(config.no_session_persistence)

    def test_handle_doctor_returns_failure_when_preflight_fails(self):
        args = SimpleNamespace(
            agent="codex",
            codex_command="missing-codex",
            codex_model=None,
            codex_profile=None,
            codex_sandbox="workspace-write",
            codex_approval="never",
            codex_timeout_seconds=3,
        )
        result = PreflightResult(
            agent_name="codex",
            checks=[
                PreflightCheck(
                    name="Codex executable",
                    passed=False,
                    command=["missing-codex"],
                    message="Codex CLI not found",
                )
            ],
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch("agentlab.cli.doctor.run_codex_preflight", return_value=result):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = handle_doctor(args)

        self.assertEqual(status, 1)
        self.assertIn("Doctor: codex", stdout.getvalue())
        self.assertIn("ERROR Codex executable: Codex CLI not found", stderr.getvalue())
        self.assertIn("Preflight failed.", stderr.getvalue())

    def test_runs_list_uses_normalized_review_overlay(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            run_dir = runs_dir / "trial-reviewed"
            run_dir.mkdir()
            (run_dir / "result.json").write_text(
                (
                    '{"trial_id":"trial-reviewed","task_id":"task-a",'
                    '"eval_suite":"starter","eval_type":"capability",'
                    '"agent_name":"codex","model_name":"gpt-test",'
                    '"status":"failed","success":false,'
                    '"trial_validity":"valid","exclusion_reason":null,'
                    '"files_changed":["app.py"],"lines_added":1,'
                    '"lines_deleted":0}'
                ),
                encoding="utf-8",
            )
            (run_dir / "review.json").write_text(
                (
                    '{"primary_label":"dependency_issue",'
                    '"secondary_labels":[],"note":"Invalid setup.",'
                    '"evidence":["report.md"],"trial_validity":"excluded",'
                    '"exclusion_reason":"setup_error"}'
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                status = handle_runs_list(SimpleNamespace(runs_dir=str(runs_dir)))

        output = stdout.getvalue()
        self.assertEqual(status, 0)
        self.assertIn("trial-reviewed", output)
        self.assertIn("excluded", output)
        self.assertIn("dependency_issue", output)
        self.assertIn("setup_error", output)

    def test_trials_summarize_shows_primary_and_secondary_review_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            for index in range(2):
                run_dir = runs_dir / f"trial-{index}"
                run_dir.mkdir()
                (run_dir / "result.json").write_text(
                    json.dumps(
                        {
                            "trial_id": f"trial-{index}",
                            "task_id": "task-a",
                            "eval_suite": "starter",
                            "eval_type": "capability",
                            "agent_name": "codex",
                            "model_name": "gpt-test",
                            "status": "passed",
                            "success": True,
                            "duration_ms": 100,
                            "files_changed": ["app.py"],
                            "review": {
                                "primary_label": "success_clean",
                                "secondary_labels": ["resource_inefficient"],
                                "trial_validity": "valid",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                status = handle_trials_summarize(
                    SimpleNamespace(runs_dir=str(runs_dir))
                )

        output = stdout.getvalue()
        self.assertEqual(status, 0)
        self.assertIn("primary_reviews", output)
        self.assertIn("secondary_reviews", output)
        self.assertIn("success_clean:2", output)
        self.assertIn("resource_inefficient:2", output)

    def test_run_summary_is_quiet_when_all_trials_pass(self):
        evaluation = SimpleNamespace(
            agent_run=SimpleNamespace(
                agent_name="example-agent",
                error=None,
            ),
            run_dir=Path("runs/example"),
            report_path=Path("runs/example/report.md"),
            result_path=Path("runs/example/result.json"),
            score=SimpleNamespace(tests_passed=True),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            _print_run_summaries([evaluation])

        self.assertEqual("", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())

    def test_run_summary_prints_failed_trials_and_agent_errors(self):
        evaluation = SimpleNamespace(
            agent_run=SimpleNamespace(
                agent_name="example-agent",
                error="agent executable not found",
            ),
            run_dir=Path("runs/example"),
            report_path=Path("runs/example/report.md"),
            result_path=Path("runs/example/result.json"),
            score=SimpleNamespace(tests_passed=False),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            _print_run_summaries([evaluation])

        self.assertIn("ERROR example-agent: agent executable not found", stderr.getvalue())
        self.assertIn("Failed trials:", stdout.getvalue())
        self.assertIn("- example: failed", stdout.getvalue())
        self.assertIn("Report: runs/example/report.md", stdout.getvalue())

    def test_handle_run_preserves_cli_summary_from_trial_execution(self):
        args = SimpleNamespace(
            task="tasks/starter/example",
            agent="codex",
            runs_dir="runs",
            trials=2,
            jobs=1,
            no_pause=True,
            codex_command="codex-test",
            codex_model="gpt-test",
            codex_profile="agentlab",
            codex_sandbox="read-only",
            codex_approval="on-request",
            codex_timeout_seconds=9,
        )
        task = SimpleNamespace(id="task-a")
        evaluations = [
            SimpleNamespace(
                agent_run=SimpleNamespace(agent_name="manual", error=None),
                run_dir=Path(f"runs/trial-{index}"),
                report_path=Path(f"runs/trial-{index}/report.md"),
                result_path=Path(f"runs/trial-{index}/result.json"),
                score=SimpleNamespace(tests_passed=True),
            )
            for index in range(2)
        ]
        stdout = io.StringIO()

        with patch("agentlab.cli.run.load_task", return_value=task):
            with patch("agentlab.cli.run.execute_trials", return_value=evaluations) as execute:
                with contextlib.redirect_stdout(stdout):
                    status = handle_run(args)

        self.assertEqual(status, 0)
        self.assertEqual(execute.call_count, 1)
        agent = execute.call_args.args[1](show_progress=False)
        self.assertEqual(agent.config.command, "codex-test")
        self.assertEqual(agent.config.model, "gpt-test")
        self.assertEqual(agent.config.profile, "agentlab")
        self.assertEqual(agent.config.sandbox, "read-only")
        self.assertEqual(agent.config.approval_policy, "on-request")
        self.assertEqual(agent.config.timeout_seconds, 9)
        self.assertFalse(agent.config.show_progress)
        config = execute.call_args.args[2]
        self.assertEqual(config.trials, 2)
        self.assertEqual(config.jobs, 1)
        self.assertEqual(config.agent_name, "codex")
        self.assertTrue(config.manual_parallel_allowed)
        self.assertIn(
            "Summary: 2/2 passed; pass@2=1.00; pass^2=1.00",
            stdout.getvalue(),
        )

    def test_handle_run_builds_claude_agent(self):
        args = SimpleNamespace(
            task="tasks/starter/example",
            agent="claude",
            runs_dir="runs",
            trials=1,
            jobs=1,
            no_pause=True,
            claude_command="claude-test",
            claude_model="sonnet",
            claude_permission_mode="acceptEdits",
            claude_output_format="stream-json",
            claude_max_turns=6,
            claude_allowed_tool=["Read"],
            claude_disallowed_tool=["Bash(git push *)"],
            claude_timeout_seconds=9,
            claude_session_persistence=True,
        )
        task = SimpleNamespace(id="task-a")
        evaluations = [
            SimpleNamespace(
                agent_run=SimpleNamespace(agent_name="claude", error=None),
                run_dir=Path("runs/trial-0"),
                report_path=Path("runs/trial-0/report.md"),
                result_path=Path("runs/trial-0/result.json"),
                score=SimpleNamespace(tests_passed=True),
            )
        ]

        with patch("agentlab.cli.run.load_task", return_value=task):
            with patch("agentlab.cli.run.execute_trials", return_value=evaluations) as execute:
                status = handle_run(args)

        self.assertEqual(status, 0)
        agent = execute.call_args.args[1](show_progress=False)
        self.assertEqual(agent.config.command, "claude-test")
        self.assertEqual(agent.config.model, "sonnet")
        self.assertEqual(agent.config.permission_mode, "acceptEdits")
        self.assertEqual(agent.config.max_turns, 6)
        self.assertEqual(agent.config.allowed_tools, ("Read",))
        self.assertEqual(agent.config.disallowed_tools, ("Bash(git push *)",))
        self.assertEqual(agent.config.timeout_seconds, 9)
        self.assertFalse(agent.config.show_progress)
        config = execute.call_args.args[2]
        self.assertEqual(config.agent_name, "claude")

    def test_task_smoke_test_verifies_reference_before_one_trial(self):
        args = SimpleNamespace(
            task="tasks/starter/example",
            agent="codex",
            runs_dir="runs",
            no_pause=True,
            codex_command="codex-test",
            codex_model="gpt-test",
            codex_profile=None,
            codex_sandbox="workspace-write",
            codex_approval="never",
            codex_timeout_seconds=1,
        )
        task = SimpleNamespace(id="task-a")
        verification = SimpleNamespace(
            success=True,
            files_changed=["app.py"],
            lines_added=2,
            lines_deleted=1,
        )
        evaluation = SimpleNamespace(
            agent_run=SimpleNamespace(
                agent_name="manual",
                diff_path=Path("runs/trial/diff.patch"),
                error=None,
            ),
            run_dir=Path("runs/trial"),
            report_path=Path("runs/trial/report.md"),
            result_path=Path("runs/trial/result.json"),
            score=SimpleNamespace(tests_passed=True),
        )
        stdout = io.StringIO()

        with patch("agentlab.cli.task.load_task", return_value=task):
            with patch("agentlab.cli.task.verify_reference", return_value=verification):
                with patch(
                    "agentlab.cli.task.execute_trials",
                    return_value=[evaluation],
                ) as execute:
                    with contextlib.redirect_stdout(stdout):
                        status = handle_task_smoke_test(args)

        self.assertEqual(status, 0)
        self.assertEqual(execute.call_count, 1)
        agent = execute.call_args.args[1](show_progress=True)
        self.assertEqual(agent.config.command, "codex-test")
        self.assertEqual(agent.config.model, "gpt-test")
        self.assertTrue(agent.config.show_progress)
        config = execute.call_args.args[2]
        self.assertEqual(config.trials, 1)
        self.assertEqual(config.jobs, 1)
        self.assertIn("Smoke test step 1/2", stdout.getvalue())
        self.assertIn("Smoke test step 2/2", stdout.getvalue())
        self.assertIn("Next step: inspect the report and diff", stdout.getvalue())

    def test_task_smoke_test_stops_when_reference_fails(self):
        args = SimpleNamespace(task="tasks/starter/example")
        task = SimpleNamespace(id="task-a")
        verification = SimpleNamespace(success=False)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch("agentlab.cli.task.load_task", return_value=task):
            with patch("agentlab.cli.task.verify_reference", return_value=verification):
                with patch("agentlab.cli.task._print_failed_reference_checks"):
                    with patch("agentlab.cli.task.execute_trials") as execute:
                        with contextlib.redirect_stdout(stdout):
                            with contextlib.redirect_stderr(stderr):
                                status = handle_task_smoke_test(args)

        self.assertEqual(status, 1)
        self.assertEqual(execute.call_count, 0)
        self.assertIn("ERROR reference verification failed", stderr.getvalue())

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
