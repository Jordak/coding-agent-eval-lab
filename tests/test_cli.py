import contextlib
import io
import unittest
from pathlib import Path
from types import SimpleNamespace

from agentlab.cli import _print_run_summaries


class CliOutputTest(unittest.TestCase):
    def test_run_summary_prints_agent_errors_to_stderr(self):
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
        self.assertIn("Status: failed", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
