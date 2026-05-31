from pathlib import Path
import unittest

from agentlab.evidence import render_capability_evidence_digest
from agentlab.human_review import create_human_review_outcome
from agentlab.outcome_evidence import normalize_outcome_evidence


class CapabilityEvidenceDigestTest(unittest.TestCase):
    def test_renders_aggregate_and_trial_evidence(self):
        digest = render_capability_evidence_digest(
            [
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-pass",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "regression",
                        "agent_name": "codex",
                        "model_name": "model-a",
                        "agent_harness_config": {"reasoning_effort": "xhigh"},
                        "status": "passed",
                        "success": True,
                        "duration_ms": 100,
                        "files_changed": ["app.py"],
                        "lines_added": 5,
                        "lines_deleted": 1,
                        "input_tokens": 10,
                        "cached_input_tokens": 4,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 2,
                        "cost_usd": None,
                        "report_path": "runs/trial-pass/report.md",
                        "transcript_path": "runs/trial-pass/transcript.md",
                        "diff_path": "runs/trial-pass/diff.patch",
                        "run_dir": "runs/trial-pass",
                    },
                    human_review_outcome=create_human_review_outcome(
                        primary_label="success_clean",
                        note="Focused patch with passing checks.",
                        secondary_labels=["resource_inefficient"],
                    ),
                ),
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-excluded",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "regression",
                        "agent_name": "codex",
                        "model_name": "model-a",
                        "agent_harness_config": {"reasoning_effort": "xhigh"},
                        "status": "failed",
                        "success": False,
                        "duration_ms": 999,
                        "files_changed": ["app.py", "env.py"],
                        "lines_added": 500,
                        "lines_deleted": 200,
                        "report_path": "runs/trial-excluded/report.md",
                        "run_dir": "runs/trial-excluded",
                    },
                    human_review_outcome=create_human_review_outcome(
                        primary_label="dependency_issue",
                        note="Task setup failed before the Trial was fair.",
                        trial_validity="excluded",
                        exclusion_reason="setup_error",
                    ),
                ),
            ]
        )

        self.assertIn("# Capability Evidence Digest", digest)
        self.assertIn("Primary Review Labels", digest)
        self.assertIn("Secondary Review Labels", digest)
        self.assertIn("IO Tok / Verified", digest)
        self.assertIn("IO Tok / Accepted", digest)
        self.assertIn("Cached Tokens", digest)
        self.assertIn("Cached Input Tokens", digest)
        self.assertIn("Reason Tokens", digest)
        self.assertIn("### Outcome Summary", digest)
        self.assertIn("### Token Summary", digest)
        self.assertIn("### Review and Patch Summary", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | xhigh | 2 | 1 | 1 | 1 | 1 | 1.00 | 1.00 | 1.00 |", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | xhigh | 15 | 4 | 2 | 15 | 15 | 4 | 2 |", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | xhigh | 100 | 1 | 5 | 1 | success_clean:1 | resource_inefficient:1 | setup_error:1 |", digest)
        self.assertIn("| trial-pass | task-a | codex | model-a | xhigh | passed | valid | success_clean | resource_inefficient |", digest)
        self.assertIn("| 1 | 5 | 1 | 10 | 4 | 5 | 2 | unknown | 100 |", digest)
        self.assertIn("| trial-excluded | task-a | codex | model-a | xhigh | failed | excluded | dependency_issue |  | setup_error |", digest)
        self.assertIn("[report](runs/trial-pass/report.md)", digest)
        self.assertIn("[transcript](runs/trial-pass/transcript.md)", digest)
        self.assertIn("[diff](runs/trial-pass/diff.patch)", digest)
        self.assertIn("[result](runs/trial-pass/result.json)", digest)

    def test_renders_token_totals_when_no_verified_results(self):
        digest = render_capability_evidence_digest(
            [
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-fail",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "regression",
                        "agent_name": "codex",
                        "model_name": "model-a",
                        "agent_harness_config": {"reasoning_effort": "xhigh"},
                        "status": "failed",
                        "success": False,
                        "duration_ms": 100,
                        "files_changed": [],
                        "lines_added": 0,
                        "lines_deleted": 0,
                        "input_tokens": 10,
                        "cached_input_tokens": 4,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 2,
                        "run_dir": "runs/trial-fail",
                    },
                    human_review_outcome=create_human_review_outcome(
                        primary_label="bad_local_fix",
                        note="Graders failed after an attempted patch.",
                    ),
                ),
            ]
        )

        self.assertIn("Cached Tokens", digest)
        self.assertIn("Reason Tokens", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | xhigh | 1 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 |", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | xhigh | 15 | 4 | 2 | unknown | unknown | unknown | unknown |", digest)
        self.assertIn("| starter | regression | task-a | codex | model-a | xhigh | 100 | 0 | 0 | 0 | bad_local_fix:1 |  |  |", digest)

    def test_renders_missing_model_identity_as_unknown(self):
        digest = render_capability_evidence_digest(
            [
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-unknown-model",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "regression",
                        "agent_name": "codex",
                        "model_name": None,
                        "status": "passed",
                        "success": True,
                        "duration_ms": 100,
                        "files_changed": [],
                        "lines_added": 0,
                        "lines_deleted": 0,
                        "run_dir": "runs/trial-unknown-model",
                    }
                )
            ]
        )

        self.assertIn(
            "| starter | regression | task-a | codex | unknown | unknown | 1 |",
            digest,
        )
        self.assertIn(
            "| trial-unknown-model | task-a | codex | unknown | unknown | passed |",
            digest,
        )

    def test_historical_digest_snapshots_disclose_missing_cached_trial_values(self):
        note = "Historical snapshot note: cached-token aggregate totals are available"
        repo_root = Path(__file__).resolve().parents[1]
        digest_paths = [
            "reports/codex-starter-suite-12-task-baseline-2026-05-11/digest.md",
            "reports/codex-starter-suite-deep-baseline-2026-05-09/digest.md",
            (
                "reports/claude-code-starter-suite-baseline-2026-05-14/"
                "capability-evidence-digest.md"
            ),
        ]

        for rel_path in digest_paths:
            digest = (repo_root / rel_path).read_text(encoding="utf-8")
            if not self._has_cached_aggregate_with_only_unknown_trial_values(digest):
                continue

            with self.subTest(path=rel_path):
                self.assertIn(note, digest)

    def _has_cached_aggregate_with_only_unknown_trial_values(self, digest: str) -> bool:
        token_section = digest.split("### Token Summary", 1)[1].split(
            "### Review and Patch Summary",
            1,
        )[0]
        token_lines = [
            line for line in token_section.splitlines() if line.startswith("| ")
        ]
        token_header = self._markdown_cells(token_lines[0])
        cached_total_index = token_header.index("Cached Tokens")
        token_rows = [self._markdown_cells(line) for line in token_lines[2:]]
        has_cached_total = any(
            row[cached_total_index] not in {"", "0", "unknown"}
            for row in token_rows
        )
        if not has_cached_total:
            return False

        trial_section = digest.split("## Trial Evidence", 1)[1]
        trial_lines = [
            line for line in trial_section.splitlines() if line.startswith("| ")
        ]
        trial_header = self._markdown_cells(trial_lines[0])
        cached_trial_index = trial_header.index("Cached Input Tokens")
        cached_trial_values = [
            self._markdown_cells(line)[cached_trial_index] for line in trial_lines[2:]
        ]
        return bool(cached_trial_values) and all(
            value == "unknown" for value in cached_trial_values
        )

    def _markdown_cells(self, row: str) -> list[str]:
        return [cell.strip() for cell in row.strip().strip("|").split("|")]


if __name__ == "__main__":
    unittest.main()
