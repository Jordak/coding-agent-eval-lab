import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agentlab.cli import (
    handle_doctor,
    handle_run,
    _codex_config_from_args,
    handle_runs_list,
    _print_run_summaries,
    build_parser,
    handle_task_smoke_test,
)
from agentlab.preflight import PreflightCheck, PreflightResult


class CliOutputTest(unittest.TestCase):
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
                "--output",
                "reports/evidence-digest.md",
            ]
        )

        self.assertEqual(args.runs_dir, "runs")
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
            "agentlab.cli.run_codex_preflight",
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

        with patch("agentlab.cli.run_codex_preflight", return_value=result):
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

        with patch("agentlab.cli.load_task", return_value=task):
            with patch("agentlab.cli.execute_trials", return_value=evaluations) as execute:
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

        with patch("agentlab.cli.load_task", return_value=task):
            with patch("agentlab.cli.verify_reference", return_value=verification):
                with patch(
                    "agentlab.cli.execute_trials",
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

        with patch("agentlab.cli.load_task", return_value=task):
            with patch("agentlab.cli.verify_reference", return_value=verification):
                with patch("agentlab.cli._print_failed_reference_checks"):
                    with patch("agentlab.cli.execute_trials") as execute:
                        with contextlib.redirect_stdout(stdout):
                            with contextlib.redirect_stderr(stderr):
                                status = handle_task_smoke_test(args)

        self.assertEqual(status, 1)
        self.assertEqual(execute.call_count, 0)
        self.assertIn("ERROR reference verification failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
