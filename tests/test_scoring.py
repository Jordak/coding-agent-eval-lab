import unittest

from agentlab.execution.scoring import CheckResult, calculate_grader_outcome
from agentlab.tasks import EvalTask, SuccessCriteria


class GraderOutcomeTest(unittest.TestCase):
    def test_passing_checks_pass(self):
        outcome = calculate_grader_outcome(
            self._task(),
            [CheckResult(command="python -m unittest", returncode=0)],
            files_changed=["app.py"],
        )

        self.assertTrue(outcome.tests_passed)
        self.assertEqual(outcome.notes, [])
        self.assertEqual(len(outcome.checks), 1)

    def test_failing_check_fails_when_tests_must_pass(self):
        outcome = calculate_grader_outcome(
            self._task(),
            [CheckResult(command="python -m unittest", returncode=1)],
            files_changed=[],
        )

        self.assertFalse(outcome.tests_passed)

    def test_tests_must_pass_false_preserves_checks_without_failing_outcome(self):
        outcome = calculate_grader_outcome(
            self._task(success=SuccessCriteria(tests_must_pass=False)),
            [CheckResult(command="python -m unittest", returncode=1)],
            files_changed=[],
        )

        self.assertTrue(outcome.tests_passed)
        self.assertFalse(outcome.checks[0].passed)

    def test_agent_adapter_error_fails_outcome(self):
        outcome = calculate_grader_outcome(
            self._task(),
            [CheckResult(command="python -m unittest", returncode=0)],
            files_changed=[],
            agent_error="agent executable not found",
        )

        self.assertFalse(outcome.tests_passed)
        self.assertEqual(outcome.notes, [])

    def test_max_files_changed_note_fails_outcome(self):
        outcome = calculate_grader_outcome(
            self._task(success=SuccessCriteria(max_files_changed=1)),
            [CheckResult(command="python -m unittest", returncode=0)],
            files_changed=["app.py", "tests/test_app.py"],
        )

        self.assertFalse(outcome.tests_passed)
        self.assertEqual(
            outcome.notes,
            ["changed 2 files; limit is 1"],
        )

    def _task(self, success=None):
        return EvalTask(
            id="fixture-task",
            title="Fixture task",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix it.",
            success=success or SuccessCriteria(),
        )


if __name__ == "__main__":
    unittest.main()
