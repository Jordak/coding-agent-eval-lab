import unittest

from agentlab.summary import summarize_trials


class SummaryTest(unittest.TestCase):
    def test_summarizes_pass_at_k_and_pass_caret_k(self):
        results = [
            self._result(success=False, duration_ms=100, files_changed=[]),
            self._result(success=True, duration_ms=300, files_changed=["a.py", "b.py"]),
            self._result(success=True, duration_ms=200, files_changed=["a.py"]),
        ]

        summary = summarize_trials(results)[0]

        self.assertEqual(summary.trials, 3)
        self.assertEqual(summary.passes, 2)
        self.assertAlmostEqual(summary.pass_rate, 2 / 3)
        self.assertEqual(summary.pass_at_k, 1.0)
        self.assertEqual(summary.pass_caret_k, 0.0)
        self.assertEqual(summary.median_duration_ms, 200)
        self.assertEqual(summary.median_files_changed, 1)

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

    def _result(
        self,
        success=True,
        duration_ms=0,
        files_changed=None,
        task_id="task-a",
        agent_name="codex",
        model_name="m1",
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
        }


if __name__ == "__main__":
    unittest.main()
