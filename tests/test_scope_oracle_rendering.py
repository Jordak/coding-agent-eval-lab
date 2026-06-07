import unittest
from pathlib import Path
from types import SimpleNamespace

from agentlab.evidence.results import reference_verification_to_result_dict
from agentlab.evidence.results import to_result_dict
from agentlab.reports.trial_markdown import render_markdown_report
from agentlab.reports.trial_markdown import render_reference_report
from agentlab.tasks import EvalTask, SuccessCriteria


class ScopeOracleRenderingTest(unittest.TestCase):
    def test_trial_report_and_result_json_render_scope_oracle_metadata(self):
        run = _run_with_scope_oracle()

        report = render_markdown_report(run)
        result = to_result_dict(run)

        self.assertIn("## Scope Oracle Metadata", report)
        self.assertIn("- Consent style: `implicit_allow`", report)
        self.assertIn("- Allowed paths: `src/`", report)
        self.assertIn("- Forbidden paths: `src/private/`", report)
        self.assertEqual(
            result["scope_oracle"],
            {
                "consent_style": "implicit_allow",
                "allowed_paths": ["src/"],
                "forbidden_paths": ["src/private/"],
            },
        )

    def test_patch_size_caveat_renders_for_setup_created_untracked_changes(self):
        run = _run_with_scope_oracle()
        run.agent_run.setup_created_untracked_changed_paths = ["setup.log"]

        report = render_markdown_report(run)
        result = to_result_dict(run)

        self.assertIn("- Lines added: `1`*", report)
        self.assertIn("- Lines deleted: `0`*", report)
        self.assertIn("Patch size metrics marked with `*`", report)
        self.assertIn("changed-file counts/lists", report)
        self.assertIn("boundary metrics", report)
        self.assertIn("include detected caveat paths", report)
        self.assertIn("`setup.log`", report)
        self.assertEqual(
            result["setup_created_untracked_changed_paths"],
            ["setup.log"],
        )
        self.assertEqual(
            result["outcome"]["setup_created_untracked_changed_paths"],
            ["setup.log"],
        )

    def test_reference_report_renders_setup_created_untracked_caveat(self):
        verification = SimpleNamespace(
            task=_run_with_scope_oracle().task,
            success=True,
            files_changed=["setup.log"],
            lines_added=2,
            lines_deleted=1,
            setup_created_untracked_changed_paths=["setup.log"],
            all_checks=[],
            notes=[],
            report_path=Path("reference-report.md"),
            result_path=Path("reference-result.json"),
            diff_path=Path("reference.diff"),
        )

        report = render_reference_report(verification)
        result = reference_verification_to_result_dict(verification)

        self.assertIn("- Lines added: `2`*", report)
        self.assertIn("- Lines deleted: `1`*", report)
        self.assertIn("Patch size metrics marked with `*`", report)
        self.assertIn("changed-file counts/lists", report)
        self.assertIn("boundary metrics", report)
        self.assertIn("include detected caveat paths", report)
        self.assertIn("`setup.log`", report)
        self.assertEqual(
            result["setup_created_untracked_changed_paths"],
            ["setup.log"],
        )
        self.assertEqual(
            result["outcome"]["setup_created_untracked_changed_paths"],
            ["setup.log"],
        )


def _run_with_scope_oracle():
    task = EvalTask(
        id="scope-task",
        title="Scope task",
        repo="https://github.com/example/repo",
        commit="abc123",
        language="python",
        prompt="Fix it.",
        consent_style="implicit_allow",
        success=SuccessCriteria(
            allowed_paths=["src/"],
            forbidden_paths=["src/private/"],
        ),
    )
    return SimpleNamespace(
        task=task,
        run_dir=Path("runs/trial-a"),
        report_path=Path("runs/trial-a/report.md"),
        result_path=Path("runs/trial-a/result.json"),
        score=SimpleNamespace(tests_passed=True, checks=[], notes=[]),
        agent_run=SimpleNamespace(
            agent_name="manual",
            model_name=None,
            agent_harness_config={},
            files_changed=["src/app.py"],
            lines_added=1,
            lines_deleted=0,
            transcript_path=Path("transcript.md"),
            diff_path=Path("diff.patch"),
            commands_run=[],
            duration_ms=123,
            setup_created_untracked_changed_paths=[],
            input_tokens=None,
            cached_input_tokens=None,
            output_tokens=None,
            reasoning_output_tokens=None,
            cost_usd=None,
            error=None,
        ),
    )


if __name__ == "__main__":
    unittest.main()
