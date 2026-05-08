import unittest

from agentlab.summary import summarize_trials


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

    def test_pass_caret_k_requires_all_trials_to_pass(self):
        results = [
            self._result(success=True, duration_ms=100, files_changed=[]),
            self._result(success=True, duration_ms=200, files_changed=[]),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.pass_at_k, 1.0)
        self.assertEqual(summary.pass_caret_k, 1.0)

    def test_groups_by_task_agent_and_model(self):
        results = [
            self._result(task_id="task-a", agent_name="codex", model_name="m1"),
            self._result(task_id="task-a", agent_name="codex", model_name="m2"),
            self._result(task_id="task-b", agent_name="codex", model_name="m1"),
        ]

        summaries = summarize_trials(results)

        self.assertEqual(len(summaries), 3)

    def test_excludes_invalid_trials_from_pass_metrics(self):
        results = [
            self._result(success=True, duration_ms=100, files_changed=["a.py"]),
            self._result(
                success=False,
                duration_ms=999,
                files_changed=["a.py", "b.py", "c.py"],
                lines_added=999,
                lines_deleted=999,
                review={
                    "primary_label": "dependency_issue",
                    "trial_validity": "excluded",
                    "exclusion_reason": "setup_error",
                },
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
        self.assertEqual(summary.exclusion_reasons, {"setup_error": 1})

    def _result(
        self,
        success=True,
        duration_ms=0,
        files_changed=None,
        task_id="task-a",
        agent_name="codex",
        model_name="m1",
        lines_added=0,
        lines_deleted=0,
        review=None,
    ):
        return {
            "eval_suite": "starter",
            "eval_type": "capability",
            "task_id": task_id,
            "agent_name": agent_name,
            "model_name": model_name,
            "success": success,
            "duration_ms": duration_ms,
            "files_changed": files_changed or [],
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "review": review,
        }


if __name__ == "__main__":
    unittest.main()
