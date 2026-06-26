from __future__ import annotations

import unittest
from pathlib import Path

from agentlab.evidence.outcome import normalize_outcome_evidence
from agentlab.reports.operability_evidence import (
    render_agent_harness_operability_table,
)


class OperabilityEvidenceTest(unittest.TestCase):
    def test_render_agent_harness_operability_table_uses_raw_result_fields(self):
        codex = _result(
            trial_id="codex-pass",
            agent_name="codex",
            model_name="gpt-test",
            status="passed",
            success=True,
            config={
                "agent_harness": "codex",
                "agent_adapter": "codex_cli",
                "model_name": "gpt-test",
                "reasoning_effort": "xhigh",
                "sandbox": "workspace-write",
                "approval_policy": "never",
                "timeout_seconds": 1800,
            },
            input_tokens=10,
            output_tokens=5,
            cost_usd=None,
        )
        claude = _result(
            trial_id="claude-fail",
            agent_name="claude",
            model_name="claude-test",
            status="failed",
            success=False,
            config={
                "agent_harness": "claude_code",
                "agent_adapter": "claude_code_cli",
                "model_name": "claude-test",
                "permission_mode": "acceptEdits",
                "max_turns": None,
                "allowed_tools": [],
                "disallowed_tools": ["Bash(git push *)"],
                "timeout_seconds": 1800,
                "no_session_persistence": True,
            },
            input_tokens=20,
            output_tokens=8,
            cost_usd=0.12,
        )

        table = "\n".join(render_agent_harness_operability_table([codex, claude]))

        self.assertIn("### Agent Harness Operability", table)
        self.assertIn("| Operability Dimension | Evidence |", table)
        self.assertIn("sandbox_mode: `workspace-write", table)
        self.assertIn("approval_policy: `acceptEdits; never`", table)
        self.assertIn("disallowed_tools", table)
        self.assertIn("timeout_seconds: `1800`", table)
        self.assertIn("observed_input_output_tokens: `2/2`", table)
        self.assertIn("observed_cost_usd: `1/2`", table)
        self.assertIn("normalized_or_derived_stop_reason", table)
        self.assertIn("first_class_halt_reason_taxonomy: `unknown`", table)
        self.assertIn("intermediate_verifier_movement: `unknown`", table)
        self.assertIn("hidden_verifier_configured: `unknown`", table)
        self.assertIn("hidden_verifier_checks: `unknown`", table)
        self.assertIn(
            "budget_operator_interruption_taxonomy: `unknown`",
            table,
        )
        self.assertIn("report_md: `2/2`", table)
        self.assertIn("result_json: `2/2`", table)

    def test_render_agent_harness_operability_table_marks_absent_receipts_unknown(self):
        result = _result(
            trial_id="codex-pass",
            agent_name="codex",
            model_name="gpt-test",
            status="passed",
            success=True,
            config={"agent_harness": "codex"},
            input_tokens=None,
            output_tokens=None,
            cost_usd=None,
        )

        table = "\n".join(render_agent_harness_operability_table([result]))

        self.assertIn("observed_input_output_tokens: `unknown`", table)
        self.assertIn("normalized_or_derived_stop_reason: `success`", table)
        self.assertIn("first_class_halt_reason_taxonomy: `unknown`", table)
        self.assertNotIn("stored_stop_reason", table)
        self.assertIn(
            "interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`",
            table,
        )
        self.assertIn("configured_token_cost_quota_limits: `unknown`", table)

    def test_render_agent_harness_operability_table_requires_input_and_output_tokens(self):
        result = _result(
            trial_id="codex-partial-tokens",
            agent_name="codex",
            model_name="gpt-test",
            status="passed",
            success=True,
            config={"agent_harness": "codex"},
            input_tokens=10,
            output_tokens=None,
            cost_usd=None,
        )

        table = "\n".join(render_agent_harness_operability_table([result]))

        self.assertIn("observed_input_output_tokens: `unknown`", table)

    def test_render_agent_harness_operability_table_keeps_reasoning_effort_out_of_budget_controls(self):
        result = _result(
            trial_id="codex-reasoning-effort",
            agent_name="codex",
            model_name="gpt-test",
            status="passed",
            success=True,
            config={
                "agent_harness": "codex",
                "reasoning_effort": "xhigh",
            },
            input_tokens=10,
            output_tokens=5,
            cost_usd=None,
        )

        table = "\n".join(render_agent_harness_operability_table([result]))

        self.assertIn("reasoning_effort: `xhigh`", table)
        self.assertIn("turn_or_step_budget: `unknown`", table)
        self.assertNotIn('turn_or_step_budget: `{"reasoning_effort": "xhigh"}`', table)

    def test_render_agent_harness_operability_table_reports_hidden_verifier_state(self):
        result = _result(
            trial_id="codex-hidden-verifier",
            agent_name="codex",
            model_name="gpt-test",
            status="passed",
            success=True,
            config={"agent_harness": "codex"},
            input_tokens=10,
            output_tokens=5,
            cost_usd=None,
            commands_run=[],
            checks=[],
            graders=[],
            hidden_verifier={
                "patch": "verifier.patch",
                "checks": [
                    {
                        "command": "pytest tests/hidden_behavior.py",
                        "returncode": 0,
                        "passed": True,
                    }
                ],
            },
        )

        table = "\n".join(render_agent_harness_operability_table([result]))

        self.assertIn("checks_array: `unknown`", table)
        self.assertIn("graders_array: `unknown`", table)
        self.assertIn("hidden_verifier_configured: `1/1`", table)
        self.assertIn("hidden_verifier_checks: `1/1`", table)


def _result(
    *,
    trial_id: str,
    agent_name: str,
    model_name: str,
    status: str,
    success: bool,
    config: dict[str, object],
    input_tokens: int | None,
    output_tokens: int | None,
    cost_usd: float | None,
    commands_run: list[object] | None = None,
    checks: list[object] | None = None,
    graders: list[object] | None = None,
    hidden_verifier: dict[str, object] | None = None,
):
    run_dir = Path("/tmp") / trial_id
    payload = {
            "trial_kind": "agent_trial",
            "trial_id": trial_id,
            "run_id": trial_id,
            "task_id": "task-a",
            "eval_suite": "starter-coding",
            "eval_type": "capability",
            "agent_name": agent_name,
            "model_name": model_name,
            "agent_harness_config": config,
            "status": status,
            "success": success,
            "duration_ms": 100,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "files_changed": ["app.py"],
            "lines_added": 3,
            "lines_deleted": 1,
            "commands_run": ["pytest"] if commands_run is None else commands_run,
            "checks": (
                [{"name": "pytest", "status": status}]
                if checks is None
                else checks
            ),
            "graders": [{"name": "pytest"}] if graders is None else graders,
            "report_path": str(run_dir / "report.md"),
            "transcript_path": str(run_dir / "transcript.md"),
            "diff_path": str(run_dir / "diff.patch"),
            "run_dir": str(run_dir),
        }
    if hidden_verifier is not None:
        payload["hidden_verifier"] = hidden_verifier
    return normalize_outcome_evidence(
        payload,
        run_dir=run_dir,
    )


if __name__ == "__main__":
    unittest.main()
