import tempfile
import unittest
from pathlib import Path

from agentlab.review import load_review, resolve_run_dir, write_review


class ReviewTest(unittest.TestCase):
    def test_writes_and_loads_review(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            review_path = write_review(
                run_dir,
                primary_label="success_clean",
                note="Focused patch with passing checks.",
                secondary_labels=["tool_misuse"],
                evidence=["diff.patch"],
            )

            self.assertTrue(review_path.exists())
            review = load_review(run_dir)
            self.assertIsNotNone(review)
            assert review is not None
            self.assertEqual(review["primary_label"], "success_clean")
            self.assertEqual(review["secondary_labels"], ["tool_misuse"])

    def test_rejects_unknown_label(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                write_review(Path(temp), "not_a_label", "bad label")

    def test_resolves_latest_run(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp)
            (runs_dir / "20260101-old").mkdir()
            latest = runs_dir / "20260102-new"
            latest.mkdir()

            self.assertEqual(resolve_run_dir(runs_dir, "latest"), latest)


if __name__ == "__main__":
    unittest.main()
