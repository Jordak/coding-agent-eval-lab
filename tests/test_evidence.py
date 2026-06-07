from pathlib import Path
import unittest

from agentlab.evidence.human_review import create_human_review_outcome
from agentlab.evidence.outcome import normalize_outcome_evidence
from agentlab.reports.capability_digest import render_capability_evidence_digest
from agentlab.reports.capability_digest_html import (
    render_capability_evidence_digest_html,
)


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
        self.assertIn("## Run Context: starter / codex / model-a / xhigh", digest)
        self.assertIn("- Suite: `starter`", digest)
        self.assertIn("- Agent Harness: `codex`", digest)
        self.assertIn("- Model: `model-a`", digest)
        self.assertIn("- Effort: `xhigh`", digest)
        self.assertIn("### Outcome Summary", digest)
        self.assertIn("### Token Summary", digest)
        self.assertIn("### Review and Patch Summary", digest)
        self.assertIn("### Trial Evidence", digest)
        self.assertIn("Portable Markdown policy:", digest)
        self.assertIn(
            "| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |",
            digest,
        )
        self.assertIn("| task-a | regression | 2 | 1 | 1 | 1 | 1 | 1.00 | 1.00 | 1.00 |", digest)
        self.assertIn("| task-a | regression | 15 | 4 | 2 | 15 | 15 | 4 | 2 |", digest)
        self.assertIn("| task-a | regression | 100 | 1 | 5 | 1 | success_clean:1 | resource_inefficient:1 | setup_error:1 |", digest)
        self.assertIn("| task-a | regression | trial-pass | passed | valid | success_clean | resource_inefficient |", digest)
        self.assertIn("| 1 | 5 | 1 | 10 | 4 | 5 | 2 | unknown | 100 |", digest)
        self.assertIn("| task-a | regression | trial-excluded | failed | excluded | dependency_issue |  | setup_error |", digest)
        self.assertNotIn("| Suite | Type | Task | Agent Harness | Model | Effort |", digest)
        self.assertNotIn("| Trial | Task | Agent Harness | Model | Effort |", digest)
        self.assertNotIn("| Report | Transcript | Diff | Result |", digest)
        self.assertNotIn("[report](", digest)
        self.assertNotIn("[transcript](", digest)
        self.assertNotIn("[diff](", digest)
        self.assertNotIn("[result](", digest)
        self.assertNotIn("runs/trial-pass/report.md", digest)

    def test_digest_marks_setup_created_untracked_patch_size_caveat(self):
        result = normalize_outcome_evidence(
            {
                "trial_id": "trial-caveat",
                "task_id": "task-a",
                "eval_suite": "starter",
                "eval_type": "regression",
                "agent_name": "codex",
                "model_name": "model-a",
                "status": "passed",
                "success": True,
                "duration_ms": 100,
                "files_changed": ["setup.log"],
                "lines_added": 5,
                "lines_deleted": 1,
                "setup_created_untracked_changed_paths": ["setup.log"],
                "report_path": "runs/trial-caveat/report.md",
                "diff_path": "runs/trial-caveat/diff.patch",
                "run_dir": "runs/trial-caveat",
            }
        )

        digest = render_capability_evidence_digest([result])
        html_report = render_capability_evidence_digest_html([result])

        self.assertIn("5*", digest)
        self.assertIn("1*", digest)
        self.assertIn("| task-a | regression | 100 | 1 | 5* | 1* |", digest)
        self.assertIn("Patch size metrics marked with `*`", digest)
        self.assertIn("have setup-created untracked path caveats", digest)
        self.assertIn("changed-file counts/lists", digest)
        self.assertIn("boundary metrics", digest)
        self.assertIn("include detected caveat paths", digest)
        self.assertIn("5*", html_report)
        self.assertIn("1*", html_report)
        self.assertGreaterEqual(digest.count("Patch size metrics marked with `*`"), 2)
        self.assertGreaterEqual(html_report.count("Patch size metrics marked with *"), 2)
        self.assertGreaterEqual(html_report.count(">5*</td>"), 2)
        self.assertIn("Patch size metrics marked with *", html_report)
        self.assertIn("have setup-created untracked path caveats", html_report)
        self.assertIn("changed-file counts/lists", html_report)
        self.assertIn("boundary metrics", html_report)
        self.assertIn("include detected caveat paths", html_report)

    def test_nested_setup_created_untracked_patch_size_caveat_round_trips(self):
        result = normalize_outcome_evidence(
            {
                "trial_id": "trial-caveat",
                "task_id": "task-a",
                "eval_suite": "starter",
                "eval_type": "regression",
                "agent_name": "codex",
                "model_name": "model-a",
                "status": "passed",
                "success": True,
                "duration_ms": 100,
                "files_changed": ["setup.log"],
                "lines_added": 5,
                "lines_deleted": 1,
                "outcome": {
                    "setup_created_untracked_changed_paths": ["setup.log"],
                },
                "run_dir": "runs/trial-caveat",
            }
        )

        result_dict = result.to_result_dict()

        self.assertEqual(
            result.setup_created_untracked_changed_paths,
            ["setup.log"],
        )
        self.assertEqual(
            result_dict["setup_created_untracked_changed_paths"],
            ["setup.log"],
        )
        self.assertEqual(
            result_dict["outcome"]["setup_created_untracked_changed_paths"],
            ["setup.log"],
        )

    def test_markdown_digest_omits_disposable_artifact_paths(self):
        digest = render_capability_evidence_digest(
            [
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-portable",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "codex",
                        "model_name": "model-a",
                        "status": "passed",
                        "success": True,
                        "duration_ms": 100,
                        "files_changed": ["app.py"],
                        "lines_added": 5,
                        "lines_deleted": 1,
                        "report_path": "/tmp/worktree/runs/trial-portable/report.md",
                        "transcript_path": "/tmp/worktree/runs/trial-portable/transcript.md",
                        "diff_path": "/tmp/worktree/runs/trial-portable/diff.patch",
                        "run_dir": "/tmp/worktree/runs/trial-portable",
                    }
                )
            ]
        )

        self.assertIn("| task-a | capability | trial-portable | passed | valid |", digest)
        self.assertNotIn("| Report | Transcript | Diff | Result |", digest)
        self.assertNotIn("[report](", digest)
        self.assertNotIn("/tmp/worktree", digest)
        self.assertNotIn("runs/trial-portable/report.md", digest)

    def test_renders_one_markdown_section_per_run_context(self):
        digest = render_capability_evidence_digest(
            [
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-codex",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "codex",
                        "model_name": "model-a",
                        "agent_harness_config": {"reasoning_effort": "xhigh"},
                        "status": "passed",
                        "success": True,
                        "duration_ms": 100,
                        "files_changed": [],
                        "lines_added": 0,
                        "lines_deleted": 0,
                        "run_dir": "runs/trial-codex",
                    }
                ),
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-claude",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "capability",
                        "agent_name": "claude",
                        "model_name": "model-b",
                        "agent_harness_config": {"reasoning_effort": "medium"},
                        "status": "failed",
                        "success": False,
                        "duration_ms": 200,
                        "files_changed": [],
                        "lines_added": 0,
                        "lines_deleted": 0,
                        "run_dir": "runs/trial-claude",
                    }
                ),
            ]
        )

        self.assertEqual(digest.count("## Run Context:"), 2)
        codex_section = digest.split(
            "## Run Context: starter / codex / model-a / xhigh",
            1,
        )[1].split("## Run Context:", 1)[0]
        claude_section = digest.split(
            "## Run Context: starter / claude / model-b / medium",
            1,
        )[1]
        self.assertIn("| task-a | capability | trial-codex | passed |", codex_section)
        self.assertNotIn("trial-claude", codex_section)
        self.assertIn("| task-a | capability | trial-claude | failed |", claude_section)
        self.assertNotIn("| Suite | Type | Task | Agent Harness | Model | Effort |", digest)

    def test_renders_canonical_audit_html_companion(self):
        repo_root = Path("/workspace/agent-eval-lab")
        html_report = render_capability_evidence_digest_html(
            [
                normalize_outcome_evidence(
                    {
                        "trial_id": "trial-pass",
                        "task_id": "task-a",
                        "eval_suite": "starter",
                        "eval_type": "regression",
                        "agent_name": "codex",
                        "model_name": "model-a",
                        "agent_harness_config": {
                            "reasoning_effort": "xhigh",
                            "sandbox": "workspace-write",
                            "approval_policy": "never",
                        },
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
                )
            ],
            {"name": "codex selected evidence", "selected_entries": 1},
            source_path=repo_root / "reports" / "digest.md",
            output_path=repo_root / "reports" / "digest.html",
            repo_root=repo_root,
        )

        self.assertIn("<!doctype html>", html_report)
        self.assertNotRegex(html_report, r"[ \t]+\n")
        self.assertIn("<h2>Outcome Summary</h2>", html_report)
        self.assertIn("<h2>Agent Harness Operability</h2>", html_report)
        self.assertIn("sandbox_mode: workspace-write", html_report)
        self.assertIn("approval_policy: never", html_report)
        self.assertIn("<h2>Token Summary</h2>", html_report)
        self.assertIn("<h2>Review and Patch Summary</h2>", html_report)
        self.assertIn("<h2>Trial Evidence</h2>", html_report)
        self.assertIn("<h3>Needs Attention</h3>", html_report)
        self.assertIn("<h3>Highest IO Token Tasks</h3>", html_report)
        self.assertIn(
            '<span>Source</span><strong><a href="digest.md">reports/digest.md</a>',
            html_report,
        )
        self.assertIn(
            '<a href="../tasks/starter/task-a/task-card.md">task-a</a>',
            html_report,
        )
        self.assertIn(
            '<a href="../runs/trial-pass/report.md">report</a>',
            html_report,
        )
        self.assertIn(
            "resource_inefficient on 1/1 trials (1 secondary)",
            html_report,
        )
        self.assertNotIn("Context Overview", html_report)
        self.assertNotIn("Task Folders", html_report)

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
        self.assertIn("## Run Context: starter / codex / model-a / xhigh", digest)
        self.assertIn("| task-a | regression | 1 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 |", digest)
        self.assertIn("| task-a | regression | 15 | 4 | 2 | unknown | unknown | unknown | unknown |", digest)
        self.assertIn("| task-a | regression | 100 | 0 | 0 | 0 | bad_local_fix:1 |  |  |", digest)

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
            "## Run Context: starter / codex / unknown / unknown",
            digest,
        )
        self.assertIn(
            "| task-a | regression | 1 | 1 | 0 | 1 | 0 |",
            digest,
        )
        self.assertIn(
            "| task-a | regression | trial-unknown-model | passed |",
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
