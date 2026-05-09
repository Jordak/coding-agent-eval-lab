import unittest

from agentlab.evidence import render_capability_evidence_digest


class CapabilityEvidenceDigestTest(unittest.TestCase):
    def test_renders_aggregate_and_trial_evidence(self):
        digest = render_capability_evidence_digest(
            [
                {
                    "trial_id": "trial-pass",
                    "task_id": "task-a",
                    "eval_suite": "starter",
                    "eval_type": "regression",
                    "agent_name": "codex",
                    "model_name": "model-a",
                    "status": "passed",
                    "success": True,
                    "duration_ms": 100,
                    "files_changed": ["app.py"],
                    "lines_added": 5,
                    "lines_deleted": 1,
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "reasoning_output_tokens": 2,
                    "cost_usd": None,
                    "review": {
                        "primary_label": "success_clean",
                        "secondary_labels": ["resource_inefficient"],
                        "trial_validity": "valid",
                    },
                    "report_path": "runs/trial-pass/report.md",
                    "transcript_path": "runs/trial-pass/transcript.md",
                    "diff_path": "runs/trial-pass/diff.patch",
                    "run_dir": "runs/trial-pass",
                },
                {
                    "trial_id": "trial-excluded",
                    "task_id": "task-a",
                    "eval_suite": "starter",
                    "eval_type": "regression",
                    "agent_name": "codex",
                    "model_name": "model-a",
                    "status": "failed",
                    "success": False,
                    "duration_ms": 999,
                    "files_changed": ["app.py", "env.py"],
                    "lines_added": 500,
                    "lines_deleted": 200,
                    "review": {
                        "primary_label": "dependency_issue",
                        "trial_validity": "excluded",
                        "exclusion_reason": "setup_error",
                    },
                    "report_path": "runs/trial-excluded/report.md",
                    "run_dir": "runs/trial-excluded",
                },
            ]
        )

        self.assertIn("# Capability Evidence Digest", digest)
        self.assertIn("Primary Review Labels", digest)
        self.assertIn("Secondary Review Labels", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | 2 | 1 | 1 | 1 | 1.00 | 1.00 | 1.00 | 100 | 1 | 5 | 1 | success_clean:1 | resource_inefficient:1 | setup_error:1 |", digest)
        self.assertIn("| trial-pass | task-a | codex | model-a | passed | valid | success_clean | resource_inefficient |", digest)
        self.assertIn("| 1 | 5 | 1 | 10 | 5 | 2 | unknown | 100 |", digest)
        self.assertIn("| trial-excluded | task-a | codex | model-a | failed | excluded | dependency_issue |  | setup_error |", digest)
        self.assertIn("[report](runs/trial-pass/report.md)", digest)
        self.assertIn("[transcript](runs/trial-pass/transcript.md)", digest)
        self.assertIn("[diff](runs/trial-pass/diff.patch)", digest)
        self.assertIn("[result](runs/trial-pass/result.json)", digest)


if __name__ == "__main__":
    unittest.main()
