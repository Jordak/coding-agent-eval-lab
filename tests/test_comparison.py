import unittest

from agentlab.comparison import (
    ComparisonEvidenceSource,
    render_comparison_evidence_digest,
)


class ComparisonEvidenceDigestTest(unittest.TestCase):
    def test_renders_task_aligned_multi_harness_evidence(self):
        digest = render_comparison_evidence_digest(
            [
                ComparisonEvidenceSource(
                    name="codex high",
                    description="High-effort Codex baseline.",
                    source_path="evidence-sets/codex.json",
                    selected_entries=3,
                    selected_result_files=3,
                    results=[
                        _result(
                            "codex-a-pass",
                            task_id="task-a",
                            agent_name="codex",
                            model_name="gpt-5.5",
                            reasoning_effort="xhigh",
                            success=True,
                            files_changed=["app.py"],
                            lines_added=5,
                            lines_deleted=1,
                            input_tokens=100,
                            cached_input_tokens=20,
                            output_tokens=30,
                            reasoning_output_tokens=10,
                            cost_usd=None,
                            primary_label="success_clean",
                            secondary_labels=["resource_inefficient"],
                        ),
                        _result(
                            "codex-a-fail",
                            task_id="task-a",
                            agent_name="codex",
                            model_name="gpt-5.5",
                            reasoning_effort="xhigh",
                            success=False,
                            files_changed=["app.py", "tests.py"],
                            lines_added=7,
                            lines_deleted=3,
                            input_tokens=None,
                            cached_input_tokens=None,
                            output_tokens=25,
                            reasoning_output_tokens=8,
                            cost_usd=None,
                            primary_label="bad_local_fix",
                            secondary_labels=["test_gap"],
                        ),
                        _result(
                            "codex-b-pass",
                            task_id="task-b",
                            agent_name="codex",
                            model_name="gpt-5.5",
                            reasoning_effort="xhigh",
                            success=True,
                            cost_usd=0.125,
                            primary_label="success_clean",
                        ),
                    ],
                ),
                ComparisonEvidenceSource(
                    name="claude haiku",
                    description="Small Claude Code baseline.",
                    source_path="evidence-sets/claude.json",
                    selected_entries=3,
                    selected_result_files=3,
                    results=[
                        _result(
                            "claude-a-fail",
                            task_id="task-a",
                            agent_name="claude",
                            model_name="claude-haiku",
                            success=False,
                            input_tokens=50,
                            output_tokens=60,
                            cost_usd=0.25,
                            primary_label="bad_local_fix",
                            secondary_labels=["test_gap"],
                        ),
                        _result(
                            "claude-a-excluded",
                            task_id="task-a",
                            agent_name="claude",
                            model_name="claude-haiku",
                            success=False,
                            trial_validity="excluded",
                            exclusion_reason="setup_error",
                            primary_label="dependency_issue",
                        ),
                        _result(
                            "claude-b-pass",
                            task_id="task-b",
                            agent_name="claude",
                            model_name=None,
                            success=True,
                            input_tokens=None,
                            output_tokens=None,
                            cost_usd=None,
                            primary_label="success_clean",
                        ),
                    ],
                ),
            ]
        )

        self.assertIn("# Comparison Evidence Digest", digest)
        self.assertIn("| codex high | evidence-sets/codex.json |", digest)
        self.assertIn("| claude haiku | evidence-sets/claude.json |", digest)
        self.assertIn(
            "| task-a | codex high | starter | regression | codex | gpt-5.5 | xhigh | 2 | 2 | 0 | 1 | 0.50 | 1.00 | 0.00 |",
            digest,
        )
        self.assertIn(
            "| 100 (1/2 known) | 20 (1/2 known) | 55 | 18 | unknown | bad_local_fix:1, success_clean:1 | resource_inefficient:1, test_gap:1 |  | input_tokens:1, cached_input_tokens:1, cost_usd:2 |",
            digest,
        )
        self.assertIn(
            "| task-a | claude haiku | starter | regression | claude | claude-haiku | unknown | 2 | 1 | 1 | 0 | 0.00 | 0.00 | 0.00 |",
            digest,
        )
        self.assertIn(
            "| 50 | unknown | 60 | unknown | 0.25 | bad_local_fix:1 | test_gap:1 | setup_error:1 | reasoning_effort:2, cached_input_tokens:1, reasoning_output_tokens:1 |",
            digest,
        )
        self.assertIn(
            "| task-b | claude haiku | starter | regression | claude | unknown | unknown | 1 | 1 | 0 | 1 | 1.00 | 1.00 | 1.00 |",
            digest,
        )
        self.assertIn(
            "model_name:1, reasoning_effort:1, input_tokens:1, cached_input_tokens:1, output_tokens:1, reasoning_output_tokens:1, cost_usd:1",
            digest,
        )


def _result(
    trial_id,
    *,
    task_id,
    agent_name,
    model_name,
    success,
    reasoning_effort=None,
    trial_validity="valid",
    exclusion_reason=None,
    files_changed=None,
    lines_added=1,
    lines_deleted=0,
    input_tokens=None,
    cached_input_tokens=None,
    output_tokens=None,
    reasoning_output_tokens=None,
    cost_usd=None,
    primary_label="success_clean",
    secondary_labels=None,
):
    result = {
        "trial_kind": "agent_trial",
        "trial_id": trial_id,
        "run_id": trial_id,
        "task_id": task_id,
        "eval_suite": "starter",
        "eval_type": "regression",
        "agent_name": agent_name,
        "model_name": model_name,
        "agent_harness_config": {},
        "status": "passed" if success else "failed",
        "success": success,
        "trial_validity": trial_validity,
        "exclusion_reason": exclusion_reason,
        "duration_ms": 100,
        "files_changed": files_changed or ["app.py"],
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning_output_tokens,
        "cost_usd": cost_usd,
        "review": {
            "primary_label": primary_label,
            "secondary_labels": secondary_labels or [],
            "trial_validity": trial_validity,
            "exclusion_reason": exclusion_reason,
        },
        "run_dir": f"runs/{trial_id}",
    }
    if reasoning_effort is not None:
        result["agent_harness_config"]["reasoning_effort"] = reasoning_effort
    return result


if __name__ == "__main__":
    unittest.main()
