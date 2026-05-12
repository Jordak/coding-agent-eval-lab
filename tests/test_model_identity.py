import unittest

from agentlab.model_identity import model_identity_from_events


class ModelIdentityTest(unittest.TestCase):
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
