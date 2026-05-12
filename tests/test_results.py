import json
import tempfile
import unittest
from pathlib import Path

from agentlab.evidence import render_capability_evidence_digest
from agentlab.results import discover_result_files, load_results
from agentlab.review import write_review
from agentlab.summary import summarize_trials


MODEL_IDENTITY_FIXTURES = Path(__file__).parent / "fixtures" / "model_identity"


class ResultsTest(unittest.TestCase):
    def test_file_artifacts_feed_trial_listing_summaries_reviews_and_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            runs_dir = Path(temp) / "runs"
            passing_run = runs_dir / "trial-pass"
            excluded_run = runs_dir / "trial-excluded"
            reference_run = runs_dir / "reference-verification"
            passing_run.mkdir(parents=True)
            excluded_run.mkdir()
            reference_run.mkdir()

            self._write_result(passing_run, trial_id="trial-pass", success=True)
            self._write_result(excluded_run, trial_id="trial-excluded", success=False)
            self._write_result(
                reference_run,
                trial_id="task-a-reference",
                success=True,
                trial_kind="reference_verification",
            )
            write_review(
                excluded_run,
                primary_label="dependency_issue",
                note="The Task environment was invalid before the Agent harness acted.",
                trial_validity="excluded",
                exclusion_reason="setup_error",
            )

            result_files = discover_result_files(runs_dir)
            self.assertEqual(
                result_files,
                [
                    reference_run / "result.json",
                    excluded_run / "result.json",
                    passing_run / "result.json",
                ],
            )

            results = load_results(result_files)
            self.assertEqual(
                [result["trial_id"] for result in results],
                ["trial-excluded", "trial-pass"],
            )
            excluded = results[0]
            self.assertEqual(excluded["review"]["primary_label"], "dependency_issue")
            self.assertEqual(excluded["trial_validity"], "excluded")
            self.assertEqual(excluded["exclusion_reason"], "setup_error")

            summary = summarize_trials(results)[0]
            self.assertEqual(summary.total_trials, 2)
            self.assertEqual(summary.trials, 1)
            self.assertEqual(summary.excluded_trials, 1)
            self.assertEqual(summary.passes, 1)

            digest = render_capability_evidence_digest(results)
            self.assertIn("- Agent trials: `2`", digest)
            self.assertIn("setup_error:1", digest)
            self.assertIn("trial-pass/result.json", digest)

    def test_load_results_backfills_line_metrics_from_diff_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            (run_dir / "diff.patch").write_text(
                """diff --git a/app.txt b/app.txt
--- a/app.txt
+++ b/app.txt
@@ -1 +1,2 @@
-before
+after
+new
""",
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                        "diff_path": str(run_dir / "diff.patch"),
                        "outcome": {},
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            self.assertEqual(result["lines_added"], 2)
            self.assertEqual(result["lines_deleted"], 1)
            self.assertEqual(result["outcome"]["lines_added"], 2)
            self.assertEqual(result["outcome"]["lines_deleted"], 1)

    def test_load_results_backfills_resource_usage_from_codex_events(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            (run_dir / "codex-events.jsonl").write_text(
                '{"type":"turn.completed","usage":{"input_tokens":10,'
                '"cached_input_tokens":4,"output_tokens":5,'
                '"reasoning_output_tokens":2}}\n',
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            self.assertEqual(result["input_tokens"], 10)
            self.assertEqual(result["cached_input_tokens"], 4)
            self.assertEqual(result["output_tokens"], 5)
            self.assertEqual(result["reasoning_output_tokens"], 2)
            self.assertEqual(result["resource_usage"]["total_tokens"], 15)
            self.assertIsNone(result["cost_usd"])

    def test_load_results_backfills_and_preserves_agent_harness_config(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                        "agent_name": "codex",
                        "model_name": None,
                        "cost_usd": None,
                        "agent_harness_config": {
                            "agent_harness": "codex",
                            "agent_adapter": "codex_cli",
                            "runtime_accountability": {
                                "account": None,
                                "future_runtime_fact": None,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            harness_config = result["agent_harness_config"]
            self.assertEqual(harness_config["agent_harness"], "codex")
            self.assertEqual(harness_config["agent_adapter"], "codex_cli")
            self.assertIsNone(harness_config["model_name"])
            runtime_accountability = harness_config["runtime_accountability"]
            self.assertIsNone(runtime_accountability["account"])
            self.assertIsNone(runtime_accountability["billing_context"])
            self.assertIsNone(runtime_accountability["cost_usd"])
            self.assertIsNone(runtime_accountability["future_runtime_fact"])

    def test_load_results_backfills_model_identity_from_claude_events(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            (run_dir / "claude-events.jsonl").write_text(
                (
                    MODEL_IDENTITY_FIXTURES
                    / "claude"
                    / "system-init-assistant-result.jsonl"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                        "agent_name": "claude",
                        "model_name": None,
                        "agent_harness_config": {
                            "agent_harness": "claude_code",
                            "agent_adapter": "claude_code_cli",
                            "model_name": None,
                            "model_source": "unknown",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            self.assertEqual(result["model_name"], "claude-sonnet-4-6")
            self.assertEqual(
                result["agent_harness_config"]["model_name"],
                "claude-sonnet-4-6",
            )
            self.assertEqual(result["agent_harness_config"]["model_source"], "events")

    def test_load_results_does_not_infer_model_from_codex_usage_only_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            (run_dir / "codex-events.jsonl").write_text(
                (
                    MODEL_IDENTITY_FIXTURES
                    / "codex"
                    / "thread-turn-usage-only.jsonl"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                        "agent_name": "codex",
                        "model_name": "gpt-requested",
                        "agent_harness_config": {
                            "agent_harness": "codex",
                            "agent_adapter": "codex_cli",
                            "model_name": "gpt-requested",
                            "model_source": "explicit",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            self.assertEqual(result["model_name"], "gpt-requested")
            harness_config = result["agent_harness_config"]
            self.assertEqual(harness_config["model_name"], "gpt-requested")
            self.assertEqual(harness_config["model_source"], "explicit")
            self.assertEqual(harness_config["requested_model_name"], "gpt-requested")

    def test_load_results_backfills_codex_event_model_over_requested_model(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-1"
            run_dir.mkdir()
            (run_dir / "codex-events.jsonl").write_text(
                '{"type":"turn.completed","model":"gpt-actual",'
                '"usage":{"input_tokens":1,"output_tokens":2}}\n',
                encoding="utf-8",
            )
            result_path = run_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "trial_kind": "agent_trial",
                        "run_dir": str(run_dir),
                        "agent_name": "codex",
                        "model_name": "gpt-requested",
                        "agent_harness_config": {
                            "agent_harness": "codex",
                            "agent_adapter": "codex_cli",
                            "model_name": "gpt-requested",
                            "model_source": "explicit",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = load_results([result_path])[0]

            self.assertEqual(result["model_name"], "gpt-actual")
            harness_config = result["agent_harness_config"]
            self.assertEqual(harness_config["model_name"], "gpt-actual")
            self.assertEqual(harness_config["model_source"], "events")
            self.assertEqual(harness_config["requested_model_name"], "gpt-requested")

    def _write_result(
        self,
        run_dir: Path,
        trial_id: str,
        success: bool,
        trial_kind: str = "agent_trial",
    ) -> None:
        result = {
            "trial_kind": trial_kind,
            "trial_id": trial_id,
            "run_id": trial_id,
            "task_id": "task-a",
            "eval_suite": "starter",
            "eval_type": "capability",
            "agent_name": "codex",
            "model_name": "model-a",
            "status": "passed" if success else "failed",
            "success": success,
            "duration_ms": 100 if success else 999,
            "files_changed": ["app.py"],
            "lines_added": 5 if success else 50,
            "lines_deleted": 1 if success else 10,
            "report_path": str(run_dir / "report.md"),
            "transcript_path": str(run_dir / "transcript.md"),
            "diff_path": str(run_dir / "diff.patch"),
            "run_dir": str(run_dir),
        }
        (run_dir / "result.json").write_text(
            json.dumps(result),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
