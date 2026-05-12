import unittest
from pathlib import Path

from agentlab.model_identity import model_identity_from_events


FIXTURES = Path(__file__).parent / "fixtures" / "model_identity"


class ModelIdentityTest(unittest.TestCase):
    def test_captured_event_stream_fixtures_parse_model_identity(self):
        cases = [
            {
                "name": "claude_code_system_init_assistant_message_and_result_usage",
                "fixture": (
                    FIXTURES / "claude" / "system-init-assistant-result.jsonl"
                ),
                "requested_model_name": "requested-sonnet",
                "expected_model_name": "claude-sonnet-4-6",
                "expected_model_source": "events",
                "expected_requested_model_name": "requested-sonnet",
            },
            {
                "name": "codex_thread_turn_completed_usage_without_runtime_model",
                "fixture": FIXTURES / "codex" / "thread-turn-usage-only.jsonl",
                "requested_model_name": "gpt-requested",
                "expected_model_name": "gpt-requested",
                "expected_model_source": "explicit",
                "expected_requested_model_name": "gpt-requested",
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                events = case["fixture"].read_text(encoding="utf-8")
                identity = model_identity_from_events(
                    events,
                    requested_model_name=case["requested_model_name"],
                )

                self.assertEqual(identity.model_name, case["expected_model_name"])
                self.assertEqual(identity.model_source, case["expected_model_source"])
                self.assertEqual(
                    identity.requested_model_name,
                    case["expected_requested_model_name"],
                )

    def test_prefers_direct_event_model_over_requested_model(self):
        identity = model_identity_from_events(
            '{"type":"turn.completed","model":"actual-model"}\n',
            requested_model_name="requested-model",
        )

        self.assertEqual(identity.model_name, "actual-model")
        self.assertEqual(identity.model_source, "events")
        self.assertEqual(identity.requested_model_name, "requested-model")

    def test_reads_claude_message_model_before_model_usage_helpers(self):
        identity = model_identity_from_events(
            '{"type":"result","modelUsage":{"helper-model":{"costUSD":0.1}}}\n'
            '{"type":"assistant","message":{"model":"main-model"}}\n',
            requested_model_name=None,
        )

        self.assertEqual(identity.model_name, "main-model")
        self.assertEqual(identity.model_source, "events")

    def test_uses_single_model_usage_entry_as_last_resort(self):
        identity = model_identity_from_events(
            '{"type":"result","modelUsage":{"only-model":{"costUSD":0.1}}}\n',
            requested_model_name=None,
        )

        self.assertEqual(identity.model_name, "only-model")
        self.assertEqual(identity.model_source, "events")

    def test_ambiguous_multimodel_usage_without_primary_model_is_unknown(self):
        events = (
            FIXTURES / "claude" / "result-multimodel-usage-only.jsonl"
        ).read_text(encoding="utf-8")

        identity = model_identity_from_events(events, requested_model_name=None)

        self.assertIsNone(identity.model_name)
        self.assertEqual(identity.model_source, "unknown")
        self.assertIsNone(identity.requested_model_name)

    def test_ambiguous_multimodel_usage_falls_back_to_requested_model(self):
        events = (
            FIXTURES / "claude" / "result-multimodel-usage-only.jsonl"
        ).read_text(encoding="utf-8")

        identity = model_identity_from_events(
            events,
            requested_model_name="requested-sonnet",
        )

        self.assertEqual(identity.model_name, "requested-sonnet")
        self.assertEqual(identity.model_source, "explicit")
        self.assertEqual(identity.requested_model_name, "requested-sonnet")

    def test_malformed_and_irrelevant_lines_are_ignored_safely(self):
        identity = model_identity_from_events(
            "not json\n"
            "[]\n"
            '{"type":"turn.completed","usage":{"input_tokens":1}}\n'
            '{"type":"turn.completed","model":"actual-model"}\n',
            requested_model_name="requested-model",
        )

        self.assertEqual(identity.model_name, "actual-model")
        self.assertEqual(identity.model_source, "events")
        self.assertEqual(identity.requested_model_name, "requested-model")

    def test_falls_back_to_requested_model_when_events_do_not_identify_model(self):
        identity = model_identity_from_events(
            '{"type":"turn.completed","usage":{"input_tokens":1}}\n',
            requested_model_name="requested-model",
        )

        self.assertEqual(identity.model_name, "requested-model")
        self.assertEqual(identity.model_source, "explicit")
        self.assertEqual(identity.requested_model_name, "requested-model")


if __name__ == "__main__":
    unittest.main()
