import unittest

from agentlab.human_review import (
    create_human_review_outcome,
    human_review_outcome_from_mapping,
    human_review_outcome_to_mapping,
)


class HumanReviewOutcomeTest(unittest.TestCase):
    def test_creates_valid_review_outcome(self):
        outcome = create_human_review_outcome(
            primary_label="success_clean",
            note="Focused patch with passing checks.",
            secondary_labels=["resource_inefficient"],
            evidence=["diff.patch"],
        )

        self.assertTrue(outcome.is_valid_trial)
        self.assertEqual(outcome.primary_label_display, "success_clean")
        self.assertEqual(outcome.secondary_labels, ("resource_inefficient",))
        self.assertEqual(outcome.evidence, ("diff.patch",))
        self.assertIsNone(outcome.exclusion_reason)

    def test_excluded_review_defaults_matching_exclusion_reason(self):
        outcome = create_human_review_outcome(
            primary_label="dependency_issue",
            note="The task environment failed before the agent acted.",
            trial_validity="excluded",
        )

        self.assertFalse(outcome.is_valid_trial)
        self.assertEqual(outcome.exclusion_reason, "dependency_issue")

    def test_rejects_valid_review_with_exclusion_reason(self):
        with self.assertRaises(ValueError):
            create_human_review_outcome(
                primary_label="success_clean",
                note="Valid trial.",
                exclusion_reason="setup_error",
            )

    def test_round_trips_mapping_shape(self):
        outcome = human_review_outcome_from_mapping(
            {
                "primary_label": "dependency_issue",
                "secondary_labels": [],
                "note": "Setup failed.",
                "evidence": ["report.md"],
                "trial_validity": "excluded",
                "exclusion_reason": "harness_error",
            }
        )

        self.assertEqual(outcome.exclusion_reason, "eval_harness_error")
        self.assertEqual(
            human_review_outcome_to_mapping(outcome),
            {
                "primary_label": "dependency_issue",
                "secondary_labels": [],
                "note": "Setup failed.",
                "evidence": ["report.md"],
                "trial_validity": "excluded",
                "exclusion_reason": "eval_harness_error",
            },
        )

    def test_canonical_collections_are_immutable(self):
        outcome = create_human_review_outcome(
            primary_label="success_clean",
            note="Focused patch.",
            secondary_labels=["resource_inefficient"],
            evidence=["diff.patch"],
        )

        with self.assertRaises(AttributeError):
            outcome.secondary_labels.append("not_a_label")
        with self.assertRaises(AttributeError):
            outcome.evidence.append("mutated")

    def test_mapping_requires_explicit_trial_validity(self):
        with self.assertRaisesRegex(ValueError, "requires trial_validity"):
            human_review_outcome_from_mapping(
                {
                    "primary_label": "success_clean",
                    "secondary_labels": [],
                    "note": "Missing persisted validity.",
                    "evidence": [],
                    "exclusion_reason": None,
                }
            )

        with self.assertRaisesRegex(ValueError, "requires trial_validity"):
            human_review_outcome_from_mapping(
                {
                    "primary_label": "success_clean",
                    "secondary_labels": [],
                    "note": "Null persisted validity.",
                    "evidence": [],
                    "trial_validity": None,
                    "exclusion_reason": None,
                }
            )

    def test_mapping_requires_explicit_exclusion_reason_for_excluded_trial(self):
        with self.assertRaisesRegex(ValueError, "requires exclusion_reason"):
            human_review_outcome_from_mapping(
                {
                    "primary_label": "dependency_issue",
                    "secondary_labels": [],
                    "note": "Missing persisted exclusion reason.",
                    "evidence": [],
                    "trial_validity": "excluded",
                }
            )

        with self.assertRaisesRegex(ValueError, "requires exclusion_reason"):
            human_review_outcome_from_mapping(
                {
                    "primary_label": "dependency_issue",
                    "secondary_labels": [],
                    "note": "Null persisted exclusion reason.",
                    "evidence": [],
                    "trial_validity": "excluded",
                    "exclusion_reason": None,
                }
            )


if __name__ == "__main__":
    unittest.main()
