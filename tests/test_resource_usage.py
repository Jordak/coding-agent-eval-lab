import unittest

from agentlab.runtime.resource_usage import parse_resource_usage_events


class ResourceUsageTest(unittest.TestCase):
    def test_parses_codex_usage_events(self):
        usage = parse_resource_usage_events(
            '{"type":"turn.completed","usage":{"input_tokens":10,'
            '"cached_input_tokens":4,"output_tokens":5,'
            '"reasoning_output_tokens":2}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":3,'
            '"output_tokens":7,"estimated_cost_usd":0.25}}\n'
        )

        self.assertEqual(usage.input_tokens, 13)
        self.assertEqual(usage.cached_input_tokens, 4)
        self.assertEqual(usage.output_tokens, 12)
        self.assertEqual(usage.reasoning_output_tokens, 2)
        self.assertEqual(usage.total_tokens, 25)
        self.assertEqual(usage.cost_usd, 0.25)


if __name__ == "__main__":
    unittest.main()
