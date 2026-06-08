import unittest

from agentlab.agents.prompts import build_agent_prompt
from agentlab.tasks import EvalTask, SuccessCriteria


class AgentPromptTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
