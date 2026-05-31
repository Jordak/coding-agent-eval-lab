import unittest

from agentlab.evidence.human_review import (
    create_human_review_outcome,
    human_review_outcome_from_mapping,
)
from agentlab.evidence.outcome import normalize_outcome_evidence
from agentlab.evidence.summary import summarize_trials


class SummaryTest(unittest.TestCase):
    def test_summarizes_pass_at_k_and_pass_caret_k(self):
        results = [
            self._result(success=False, duration_ms=100, files_changed=[]),
            self._result(
                success=True,
                duration_ms=300,
                files_changed=["a.py", "b.py"],
                lines_added=8,
                lines_deleted=3,
            ),
            self._result(
                success=True,
                duration_ms=200,
                files_changed=["a.py"],
                lines_added=4,
                lines_deleted=1,
            ),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.trials, 3)
        self.assertEqual(summary.passes, 2)
        self.assertAlmostEqual(summary.pass_rate, 2 / 3)
        self.assertEqual(summary.pass_at_k, 1.0)
        self.assertEqual(summary.pass_caret_k, 0.0)
        self.assertEqual(summary.median_duration_ms, 200)
        self.assertEqual(summary.median_files_changed, 1)
        self.assertEqual(summary.median_lines_added, 4)
        self.assertEqual(summary.median_lines_deleted, 1)

    def test_summarizes_tokens_per_verified_and_accepted_result(self):
        results = [
            self._result(
                success=False,
                input_tokens=100,
                output_tokens=20,
                cached_input_tokens=4,
                reasoning_output_tokens=2,
            ),
            self._result(
                success=True,
                input_tokens=10,
                output_tokens=5,
                cached_input_tokens=1,
                reasoning_output_tokens=1,
                review={
                    "primary_label": "success_clean",
                    "secondary_labels": [],
                    "trial_validity": "valid",
                },
            ),
            self._result(
                success=True,
                input_tokens=30,
                output_tokens=10,
                cached_input_tokens=5,
                reasoning_output_tokens=3,
                review={
                    "primary_label": "success_messy",
                    "secondary_labels": [],
                    "trial_validity": "valid",
                },
            ),
            self._result(
                success=True,
                input_tokens=999,
                output_tokens=999,
                cached_input_tokens=999,
                reasoning_output_tokens=999,
                review={
                    "primary_label": "dependency_issue",
                    "secondary_labels": [],
                    "trial_validity": "excluded",
                    "exclusion_reason": "setup_error",
                },
            ),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.passes, 2)
        self.assertEqual(summary.accepted_results, 1)
        self.assertEqual(summary.total_input_output_tokens, 175)
        self.assertEqual(summary.total_cached_input_tokens, 10)
        self.assertEqual(summary.total_reasoning_output_tokens, 6)
        self.assertEqual(summary.input_output_tokens_per_verified_result, 87.5)
        self.assertEqual(summary.input_output_tokens_per_accepted_result, 175)
        self.assertEqual(summary.cached_input_tokens_per_verified_result, 5)
        self.assertEqual(summary.reasoning_output_tokens_per_verified_result, 3)

    def test_token_per_result_metrics_are_unknown_when_required_tokens_missing(self):
        results = [
            self._result(
                success=True,
                input_tokens=10,
                output_tokens=None,
                cached_input_tokens=3,
                reasoning_output_tokens=5,
            ),
            self._result(
                success=False,
                input_tokens=999,
                output_tokens=999,
                review={
                    "primary_label": "dependency_issue",
                    "secondary_labels": [],
                    "trial_validity": "excluded",
                    "exclusion_reason": "setup_error",
                },
            ),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.trials, 1)
        self.assertEqual(summary.passes, 1)
        self.assertIsNone(summary.total_input_output_tokens)
        self.assertEqual(summary.total_cached_input_tokens, 3)
        self.assertEqual(summary.total_reasoning_output_tokens, 5)
        self.assertIsNone(summary.input_output_tokens_per_verified_result)
        self.assertIsNone(summary.input_output_tokens_per_accepted_result)
        self.assertEqual(summary.cached_input_tokens_per_verified_result, 3)
        self.assertEqual(summary.reasoning_output_tokens_per_verified_result, 5)

    def test_token_per_result_metrics_are_unknown_when_no_success_denominator(self):
        results = [
            self._result(
                success=False,
                input_tokens=10,
                output_tokens=5,
                cached_input_tokens=4,
                reasoning_output_tokens=2,
            ),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.trials, 1)
        self.assertEqual(summary.passes, 0)
        self.assertEqual(summary.accepted_results, 0)
        self.assertEqual(summary.total_input_output_tokens, 15)
        self.assertEqual(summary.total_cached_input_tokens, 4)
        self.assertEqual(summary.total_reasoning_output_tokens, 2)
        self.assertIsNone(summary.input_output_tokens_per_verified_result)
        self.assertIsNone(summary.input_output_tokens_per_accepted_result)
        self.assertIsNone(summary.cached_input_tokens_per_verified_result)
        self.assertIsNone(summary.reasoning_output_tokens_per_verified_result)

    def test_pass_caret_k_requires_all_trials_to_pass(self):
        results = [
            self._result(success=True, duration_ms=100, files_changed=[]),
            self._result(success=True, duration_ms=200, files_changed=[]),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.pass_at_k, 1.0)
        self.assertEqual(summary.pass_caret_k, 1.0)

    def test_groups_by_task_agent_model_and_effort(self):
        results = [
            self._result(
                task_id="task-a",
                agent_name="codex",
                model_name="m1",
                reasoning_effort="high",
            ),
            self._result(
                task_id="task-a",
                agent_name="codex",
                model_name="m1",
                reasoning_effort="xhigh",
            ),
            self._result(
                task_id="task-a",
                agent_name="codex",
                model_name="m2",
                reasoning_effort="high",
            ),
            self._result(
                task_id="task-b",
                agent_name="codex",
                model_name="m1",
                reasoning_effort="high",
            ),
        ]

        summaries = summarize_trials(results)

        self.assertEqual(len(summaries), 4)

    def test_excludes_invalid_trials_from_pass_metrics(self):
        results = [
            self._result(success=True, duration_ms=100, files_changed=["a.py"]),
            self._result(
                success=False,
                duration_ms=999,
                files_changed=["a.py", "b.py", "c.py"],
                lines_added=999,
                lines_deleted=999,
                human_review_outcome=create_human_review_outcome(
                    primary_label="dependency_issue",
                    note="Task setup failed before the Trial was fair.",
                    secondary_labels=["resource_inefficient"],
                    trial_validity="excluded",
                    exclusion_reason="setup_error",
                ),
            ),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.total_trials, 2)
        self.assertEqual(summary.trials, 1)
        self.assertEqual(summary.excluded_trials, 1)
        self.assertEqual(summary.passes, 1)
        self.assertEqual(summary.pass_rate, 1.0)
        self.assertEqual(summary.pass_at_k, 1.0)
        self.assertEqual(summary.pass_caret_k, 1.0)
        self.assertEqual(summary.median_duration_ms, 100)
        self.assertEqual(summary.median_files_changed, 1)
        self.assertEqual(summary.median_lines_added, 0)
        self.assertEqual(summary.median_lines_deleted, 0)
        self.assertEqual(summary.review_labels, {})
        self.assertEqual(summary.secondary_review_labels, {})
        self.assertEqual(summary.exclusion_reasons, {"setup_error": 1})

    def test_counts_secondary_review_labels_separately_from_primary_labels(self):
        results = [
            self._result(
                success=True,
                human_review_outcome=create_human_review_outcome(
                    primary_label="success_clean",
                    note="Focused patch.",
                    secondary_labels=["resource_inefficient"],
                ),
            ),
            self._result(
                success=True,
                human_review_outcome=create_human_review_outcome(
                    primary_label="success_clean",
                    note="Focused patch.",
                    secondary_labels=["resource_inefficient"],
                ),
            ),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.trials, 2)
        self.assertEqual(summary.passes, 2)
        self.assertEqual(summary.pass_rate, 1.0)
        self.assertEqual(summary.pass_at_k, 1.0)
        self.assertEqual(summary.pass_caret_k, 1.0)
        self.assertEqual(summary.review_labels, {"success_clean": 2})
        self.assertEqual(
            summary.secondary_review_labels,
            {"resource_inefficient": 2},
        )

    def _result(
        self,
        success=True,
        duration_ms=0,
        files_changed=None,
        task_id="task-a",
        agent_name="codex",
        model_name="m1",
        reasoning_effort=None,
        lines_added=0,
        lines_deleted=0,
        human_review_outcome=None,
        review=None,
        input_tokens=None,
        output_tokens=None,
        cached_input_tokens=None,
        reasoning_output_tokens=None,
    ):
        if human_review_outcome is None and review is not None:
            review_payload = dict(review)
            review_payload.setdefault("note", "Test review.")
            review_payload.setdefault("evidence", [])
            review_payload.setdefault("secondary_labels", [])
            review_payload.setdefault("trial_validity", "valid")
            human_review_outcome = human_review_outcome_from_mapping(review_payload)

        return normalize_outcome_evidence(
            {
                "eval_suite": "starter",
                "eval_type": "capability",
                "task_id": task_id,
                "agent_name": agent_name,
                "model_name": model_name,
                "agent_harness_config": {"reasoning_effort": reasoning_effort},
                "success": success,
                "duration_ms": duration_ms,
                "files_changed": files_changed or [],
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_input_tokens": cached_input_tokens,
                "reasoning_output_tokens": reasoning_output_tokens,
            },
            human_review_outcome=human_review_outcome,
        )


if __name__ == "__main__":
    unittest.main()
