import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from agentlab.agents.manual import _print_manual_instructions
from agentlab.agents.prompts import build_agent_prompt
from agentlab.tasks import EvalTask, HiddenVerifier, SuccessCriteria


class AgentPromptTest(unittest.TestCase):
    def test_target_graders_are_not_injected(self):
        task = EvalTask(
            id="grader-task",
            title="Grader task",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix the behavior.",
            test=["pytest tests/hidden_behavior.py"],
        )

        prompt = build_agent_prompt(task)

        self.assertIn("Fix the behavior.", prompt)
        self.assertNotIn("Validation commands that will be run", prompt)
        self.assertNotIn("pytest tests/hidden_behavior.py", prompt)

    def test_visible_validation_is_injected(self):
        task = EvalTask(
            id="visible-validation-task",
            title="Visible validation task",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix the behavior.",
            visible_validation=["pytest tests/focused_check.py"],
            test=["pytest tests/hidden_behavior.py"],
        )

        prompt = build_agent_prompt(task)

        self.assertIn("Suggested validation commands:", prompt)
        self.assertIn("pytest tests/focused_check.py", prompt)
        self.assertNotIn("pytest tests/hidden_behavior.py", prompt)

    def test_manual_instructions_hide_target_graders(self):
        task = EvalTask(
            id="manual-task",
            title="Manual task",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix the behavior.",
            visible_validation=["pytest tests/focused_check.py"],
            test=["pytest tests/hidden_behavior.py"],
        )
        output = StringIO()

        with redirect_stdout(output):
            _print_manual_instructions(task, Path("/tmp/workspace"))

        printed = output.getvalue()
        self.assertIn("Suggested validation commands:", printed)
        self.assertIn("pytest tests/focused_check.py", printed)
        self.assertNotIn("pytest tests/hidden_behavior.py", printed)

    def test_scope_oracle_metadata_is_not_injected(self):
        task = EvalTask(
            id="scope-task",
            title="Scope task",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix the failing behavior.",
            consent_style="explicit_allow",
            success=SuccessCriteria(
                allowed_paths=["src/"],
                forbidden_paths=["src/private/"],
            ),
        )

        prompt = build_agent_prompt(task)

        self.assertIn("Fix the failing behavior.", prompt)
        self.assertNotIn("explicit_allow", prompt)
        self.assertNotIn("src/", prompt)
        self.assertNotIn("forbidden_paths", prompt)
        self.assertNotIn("allowed_paths", prompt)

    def test_hidden_verifier_is_not_injected(self):
        task = EvalTask(
            id="hidden-task",
            title="Hidden task",
            repo="https://github.com/example/repo",
            commit="abc123",
            language="python",
            prompt="Fix the behavior.",
            visible_validation=["pytest tests/focused_check.py"],
            hidden_verifier=HiddenVerifier(
                patch="verifier.patch",
                commands=["pytest tests/hidden_behavior.py"],
            ),
        )

        prompt = build_agent_prompt(task)
        output = StringIO()
        with redirect_stdout(output):
            _print_manual_instructions(task, Path("/tmp/workspace"))
        printed = output.getvalue()

        self.assertIn("pytest tests/focused_check.py", prompt)
        self.assertNotIn("verifier.patch", prompt)
        self.assertNotIn("pytest tests/hidden_behavior.py", prompt)
        self.assertIn("pytest tests/focused_check.py", printed)
        self.assertNotIn("verifier.patch", printed)
        self.assertNotIn("pytest tests/hidden_behavior.py", printed)


if __name__ == "__main__":
    unittest.main()
