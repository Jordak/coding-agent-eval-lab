import json
import tempfile
import unittest
from pathlib import Path

from agentlab.reports.capability_digest import render_capability_evidence_digest
from agentlab.evidence.sets import EvidenceSet, load_evidence_set
from agentlab.evidence.outcome import load_outcome_evidences
from agentlab.evidence.review_artifacts import write_review
from agentlab.evidence.snapshots import write_evidence_snapshot


class EvidenceSetTest(unittest.TestCase):
    def test_manifest_selects_digest_trials_and_excludes_unselected_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs_dir = root / "runs"
            passing = runs_dir / "trial-pass"
            excluded = runs_dir / "trial-excluded"
            manual = runs_dir / "trial-manual"
            for run_dir in [passing, excluded, manual]:
                run_dir.mkdir(parents=True)

            _write_result(passing, "trial-pass", success=True, agent_name="codex")
            _write_result(excluded, "trial-excluded", success=False, agent_name="codex")
            _write_result(manual, "trial-manual", success=False, agent_name="manual")
            write_review(
                excluded,
                primary_label="dependency_issue",
                note="Task setup failed before measuring the agent harness.",
                trial_validity="excluded",
                exclusion_reason="setup_error",
            )
            manifest = root / "codex-evidence.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "codex selected evidence",
                        "description": "Only the Codex trials selected for report prep.",
                        "trials": [
                            "trial-pass",
                            "trial-excluded/result.json",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            evidence_set = load_evidence_set(manifest, runs_dir)
            results = load_outcome_evidences(evidence_set.result_files)
            digest = render_capability_evidence_digest(
                results,
                evidence_set.digest_context(),
            )

        self.assertEqual(
            [path.parent.name for path in evidence_set.result_files],
            ["trial-pass", "trial-excluded"],
        )
        self.assertEqual(
            [result.trial_id for result in results],
            ["trial-pass", "trial-excluded"],
        )
        self.assertIn("- Evidence set: `codex selected evidence`", digest)
        self.assertIn("- Selected entries: `2`", digest)
        self.assertIn("- Selected result files: `2`", digest)
        self.assertIn("setup_error:1", digest)
        self.assertIn("trial-pass", digest)
        self.assertIn("trial-excluded", digest)
        self.assertNotIn("trial-manual", digest)

    def test_manifest_requires_non_empty_trial_list(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "empty.json"
            manifest.write_text(json.dumps({"trials": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_evidence_set(manifest, Path(temp) / "runs")

    def test_digest_context_uses_repo_relative_source_path_when_possible(self):
        context = EvidenceSet(
            name="selected",
            description="",
            source_path=Path.cwd() / "evidence-sets" / "selected.json",
            trial_entries=["trial-a"],
            result_files=[],
        ).digest_context()

        self.assertEqual(context["source_path"], "evidence-sets/selected.json")

    def test_manifest_snapshot_keeps_evidence_resolvable_without_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs_dir = root / "runs"
            run_dir = runs_dir / "trial-pass"
            run_dir.mkdir(parents=True)
            _write_result(run_dir, "trial-pass", success=True, agent_name="codex")

            results = load_outcome_evidences([run_dir / "result.json"])
            snapshot = root / "selected.outcome-evidence.json"
            write_evidence_snapshot(snapshot, results)
            manifest = root / "selected.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "selected",
                        "trials": ["trial-pass"],
                        "outcome_evidence_snapshot": snapshot.name,
                    }
                ),
                encoding="utf-8",
            )

            evidence_set = load_evidence_set(manifest, root / "missing-runs")
            digest = render_capability_evidence_digest(
                evidence_set.snapshot_results or [],
                evidence_set.digest_context(),
            )

        self.assertEqual(evidence_set.result_files, [])
        self.assertEqual(len(evidence_set.snapshot_results or []), 1)
        self.assertIn("- Outcome evidence snapshot: `", digest)
        self.assertIn("- Selected snapshot records: `1`", digest)
        self.assertIn("| task-a | capability | trial-pass | passed | valid |", digest)


def _write_result(
    run_dir: Path,
    trial_id: str,
    *,
    success: bool,
    agent_name: str,
) -> None:
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "trial_kind": "agent_trial",
                "trial_id": trial_id,
                "run_id": trial_id,
                "task_id": "task-a",
                "eval_suite": "starter",
                "eval_type": "capability",
                "agent_name": agent_name,
                "model_name": "",
                "status": "passed" if success else "failed",
                "success": success,
                "duration_ms": 100,
                "files_changed": ["app.py"],
                "lines_added": 5,
                "lines_deleted": 1,
                "run_dir": str(run_dir),
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
