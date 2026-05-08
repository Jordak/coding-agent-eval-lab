import json
import tempfile
import unittest
from pathlib import Path

from agentlab.results import load_results


class ResultsTest(unittest.TestCase):
    def test_load_results_backfills_line_metrics_from_diff_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            (run_dir / "diff.patch").write_text(
                """diff --git a/app.txt b/app.txt
--- a/app.txt
+++ b/app.txt
@@ -1 +1,2 @@
-before
+after
+new
""",
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                        "diff_path": str(run_dir / "diff.patch"),
                        "outcome": {},
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            self.assertEqual(result["lines_added"], 2)
            self.assertEqual(result["lines_deleted"], 1)
            self.assertEqual(result["outcome"]["lines_added"], 2)
            self.assertEqual(result["outcome"]["lines_deleted"], 1)


if __name__ == "__main__":
    unittest.main()
