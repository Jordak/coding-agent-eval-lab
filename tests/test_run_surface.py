import unittest
from pathlib import Path
from types import SimpleNamespace

from agentlab.agents.claude_code import (
    ClaudeCodeConfig,
    ClaudeCodeRuntimeFacts,
    claude_code_agent_harness_config,
)
from agentlab.agents.codex_cli import (
    CodexCliConfig,
    CodexRuntimeFacts,
    codex_agent_harness_config,
)
from agentlab.evidence.outcome import normalize_outcome_evidence
from agentlab.reports.capability_digest import render_capability_evidence_digest
from agentlab.reports.trial_markdown import render_markdown_report
from agentlab.runtime.run_surface import RUN_SURFACE_FIELDS, normalize_run_surface


class RunSurfaceTest(unittest.TestCase):
    def test_codex_config_maps_to_neutral_run_surface(self):
        config = codex_agent_harness_config(
            CodexCliConfig(
                command="codex-test",
                model=None,
                sandbox="workspace-write",
                approval_policy="never",
                timeout_seconds=60,
            ),
            runtime_facts=CodexRuntimeFacts(cli_version="codex 1.2.3"),
        )

        surface = normalize_run_surface(
            None,
            agent_harness_config=config,
            agent_name="codex",
            status="passed",
            success=True,
        )

        self.assertEqual(surface["execution_surface"], "local_cli")
        self.assertEqual(surface["runtime_version"], "codex 1.2.3")
        self.assertEqual(surface["model_identity_source"], "unknown")
        self.assertEqual(surface["sandbox_mode"], "workspace-write")
        self.assertEqual(surface["approval_policy"], "never")
        self.assertEqual(surface["tool_policy"], "unknown")
        self.assertEqual(surface["network_policy"], "unknown")
        self.assertEqual(surface["timeout_seconds"], 60)
        self.assertEqual(surface["stop_reason"], "success")
        self.assertEqual(surface["human_intervention_events"], [])
        self.assertEqual(surface["workspace_history_policy"], "unknown")
        self.assertEqual(surface["workspace_base_ref"], "unknown")

    def test_reasoning_effort_is_not_turn_or_step_budget(self):
        surface = normalize_run_surface(
            None,
            agent_harness_config={
                "agent_harness": "codex",
                "agent_adapter": "codex_cli",
                "reasoning_effort": "xhigh",
            },
            agent_name="codex",
            status="passed",
            success=True,
        )
        legacy_surface = normalize_run_surface(
            {"turn_or_step_budget": {"reasoning_effort": "xhigh"}},
            agent_harness_config={"agent_harness": "codex"},
            agent_name="codex",
            status="passed",
            success=True,
        )
        explicit_surface = normalize_run_surface(
            None,
            agent_harness_config={
                "agent_harness": "custom",
                "turn_or_step_budget": {"step_budget": 8},
            },
            agent_name="custom",
            status="passed",
            success=True,
        )

        self.assertEqual(surface["turn_or_step_budget"], "unknown")
        self.assertEqual(legacy_surface["turn_or_step_budget"], "unknown")
        self.assertEqual(
            explicit_surface["turn_or_step_budget"],
            {"step_budget": 8},
        )

    def test_claude_config_maps_to_neutral_run_surface(self):
        config = claude_code_agent_harness_config(
            ClaudeCodeConfig(
                command="claude-test",
                model=None,
                permission_mode="acceptEdits",
                max_turns=8,
                allowed_tools=("Read", "Edit"),
                disallowed_tools=("Bash(git push *)",),
                timeout_seconds=60,
                no_session_persistence=True,
            ),
            runtime_facts=ClaudeCodeRuntimeFacts(cli_version="2.1.118"),
        )

        surface = normalize_run_surface(
            None,
            agent_harness_config=config,
            agent_name="claude",
            status="failed",
            success=False,
        )

        self.assertEqual(surface["execution_surface"], "local_cli")
        self.assertEqual(surface["runtime_version"], "2.1.118")
        self.assertEqual(surface["approval_policy"], "acceptEdits")
        self.assertEqual(
            surface["tool_policy"],
            {
                "allowed_tools": ["Read", "Edit"],
                "disallowed_tools": ["Bash(git push *)"],
            },
        )
        self.assertEqual(surface["memory_scope"], "no_session_persistence")
        self.assertEqual(surface["turn_or_step_budget"], {"max_turns": 8})
        self.assertEqual(surface["stop_reason"], "grader_failure")

    def test_manual_and_missing_fields_are_explicit(self):
        surface = normalize_run_surface(
            None,
            agent_harness_config={
                "agent_harness": "manual",
                "agent_adapter": "manual",
                "human_intervention_events": ["manual_edit_pause"],
            },
            agent_name="manual",
            status="passed",
            success=True,
        )

        self.assertEqual(sorted(surface), sorted(RUN_SURFACE_FIELDS))
        self.assertEqual(surface["execution_surface"], "unknown")
        self.assertEqual(surface["runtime_version"], "unknown")
        self.assertEqual(surface["sandbox_mode"], "unknown")
        self.assertEqual(surface["approval_policy"], "unknown")
        self.assertEqual(surface["tool_policy"], "unknown")
        self.assertEqual(surface["memory_scope"], "unknown")
        self.assertEqual(surface["network_policy"], "unknown")
        self.assertEqual(surface["timeout_seconds"], "unknown")
        self.assertEqual(surface["turn_or_step_budget"], "unknown")
        self.assertEqual(surface["human_intervention_events"], ["manual_edit_pause"])
        self.assertEqual(surface["workspace_history_policy"], "unknown")
        self.assertEqual(surface["workspace_base_ref"], "unknown")

    def test_trial_report_renders_run_surface(self):
        agent_harness_config = codex_agent_harness_config(
            CodexCliConfig(
                command="codex-test",
                sandbox="workspace-write",
                approval_policy="never",
                timeout_seconds=60,
            ),
            runtime_facts=CodexRuntimeFacts(cli_version="codex 1.2.3"),
        )
        agent_harness_config["reasoning_effort"] = "xhigh"
        run = SimpleNamespace(
            task=SimpleNamespace(id="task-a", suite="starter", eval_type="regression"),
            run_dir=Path("runs/trial-a"),
            score=SimpleNamespace(tests_passed=True, checks=[], notes=[]),
            agent_run=SimpleNamespace(
                agent_name="codex",
                agent_harness_config=agent_harness_config,
                files_changed=[],
                lines_added=0,
                lines_deleted=0,
                transcript_path=Path("transcript.md"),
                diff_path=Path("diff.patch"),
                duration_ms=123,
                input_tokens=None,
                cached_input_tokens=None,
                output_tokens=None,
                reasoning_output_tokens=None,
                cost_usd=None,
                error=None,
            ),
            workspace_history_policy="base_only",
            workspace_base_ref="abc123",
        )

        report = render_markdown_report(run)

        self.assertIn("## Run Surface", report)
        self.assertIn("- Execution surface: `local_cli`", report)
        self.assertIn("- Runtime version: `codex 1.2.3`", report)
        self.assertIn("- Sandbox mode: `workspace-write`", report)
        self.assertIn("- Approval policy: `never`", report)
        self.assertIn("- Turn or step budget: `unknown`", report)
        self.assertIn("- Stop reason: `success`", report)
        self.assertIn("- Workspace history policy: `base_only`", report)
        self.assertIn("- Workspace base ref: `abc123`", report)
        self.assertIn("## Agent Harness Configuration", report)
        self.assertIn("- Reasoning effort: `xhigh`", report)

    def test_capability_digest_includes_run_surface_summary(self):
        result = normalize_outcome_evidence(
            {
                "trial_id": "trial-a",
                "task_id": "task-a",
                "eval_suite": "starter",
                "eval_type": "regression",
                "agent_name": "codex",
                "model_name": "gpt-test",
                "agent_harness_config": {
                    "agent_harness": "codex",
                    "agent_adapter": "codex_cli",
                    "model_source": "events",
                    "sandbox": "workspace-write",
                    "approval_policy": "never",
                    "timeout_seconds": 60,
                    "cli_version": "codex 1.2.3",
                },
                "status": "passed",
                "success": True,
                "run_surface": {
                    "workspace_history_policy": "base_only",
                    "workspace_base_ref": "abc123",
                },
                "duration_ms": 123,
                "files_changed": [],
                "lines_added": 0,
                "lines_deleted": 0,
                "run_dir": "runs/trial-a",
            }
        )

        digest = render_capability_evidence_digest([result])

        self.assertIn("### Run Surface", digest)
        self.assertIn(
            "| Execution Surface | Runtime Version | Model Source | Sandbox | Approval | Memory | Network | Timeout Seconds | Stop Reason | Workspace History | Workspace Base Ref |",
            digest,
        )
        self.assertIn(
            "| local_cli | codex 1.2.3 | events | workspace-write | never | unknown | unknown | 60 | success | base_only | abc123 |",
            digest,
        )

    def test_historical_result_loads_with_backfilled_run_surface(self):
        result = normalize_outcome_evidence(
            {
                "trial_id": "trial-a",
                "agent_name": "claude",
                "model_name": None,
                "agent_harness_config": {
                    "agent_harness": "claude_code",
                    "agent_adapter": "claude_code_cli",
                    "permission_mode": "acceptEdits",
                    "no_session_persistence": True,
                },
                "status": "failed",
                "success": False,
            }
        )

        self.assertEqual(result.run_surface["execution_surface"], "local_cli")
        self.assertEqual(result.run_surface["approval_policy"], "acceptEdits")
        self.assertEqual(
            result.run_surface["memory_scope"],
            "no_session_persistence",
        )
        self.assertEqual(result.run_surface["stop_reason"], "grader_failure")
        self.assertEqual(result.run_surface["workspace_history_policy"], "unknown")
        self.assertEqual(result.run_surface["workspace_base_ref"], "unknown")
