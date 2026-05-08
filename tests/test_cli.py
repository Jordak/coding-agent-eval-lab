import contextlib
import io
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agentlab.cli import _print_run_summaries, _run_trials, build_parser


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

    def test_parallel_trials_disable_per_agent_progress(self):
        lock = threading.Lock()
        progress_values = []

        def fake_run_task(task, agent, runs_dir):
            with lock:
                index = len(progress_values)
                progress_values.append(agent.config.show_progress)
            return SimpleNamespace(
                agent_run=SimpleNamespace(agent_name="codex", error=None),
                run_dir=Path(runs_dir) / f"run-{index}",
                report_path=Path(runs_dir) / f"run-{index}" / "report.md",
                result_path=Path(runs_dir) / f"run-{index}" / "result.json",
                score=SimpleNamespace(tests_passed=True),
            )

        with tempfile.TemporaryDirectory() as temp:
            args = SimpleNamespace(
                agent="codex",
                codex_command="codex-test",
                codex_model=None,
                codex_profile=None,
                codex_sandbox="workspace-write",
                codex_approval="never",
                codex_timeout_seconds=1,
                jobs=2,
                no_pause=True,
                runs_dir=temp,
                trials=3,
            )
            stdout = io.StringIO()

            with patch("agentlab.cli.run_task", side_effect=fake_run_task):
                with contextlib.redirect_stdout(stdout):
                    evaluations = _run_trials(SimpleNamespace(id="task"), args)

        self.assertEqual(len(evaluations), 3)
        self.assertEqual(progress_values, [False, False, False])
        self.assertNotIn("Completed trial", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
