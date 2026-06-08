import json
import tempfile
import unittest
from pathlib import Path

from agentlab.evidence.human_review import create_human_review_outcome
from agentlab.evidence.outcome import normalize_outcome_evidence
from agentlab.evidence.snapshots import (
    load_evidence_snapshot,
    write_evidence_snapshot,
)
from agentlab.reports.capability_digest import render_capability_evidence_digest
from agentlab.reports.operability_evidence import (
    render_agent_harness_operability_table,
)


class EvidenceSnapshotTest(unittest.TestCase):
    def test_snapshot_round_trips_outcome_evidence_without_local_artifact_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "worktree" / "runs" / "trial-pass"
            result = normalize_outcome_evidence(
                {
                    "trial_id": "trial-pass",
                    "task_id": "task-a",
                    "eval_suite": "starter",
                    "eval_type": "capability",
                    "agent_name": "codex",
                    "model_name": "model-a",
                    "agent_harness_config": {"reasoning_effort": "low"},
                    "run_surface": {"sandbox_mode": "workspace-write"},
                    "status": "passed",
                    "success": True,
                    "duration_ms": 100,
                    "files_changed": ["app.py"],
                    "lines_added": 5,
                    "lines_deleted": 1,
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "report_path": str(run_dir / "report.md"),
                    "result_path": str(run_dir / "result.json"),
                    "transcript_path": str(run_dir / "transcript.md"),
                    "diff_path": str(run_dir / "diff.patch"),
                    "run_dir": str(run_dir),
                },
                human_review_outcome=create_human_review_outcome(
                    primary_label="success_clean",
                    note="Reviewed and accepted.",
                    secondary_labels=["resource_inefficient"],
                ),
            )
            snapshot_path = root / "evidence.json"

            write_evidence_snapshot(snapshot_path, [result])
            snapshot_text = snapshot_path.read_text(encoding="utf-8")
            loaded = load_evidence_snapshot(snapshot_path)
            digest = render_capability_evidence_digest(loaded)

        self.assertNotIn(str(root), snapshot_text)
        self.assertEqual(len(loaded), 1)
        loaded_result = loaded[0]
        self.assertEqual(loaded_result.trial_id, "trial-pass")
        self.assertEqual(loaded_result.primary_review_label, "success_clean")
        self.assertEqual(loaded_result.secondary_review_labels, ["resource_inefficient"])
        self.assertEqual(loaded_result.report_path, None)
        self.assertTrue(loaded_result.report_artifact.was_present)
        self.assertIsNone(loaded_result.report_artifact.path)
        self.assertTrue(loaded_result.transcript_artifact.was_present)
        self.assertIsNone(loaded_result.transcript_artifact.path)
        self.assertTrue(loaded_result.diff_artifact.was_present)
        self.assertIsNone(loaded_result.diff_artifact.path)
        self.assertTrue(loaded_result.result_artifact.was_present)
        self.assertIsNone(loaded_result.result_artifact.path)
        self.assertTrue(loaded_result.run_artifact.was_present)
        self.assertIsNone(loaded_result.run_artifact.path)
        self.assertEqual(loaded_result.run_dir, "")
        self.assertIn("| task-a | capability | trial-pass | passed | valid |", digest)
        operability = "\n".join(render_agent_harness_operability_table(loaded))
        self.assertIn("report_md: `1/1`", operability)
        self.assertIn("transcript: `1/1`", operability)
        self.assertIn("diff_patch: `1/1`", operability)

    def test_snapshot_preserves_scope_oracle_metadata(self):
        result = normalize_outcome_evidence(
            {
                "trial_id": "trial-scope-oracle",
                "task_id": "task-a",
                "eval_suite": "starter",
                "eval_type": "capability",
                "agent_name": "codex",
                "status": "passed",
                "success": True,
                "scope_oracle": {
                    "consent_style": "explicit_allow",
                    "allowed_paths": ["src/"],
                    "forbidden_paths": ["src/private/"],
                },
            }
        )

        with tempfile.TemporaryDirectory() as temp:
            snapshot_path = Path(temp) / "evidence.json"
            write_evidence_snapshot(snapshot_path, [result])
            loaded = load_evidence_snapshot(snapshot_path)

        self.assertEqual(
            loaded[0].scope_oracle,
            {
                "consent_style": "explicit_allow",
                "allowed_paths": ["src/"],
                "forbidden_paths": ["src/private/"],
            },
        )
        self.assertEqual(
            loaded[0].to_result_dict()["scope_oracle"],
            {
                "consent_style": "explicit_allow",
                "allowed_paths": ["src/"],
                "forbidden_paths": ["src/private/"],
            },
        )

    def test_snapshot_scrubs_local_paths_from_nested_result_strings(self):
        result = normalize_outcome_evidence(
            {
                "trial_id": "trial-pass",
                "task_id": "task-a",
                "eval_suite": "starter",
                "eval_type": "capability",
                "agent_name": "claude",
                "model_name": "claude-opus-4-8",
                "agent_harness_config": {
                    "command_identity": "/Users/example/.local/bin/claude",
                },
                "status": "passed",
                "success": True,
                "checks": [
                    {
                        "command": "python -m pip install -e .",
                        "passed": True,
                        "returncode": 0,
                        "stdout": (
                            "Obtaining file:///Users/example/.codex/worktrees/"
                            "abc/project/runs/trial/workspace\n"
                            "Stored in directory: /private/tmp/pip-cache\n"
                        ),
                        "stderr": "",
                    }
                ],
            }
        )

        with tempfile.TemporaryDirectory() as temp:
            snapshot_path = Path(temp) / "evidence.json"
            write_evidence_snapshot(snapshot_path, [result])
            snapshot_text = snapshot_path.read_text(encoding="utf-8")

        self.assertNotIn("/Users/", snapshot_text)
        self.assertNotIn("/private/", snapshot_text)
        self.assertNotIn(".codex/worktrees", snapshot_text)
        self.assertIn('"command_identity": null', snapshot_text)
        self.assertIn("<local-path>", snapshot_text)

    def test_rejects_unknown_snapshot_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            snapshot_path = Path(temp) / "evidence.json"
            snapshot_path.write_text(
                json.dumps({"schema": "unknown", "records": []}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_evidence_snapshot(snapshot_path)


if __name__ == "__main__":
    unittest.main()
