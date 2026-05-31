import json
import tempfile
import unittest
from pathlib import Path

from agentlab.evidence.review_artifacts import (
    ReviewArtifactError,
    load_review,
    resolve_run_dir,
    write_review,
)


class ReviewTest(unittest.TestCase):
    def test_writes_and_loads_review(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            review_path = write_review(
                run_dir,
                primary_label="success_clean",
                note="Focused patch with passing checks.",
                secondary_labels=["resource_inefficient"],
                evidence=["diff.patch"],
            )

            self.assertTrue(review_path.exists())
            review = load_review(run_dir)
            self.assertIsNotNone(review)
            assert review is not None
            self.assertEqual(review.primary_label, "success_clean")
            self.assertEqual(review.secondary_labels, ("resource_inefficient",))
            self.assertEqual(review.trial_validity, "valid")
            self.assertIsNone(review.exclusion_reason)

    def test_rejects_unknown_label(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                write_review(Path(temp), "not_a_label", "bad label")

    def test_excluded_review_requires_exclusion_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                write_review(
                    Path(temp),
                    primary_label="spec_misread",
                    note="Not a fair task run.",
                    trial_validity="excluded",
                )

    def test_excluded_review_defaults_dependency_issue_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)

            write_review(
                run_dir,
                primary_label="dependency_issue",
                note="The task environment was missing PYTHONPATH.",
                trial_validity="excluded",
            )

            review = load_review(run_dir)
            self.assertIsNotNone(review)
            assert review is not None
            self.assertEqual(review.trial_validity, "excluded")
            self.assertEqual(review.exclusion_reason, "dependency_issue")

    def test_legacy_harness_error_normalizes_to_eval_harness_error(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)

            write_review(
                run_dir,
                primary_label="dependency_issue",
                note="The evaluation harness failed before the agent acted.",
                trial_validity="excluded",
                exclusion_reason="harness_error",
            )

            review = load_review(run_dir)
            self.assertIsNotNone(review)
            assert review is not None
            self.assertEqual(review.exclusion_reason, "eval_harness_error")

    def test_review_does_not_update_result_validity_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_id": "trial-1",
                        "trial_validity": "valid",
                        "exclusion_reason": None,
                    }
                ),
                encoding="utf-8",
            )

            write_review(
                run_dir,
                primary_label="dependency_issue",
                note="The dependency install failed before the agent acted.",
                trial_validity="excluded",
                exclusion_reason="setup_error",
            )

            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["trial_validity"], "valid")
            self.assertIsNone(result["exclusion_reason"])
            self.assertNotIn("review", result)

    def test_missing_review_returns_none(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(load_review(Path(temp)))

    def test_invalid_review_artifact_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "review.json").write_text("{not json", encoding="utf-8")

            with self.assertRaises(ReviewArtifactError):
                load_review(run_dir)

    def test_non_utf8_review_artifact_raises_review_artifact_error(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "review.json").write_bytes(b"\xff")

            with self.assertRaisesRegex(ReviewArtifactError, "UTF-8 JSON"):
                load_review(run_dir)

    def test_missing_review_validity_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
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

            with self.assertRaisesRegex(
                ReviewArtifactError,
                "requires trial_validity",
            ):
                load_review(run_dir)

    def test_missing_excluded_review_reason_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / "review.json").write_text(
                json.dumps(
                    {
                        "primary_label": "dependency_issue",
                        "secondary_labels": [],
                        "note": "Missing persisted exclusion reason.",
                        "evidence": [],
                        "trial_validity": "excluded",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ReviewArtifactError,
                "requires exclusion_reason",
            ):
                load_review(run_dir)

    def test_resolves_latest_run(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            (runs_dir / "20260101-old").mkdir()
            latest = runs_dir / "20260102-new"
            latest.mkdir()

            self.assertEqual(resolve_run_dir(runs_dir, "latest"), latest)


if __name__ == "__main__":
    unittest.main()
