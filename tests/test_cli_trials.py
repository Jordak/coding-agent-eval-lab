import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agentlab.cli import handle_runs_list, handle_trials_summarize


class CliTrialsOutputTest(unittest.TestCase):
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
                    '"lines_deleted":0,"input_tokens":10,'
                    '"cached_input_tokens":4,"output_tokens":5,'
                    '"reasoning_output_tokens":2}'
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
        self.assertEqual(
            _table_headers(output)[-5:-1],
            ["in_tok", "cached_tok", "out_tok", "reason_tok"],
        )
        row = _first_table_row(output)
        self.assertEqual(row["in_tok"], "10")
        self.assertEqual(row["cached_tok"], "4")
        self.assertEqual(row["out_tok"], "5")
        self.assertEqual(row["reason_tok"], "2")

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
                            "agent_harness_config": {
                                "reasoning_effort": "xhigh",
                            },
                            "status": "passed",
                            "success": True,
                            "duration_ms": 100,
                            "files_changed": ["app.py"],
                            "input_tokens": 10 + (index * 10),
                            "cached_input_tokens": 2,
                            "output_tokens": 5,
                            "reasoning_output_tokens": 3,
                        }
                    ),
                    encoding="utf-8",
                )
                (run_dir / "review.json").write_text(
                    json.dumps(
                        {
                            "primary_label": "success_clean",
                            "secondary_labels": ["resource_inefficient"],
                            "note": "Focused patch.",
                            "evidence": [],
                            "trial_validity": "valid",
                            "exclusion_reason": None,
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
        self.assertIn("accepted", output)
        self.assertIn("reason_tok", output)
        self.assertIn("io_tok_per_verified", output)
        self.assertIn("effort", output)
        self.assertIn("xhigh", output)
        self.assertIn("success_clean:2", output)
        self.assertIn("resource_inefficient:2", output)
        headers = _table_headers(output)
        token_start = headers.index("io_tok")
        self.assertEqual(
            headers[token_start : token_start + 7],
            [
                "io_tok",
                "cached_tok",
                "reason_tok",
                "io_tok_per_verified",
                "io_tok_per_accepted",
                "cached_tok_per_verified",
                "reason_tok_per_verified",
            ],
        )
        row = _first_table_row(output)
        self.assertEqual(row["io_tok"], "40")
        self.assertEqual(row["cached_tok"], "4")
        self.assertEqual(row["reason_tok"], "6")
        self.assertEqual(row["io_tok_per_verified"], "20")
        self.assertEqual(row["io_tok_per_accepted"], "20")
        self.assertEqual(row["cached_tok_per_verified"], "2")
        self.assertEqual(row["reason_tok_per_verified"], "3")

    def test_trials_summarize_shows_token_totals_when_no_trials_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            run_dir = runs_dir / "trial-failed"
            run_dir.mkdir()
            (run_dir / "result.json").write_text(
                json.dumps(
                    {
                        "trial_id": "trial-failed",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "codex",
                        "model_name": "gpt-test",
                        "agent_harness_config": {
                            "reasoning_effort": "xhigh",
                        },
                        "status": "failed",
                        "success": False,
                        "duration_ms": 100,
                        "files_changed": ["app.py"],
                        "input_tokens": 10,
                        "cached_input_tokens": 4,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 2,
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "review.json").write_text(
                json.dumps(
                    {
                        "primary_label": "bad_local_fix",
                        "secondary_labels": [],
                        "note": "Graders failed after an attempted patch.",
                        "evidence": [],
                        "trial_validity": "valid",
                        "exclusion_reason": None,
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
        self.assertIn("io_tok", output)
        self.assertIn("cached_tok", output)
        self.assertIn("reason_tok", output)
        self.assertIn("io_tok_per_verified", output)
        self.assertIn("unknown", output)
        self.assertIn("15", output)
        self.assertIn("4", output)
        self.assertIn("2", output)


def _first_table_row(output: str) -> dict[str, str]:
    lines = [line for line in output.splitlines() if line.strip()]
    headers = _table_headers(output)
    values = lines[2].split()
    return dict(zip(headers, values))


def _table_headers(output: str) -> list[str]:
    lines = [line for line in output.splitlines() if line.strip()]
    return lines[0].split()


if __name__ == "__main__":
    unittest.main()
