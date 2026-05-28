import json
import tempfile
import unittest
from pathlib import Path

from agentlab.evidence import render_capability_evidence_digest
from agentlab.outcome_evidence import (
    load_outcome_evidence,
    normalize_outcome_evidence,
)
from agentlab.summary import summarize_trials


class OutcomeEvidenceTest(unittest.TestCase):
    def test_loads_current_result_metadata_into_normalized_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-current"
            run_dir.mkdir()
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "trial_id": "trial-current",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "codex",
                        "model_name": "gpt-test",
                        "status": "passed",
                        "success": True,
                        "trial_validity": "valid",
                        "exclusion_reason": None,
                        "outcome": {
                            "status": "passed",
                            "files_changed": ["app.py"],
                            "n_files_changed": 1,
                            "lines_added": 2,
                            "lines_deleted": 1,
                        },
                        "resource_usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 4,
                            "output_tokens": 5,
                            "reasoning_output_tokens": 2,
                            "total_tokens": 15,
                            "cost_usd": None,
                        },
                        "run_dir": str(run_dir),
                    }
                ),
                encoding="utf-8",
            )

            evidence = load_outcome_evidence(result_path)

            self.assertIsNotNone(evidence)
            assert evidence is not None
            result = evidence.to_result_dict()
            self.assertEqual(result["trial_id"], "trial-current")
            self.assertEqual(result["outcome"]["status"], "passed")
            self.assertEqual(result["files_changed"], ["app.py"])
            self.assertEqual(result["n_files_changed"], 1)
            self.assertEqual(result["resource_usage"]["total_tokens"], 15)

    def test_loads_older_result_metadata_with_edit_and_resource_backfills(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-old"
            run_dir.mkdir()
            (run_dir / "diff.patch").write_text(
                """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
-before
+after
+new
""",
                encoding="utf-8",
            )
            (run_dir / "codex-events.jsonl").write_text(
                '{"type":"turn.completed","usage":{"input_tokens":7,'
                '"cached_input_tokens":3,"output_tokens":11,'
                '"reasoning_output_tokens":5,"estimated_cost_usd":0.02}}\n',
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "run_id": "trial-old",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "codex",
                        "model_name": "gpt-test",
                        "success": False,
                        "run_dir": str(run_dir),
                    }
                ),
                encoding="utf-8",
            )

            evidence = load_outcome_evidence(result_path)

            self.assertIsNotNone(evidence)
            assert evidence is not None
            result = evidence.to_result_dict()
            self.assertEqual(result["trial_id"], "trial-old")
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["files_changed"], ["app.py"])
            self.assertEqual(result["n_files_changed"], 1)
            self.assertEqual(result["lines_added"], 2)
            self.assertEqual(result["lines_deleted"], 1)
            self.assertEqual(result["outcome"]["lines_added"], 2)
            self.assertEqual(result["input_tokens"], 7)
            self.assertEqual(result["output_tokens"], 11)
            self.assertEqual(result["resource_usage"]["total_tokens"], 18)
            self.assertEqual(result["cost_usd"], 0.02)

    def test_human_review_outcome_overlay_feeds_summary_and_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-reviewed"
            run_dir.mkdir()
            (run_dir / "result.json").write_text(
                json.dumps(
                    {
                        "trial_id": "trial-reviewed",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "codex",
                        "model_name": "gpt-test",
                        "status": "failed",
                        "success": False,
                        "trial_validity": "valid",
                        "exclusion_reason": None,
                        "duration_ms": 999,
                        "files_changed": ["app.py", "env.py"],
                        "lines_added": 50,
                        "lines_deleted": 10,
                        "run_dir": str(run_dir),
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "review.json").write_text(
                json.dumps(
                    {
                        "primary_label": "dependency_issue",
                        "secondary_labels": [],
                        "note": "Task setup failed before the Trial was fair.",
                        "evidence": ["report.md"],
                        "trial_validity": "excluded",
                        "exclusion_reason": "setup_error",
                    }
                ),
                encoding="utf-8",
            )

            evidence = load_outcome_evidence(run_dir / "result.json")

            self.assertIsNotNone(evidence)
            assert evidence is not None
            result = evidence.to_result_dict()
            summary = summarize_trials([evidence])[0]
            digest = render_capability_evidence_digest([evidence])

            self.assertEqual(result["trial_validity"], "excluded")
            self.assertEqual(result["exclusion_reason"], "setup_error")
            self.assertEqual(summary.total_trials, 1)
            self.assertEqual(summary.trials, 0)
            self.assertEqual(summary.excluded_trials, 1)
            self.assertEqual(summary.exclusion_reasons, {"setup_error": 1})
            self.assertIn(
                "| trial-reviewed | task-a | codex | gpt-test | unknown | failed | "
                "excluded | dependency_issue |  | setup_error |",
                digest,
            )

    def test_normalized_count_uses_backfilled_n_files_for_old_artifacts(self):
        evidence = normalize_outcome_evidence(
            {
                "trial_id": "trial-count-only",
                "success": True,
                "outcome": {"n_files_changed": 3},
            }
        )

        self.assertEqual(evidence.files_changed_count, 3)

    def test_exposes_reporting_facts_without_raw_review_shape(self):
        evidence = normalize_outcome_evidence(
            {
                "trial_id": "trial-reporting",
                "success": True,
                "agent_harness_config": {"reasoning_effort": "xhigh"},
                "files_changed": ["app.py", "tests.py"],
                "input_tokens": 10,
                "output_tokens": 5,
                "reasoning_output_tokens": 2,
                "cost_usd": 0.01,
                "run_dir": "runs/trial-reporting",
                "review": {
                    "primary_label": "success_clean",
                    "secondary_labels": ["resource_inefficient"],
                    "trial_validity": "valid",
                },
            }
        )

        self.assertTrue(evidence.is_valid_trial)
        self.assertEqual(evidence.primary_review_label, "success_clean")
        self.assertEqual(
            evidence.secondary_review_labels,
            ["resource_inefficient"],
        )
        self.assertEqual(evidence.reasoning_effort, "xhigh")
        self.assertEqual(evidence.reasoning_effort_display, "xhigh")
        self.assertEqual(evidence.model_name_display, "unknown")
        self.assertEqual(evidence.files_changed_count, 2)
        self.assertEqual(evidence.input_tokens, 10)
        self.assertEqual(evidence.output_tokens, 5)
        self.assertEqual(evidence.reasoning_output_tokens, 2)
        self.assertEqual(evidence.cost_usd, 0.01)
        self.assertEqual(
            evidence.result_path,
            "runs/trial-reporting/result.json",
        )


if __name__ == "__main__":
    unittest.main()
