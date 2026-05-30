import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agentlab.cli import main


class CliReviewArtifactTest(unittest.TestCase):
    def test_main_reports_invalid_review_artifacts_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            self._write_invalid_review_trial(runs_dir / "trial-invalid")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(["trials", "list", "--runs-dir", str(runs_dir)])

        self.assertEqual(status, 1)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("ERROR invalid review artifact", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_main_reports_missing_review_validity_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            run_dir = runs_dir / "trial-missing-validity"
            self._write_invalid_review_trial(run_dir)
            (run_dir / "review.json").write_text(
                json.dumps(
                    {
                        "primary_label": "success_clean",
                        "secondary_labels": [],
                        "note": "Missing persisted validity.",
                        "evidence": [],
                        "exclusion_reason": None,
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(["trials", "list", "--runs-dir", str(runs_dir)])

        self.assertEqual(status, 1)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("ERROR invalid review artifact", stderr.getvalue())
        self.assertIn("requires trial_validity", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_main_reports_non_utf8_review_artifacts_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            run_dir = runs_dir / "trial-non-utf8"
            self._write_invalid_review_trial(run_dir)
            (run_dir / "review.json").write_bytes(b"\xff")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(["trials", "list", "--runs-dir", str(runs_dir)])

        self.assertEqual(status, 1)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("ERROR review artifact must be UTF-8 JSON", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_report_digest_reports_invalid_review_artifacts_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            self._write_invalid_review_trial(runs_dir / "trial-invalid")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(
                    [
                        "report",
                        "capability-evidence-digest",
                        "--runs-dir",
                        str(runs_dir),
                    ]
                )

        self.assertEqual(status, 1)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("ERROR invalid review artifact", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_archive_excluded_reports_invalid_review_artifacts_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            self._write_invalid_review_trial(runs_dir / "trial-invalid")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(
                    [
                        "trials",
                        "archive-excluded",
                        "--runs-dir",
                        str(runs_dir),
                    ]
                )

        self.assertEqual(status, 1)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("ERROR invalid review artifact", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def _write_invalid_review_trial(self, run_dir: Path) -> None:
        run_dir.mkdir(parents=True)
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "trial_kind": "agent_trial",
                    "trial_id": run_dir.name,
                    "run_id": run_dir.name,
                    "task_id": "task-a",
                    "eval_suite": "starter",
                    "eval_type": "capability",
                    "agent_name": "codex",
                    "status": "failed",
                    "success": False,
                    "run_dir": str(run_dir),
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "review.json").write_text(
            json.dumps(
                {
                    "primary_label": "not_a_label",
                    "secondary_labels": [],
                    "note": "Invalid canonical review.",
                    "evidence": [],
                    "trial_validity": "excluded",
                    "exclusion_reason": "setup_error",
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
