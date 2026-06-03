from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agentlab.cli import main
from agentlab.evidence.outcome import load_outcome_evidence
from agentlab.evidence.review_proposals import (
    REVIEW_PROPOSAL_FILENAME,
    ReviewProposalContext,
    clear_review_proposal,
    create_review_proposal,
    generate_review_proposal_for_run,
    load_review_proposal,
    write_review_proposal,
)
from agentlab.evidence.summary import summarize_trials
from agentlab.reports.capability_digest import render_capability_evidence_digest


class ReviewProposalTest(unittest.TestCase):
    def test_writes_and_loads_review_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            proposal = create_review_proposal(
                proposed_primary_label="success_clean",
                proposed_secondary_labels=["resource_inefficient"],
                proposed_note="Focused patch with passing checks.",
                evidence=["diff.patch", "report.md excerpt: all checks passed"],
                proposed_trial_validity="valid",
                proposed_exclusion_reason=None,
                confidence=0.82,
                reviewer_identity="fake-review-agent",
                created_at="2026-06-03T12:00:00Z",
            )

            proposal_path = write_review_proposal(run_dir, proposal)
            loaded = load_review_proposal(run_dir)

        self.assertEqual(proposal_path.name, REVIEW_PROPOSAL_FILENAME)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.proposed_primary_label, "success_clean")
        self.assertEqual(
            loaded.proposed_secondary_labels,
            ("resource_inefficient",),
        )
        self.assertEqual(loaded.proposed_note, "Focused patch with passing checks.")
        self.assertEqual(
            loaded.evidence,
            ("diff.patch", "report.md excerpt: all checks passed"),
        )
        self.assertEqual(loaded.proposed_trial_validity, "valid")
        self.assertIsNone(loaded.proposed_exclusion_reason)
        self.assertEqual(loaded.confidence, 0.82)
        self.assertEqual(loaded.reviewer_identity, "fake-review-agent")
        self.assertEqual(loaded.created_at, "2026-06-03T12:00:00Z")

    def test_excluded_review_proposal_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            proposal = create_review_proposal(
                proposed_primary_label="dependency_issue",
                proposed_note="Task setup failed before the trial was fair.",
                evidence=["report.md excerpt: setup command failed"],
                proposed_trial_validity="excluded",
                proposed_exclusion_reason="setup_error",
                confidence=0.4,
                reviewer_identity="fake-review-agent",
                created_at="2026-06-03T12:00:00Z",
            )

            write_review_proposal(run_dir, proposal)
            loaded = load_review_proposal(run_dir)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.proposed_trial_validity, "excluded")
        self.assertEqual(loaded.proposed_exclusion_reason, "setup_error")

    def test_rejects_invalid_proposal_confidence(self):
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            create_review_proposal(
                proposed_primary_label="success_clean",
                proposed_note="Impossible confidence.",
                confidence=1.2,
                reviewer_identity="fake-review-agent",
            )

    def test_loading_requires_explicit_proposed_trial_validity(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            (run_dir / REVIEW_PROPOSAL_FILENAME).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "proposed_primary_label": "success_clean",
                        "proposed_secondary_labels": [],
                        "proposed_note": "Missing validity.",
                        "evidence": [],
                        "confidence": 0.5,
                        "reviewer_identity": "fake-review-agent",
                        "created_at": "2026-06-03T12:00:00Z",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "requires proposed_trial_validity"):
                load_review_proposal(run_dir)

    def test_clear_review_proposal_removes_draft_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            write_review_proposal(
                run_dir,
                create_review_proposal(
                    proposed_primary_label="success_clean",
                    proposed_note="Draft to clear.",
                    evidence=["diff.patch"],
                    confidence=0.6,
                    reviewer_identity="fake-review-agent",
                    created_at="2026-06-03T12:00:00Z",
                ),
            )

            cleared = clear_review_proposal(run_dir)
            cleared_again = clear_review_proposal(run_dir)

        self.assertIsNotNone(cleared)
        assert cleared is not None
        self.assertEqual(cleared.name, REVIEW_PROPOSAL_FILENAME)
        self.assertIsNone(cleared_again)
        self.assertFalse(cleared.exists())

    def test_fake_proposer_can_generate_review_proposal_for_run(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-pass"
            run_dir.mkdir()
            _write_result(run_dir, "trial-pass", success=True)
            proposer = _FakeProposer(
                create_review_proposal(
                    proposed_primary_label="success_clean",
                    proposed_note="Fake proposer accepted this clean run.",
                    evidence=["fake evidence"],
                    confidence=0.9,
                    reviewer_identity="fake-review-agent",
                    created_at="2026-06-03T12:00:00Z",
                )
            )

            proposal_path, proposal = generate_review_proposal_for_run(
                run_dir,
                proposer,
            )

        self.assertEqual(proposal_path.name, REVIEW_PROPOSAL_FILENAME)
        self.assertEqual(proposal.proposed_primary_label, "success_clean")
        self.assertEqual(len(proposer.contexts), 1)
        self.assertEqual(proposer.contexts[0].result.trial_id, "trial-pass")

    def test_deterministic_proposer_handles_passing_failed_and_invalid_shapes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            passing = root / "trial-pass"
            failing = root / "trial-fail"
            invalid = root / "trial-invalid"
            for run_dir in [passing, failing, invalid]:
                run_dir.mkdir()
            _write_result(passing, "trial-pass", success=True)
            _write_result(failing, "trial-fail", success=False)
            _write_result(
                invalid,
                "trial-invalid",
                success=False,
                error="setup failed: No module named click",
            )

            _, pass_proposal = generate_review_proposal_for_run(passing)
            _, fail_proposal = generate_review_proposal_for_run(failing)
            _, invalid_proposal = generate_review_proposal_for_run(invalid)

        self.assertEqual(pass_proposal.proposed_primary_label, "success_clean")
        self.assertEqual(pass_proposal.proposed_trial_validity, "valid")
        self.assertEqual(fail_proposal.proposed_primary_label, "spec_misread")
        self.assertEqual(fail_proposal.proposed_trial_validity, "valid")
        self.assertEqual(invalid_proposal.proposed_primary_label, "dependency_issue")
        self.assertEqual(invalid_proposal.proposed_trial_validity, "excluded")
        self.assertEqual(invalid_proposal.proposed_exclusion_reason, "setup_error")

    def test_summary_and_digest_ignore_unapplied_review_proposals(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-proposed"
            run_dir.mkdir()
            _write_result(run_dir, "trial-proposed", success=True)
            write_review_proposal(
                run_dir,
                create_review_proposal(
                    proposed_primary_label="success_clean",
                    proposed_note="This should not count until review.json exists.",
                    evidence=["proposal evidence"],
                    confidence=0.9,
                    reviewer_identity="fake-review-agent",
                    created_at="2026-06-03T12:00:00Z",
                ),
            )

            evidence = load_outcome_evidence(run_dir / "result.json")

        self.assertIsNotNone(evidence)
        assert evidence is not None
        summary = summarize_trials([evidence])[0]
        digest = render_capability_evidence_digest([evidence])
        self.assertEqual(evidence.primary_review_label, "")
        self.assertEqual(summary.accepted_results, 0)
        self.assertEqual(summary.review_labels, {})
        self.assertNotIn("success_clean", digest)
        self.assertNotIn("This should not count", digest)

    def test_cli_generates_review_proposal_for_one_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs_dir = root / "runs"
            run_dir = runs_dir / "trial-pass"
            run_dir.mkdir(parents=True)
            _write_result(run_dir, "trial-pass", success=True)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(
                    [
                        "review-proposals",
                        "run",
                        "--run",
                        str(run_dir),
                        "--reviewer",
                        "cli-reviewer",
                    ]
                )

            proposal = load_review_proposal(run_dir)

        self.assertEqual(status, 0)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Heuristic review proposal:", stdout.getvalue())
        self.assertIsNotNone(proposal)
        assert proposal is not None
        self.assertEqual(proposal.proposed_primary_label, "success_clean")
        self.assertEqual(proposal.reviewer_identity, "cli-reviewer")

    def test_cli_writes_explicit_review_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-write"
            run_dir.mkdir()
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(
                    [
                        "review-proposals",
                        "write",
                        "--run",
                        str(run_dir),
                        "--label",
                        "success_messy",
                        "--secondary",
                        "resource_inefficient",
                        "--note",
                        "Graders passed, but the patch used disproportionate resources.",
                        "--evidence",
                        "result.json: 180000 tokens for a small task",
                        "--confidence",
                        "0.7",
                        "--reviewer",
                        "trial-review-skill",
                    ]
                )

            proposal = load_review_proposal(run_dir)

        self.assertEqual(status, 0)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Review proposal:", stdout.getvalue())
        self.assertIsNotNone(proposal)
        assert proposal is not None
        self.assertEqual(proposal.proposed_primary_label, "success_messy")
        self.assertEqual(proposal.proposed_secondary_labels, ("resource_inefficient",))
        self.assertEqual(proposal.confidence, 0.7)
        self.assertEqual(proposal.reviewer_identity, "trial-review-skill")

    def test_cli_clears_review_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "trial-clear"
            run_dir.mkdir()
            write_review_proposal(
                run_dir,
                create_review_proposal(
                    proposed_primary_label="success_clean",
                    proposed_note="Draft to clear after applying review.",
                    evidence=["report.md"],
                    confidence=0.6,
                    reviewer_identity="fake-review-agent",
                    created_at="2026-06-03T12:00:00Z",
                ),
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(["review-proposals", "clear", "--run", str(run_dir)])

            proposal = load_review_proposal(run_dir)

        self.assertEqual(status, 0)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Cleared review proposal:", stdout.getvalue())
        self.assertIsNone(proposal)

    def test_cli_generates_review_proposals_for_evidence_set(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs_dir = root / "runs"
            passing = runs_dir / "trial-pass"
            failing = runs_dir / "trial-fail"
            passing.mkdir(parents=True)
            failing.mkdir(parents=True)
            _write_result(passing, "trial-pass", success=True)
            _write_result(failing, "trial-fail", success=False)
            evidence_set = root / "evidence.json"
            evidence_set.write_text(
                json.dumps(
                    {
                        "name": "selected trials",
                        "trials": ["trial-pass", "trial-fail/result.json"],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(
                    [
                        "review-proposals",
                        "evidence-set",
                        "--runs-dir",
                        str(runs_dir),
                        "--evidence-set",
                        str(evidence_set),
                        "--reviewer",
                        "cli-reviewer",
                    ]
                )

            passing_proposal = load_review_proposal(passing)
            failing_proposal = load_review_proposal(failing)

        self.assertEqual(status, 0)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Generated heuristic review proposals: 2", stdout.getvalue())
        self.assertIsNotNone(passing_proposal)
        self.assertIsNotNone(failing_proposal)
        assert passing_proposal is not None
        assert failing_proposal is not None
        self.assertEqual(passing_proposal.proposed_primary_label, "success_clean")
        self.assertEqual(failing_proposal.proposed_primary_label, "spec_misread")
        self.assertEqual(passing_proposal.reviewer_identity, "cli-reviewer")
        self.assertEqual(failing_proposal.reviewer_identity, "cli-reviewer")


class _FakeProposer:
    def __init__(self, proposal):
        self.proposal = proposal
        self.contexts: list[ReviewProposalContext] = []

    def propose(self, context: ReviewProposalContext):
        self.contexts.append(context)
        return self.proposal


def _write_result(
    run_dir: Path,
    trial_id: str,
    *,
    success: bool,
    error: str | None = None,
) -> None:
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "trial_kind": "agent_trial",
                "trial_id": trial_id,
                "run_id": trial_id,
                "task_id": "task-a",
                "task_title": "Task A",
                "eval_suite": "starter",
                "eval_type": "capability",
                "agent_name": "codex",
                "model_name": "gpt-test",
                "agent_harness_config": {},
                "status": "passed" if success else "failed",
                "success": success,
                "duration_ms": 100,
                "error": error,
                "files_changed": ["app.py"] if success else [],
                "lines_added": 5 if success else 0,
                "lines_deleted": 1 if success else 0,
                "checks": [
                    {
                        "command": "python3 -m pytest",
                        "passed": success,
                        "stdout": "",
                        "stderr": error or "",
                    }
                ],
                "report_path": str(run_dir / "report.md"),
                "diff_path": str(run_dir / "diff.patch"),
                "transcript_path": str(run_dir / "transcript.md"),
                "run_dir": str(run_dir),
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "report.md").write_text(
        "# Trial report\n\nAll checks passed." if success else "# Trial report\n\nChecks failed.",
        encoding="utf-8",
    )
    (run_dir / "diff.patch").write_text(
        "diff --git a/app.py b/app.py\n" if success else "",
        encoding="utf-8",
    )
    (run_dir / "transcript.md").write_text(
        "Agent attempted the task.",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
