from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentlab.evidence.results import discover_result_files
from agentlab.evidence.review_artifacts import write_review
from agentlab.evidence.archive import archive_excluded_trials, plan_excluded_trial_archive


class TrialArchiveTest(unittest.TestCase):
    def test_dry_run_plans_only_reviewed_excluded_trials_for_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp) / "runs"
            reviewed_excluded = runs_dir / "trial-excluded"
            reviewed_valid = runs_dir / "trial-valid"
            unreviewed_excluded = runs_dir / "trial-unreviewed"
            for run_dir in [reviewed_excluded, reviewed_valid, unreviewed_excluded]:
                run_dir.mkdir(parents=True)

            _write_result(reviewed_excluded, "trial-excluded", success=False)
            _write_result(reviewed_valid, "trial-valid", success=True)
            _write_result(
                unreviewed_excluded,
                "trial-unreviewed",
                success=False,
                trial_validity="excluded",
                exclusion_reason="setup_error",
            )
            write_review(
                reviewed_excluded,
                primary_label="dependency_issue",
                note="Setup failed before the agent harness acted.",
                trial_validity="excluded",
                exclusion_reason="setup_error",
            )
            write_review(
                reviewed_valid,
                primary_label="success_clean",
                note="Focused passing patch.",
            )

            candidates = plan_excluded_trial_archive(
                runs_dir,
                exclusion_reasons=["setup_error"],
            )
            archive_result = archive_excluded_trials(
                runs_dir,
                exclusion_reasons=["setup_error"],
            )

            self.assertEqual(
                [candidate.trial_id for candidate in candidates],
                ["trial-excluded"],
            )
            self.assertTrue(archive_result.dry_run)
            self.assertEqual(
                [candidate.trial_id for candidate in archive_result.candidates],
                ["trial-excluded"],
            )
            self.assertTrue(reviewed_excluded.exists())
            self.assertTrue(reviewed_valid.exists())
            self.assertTrue(unreviewed_excluded.exists())

    def test_apply_moves_artifacts_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp) / "runs"
            run_dir = runs_dir / "trial-excluded"
            run_dir.mkdir(parents=True)
            _write_result(run_dir, "trial-excluded", success=False)
            write_review(
                run_dir,
                primary_label="dependency_issue",
                note="Setup failed before the agent harness acted.",
                trial_validity="excluded",
                exclusion_reason="setup_error",
            )

            archive_result = archive_excluded_trials(
                runs_dir,
                exclusion_reasons=["setup_error"],
                apply=True,
            )

            archived_run = (
                runs_dir
                / "_archive"
                / "excluded"
                / "setup_error"
                / "trial-excluded"
            )
            manifest_path = runs_dir / "_archive" / "archive-manifest.jsonl"
            manifest = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]

            self.assertFalse(run_dir.exists())
            self.assertTrue((archived_run / "result.json").exists())
            self.assertFalse(discover_result_files(runs_dir))
            self.assertFalse(archive_result.dry_run)
            self.assertEqual(archive_result.manifest_path, manifest_path)
            self.assertEqual(manifest[0]["trial_id"], "trial-excluded")
            self.assertEqual(manifest[0]["task_id"], "task-a")
            self.assertEqual(manifest[0]["agent_harness"], "codex")
            self.assertEqual(manifest[0]["exclusion_reason"], "setup_error")
            self.assertEqual(manifest[0]["original_path"], str(run_dir))
            self.assertEqual(manifest[0]["archived_path"], str(archived_run))


def _write_result(
    run_dir: Path,
    trial_id: str,
    *,
    success: bool,
    trial_validity: str = "valid",
    exclusion_reason: str | None = None,
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
                "agent_name": "codex",
                "model_name": "",
                "status": "passed" if success else "failed",
                "success": success,
                "trial_validity": trial_validity,
                "exclusion_reason": exclusion_reason,
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
