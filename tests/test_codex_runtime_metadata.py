import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from agentlab.runtime.codex_metadata import (
    LOCAL_CODEX_STATE_SOURCE,
    codex_model_identity_from_events_and_state,
    parse_codex_thread_id_from_events,
    recover_codex_runtime_metadata,
)


class CodexRuntimeMetadataTest(unittest.TestCase):
    def test_parses_thread_started_thread_id(self):
        thread_id = parse_codex_thread_id_from_events(
            "not json\n"
            '{"type":"turn.started"}\n'
            '{"type":"thread.started","thread_id":"thread-1"}\n'
        )

        self.assertEqual(thread_id, "thread-1")

    def test_recovers_model_identity_from_local_codex_state(self):
        with tempfile.TemporaryDirectory() as temp:
            state_db = Path(temp) / "state.sqlite"
            self._write_state_db(state_db, thread_id="thread-1", model="gpt-5.5")

            identity = codex_model_identity_from_events_and_state(
                '{"type":"thread.started","thread_id":"thread-1"}\n'
                '{"type":"turn.completed","usage":{}}\n',
                requested_model_name=None,
                codex_state_db=state_db,
            )

        self.assertEqual(identity.model_name, "gpt-5.5")
        self.assertEqual(identity.model_source, LOCAL_CODEX_STATE_SOURCE)
        self.assertEqual(identity.reasoning_effort, "xhigh")
        self.assertEqual(identity.model_provider, "openai")
        self.assertEqual(identity.codex_thread_id, "thread-1")
        self.assertEqual(identity.codex_thread_source, "exec")
        self.assertEqual(identity.cli_version, "0.130.0-alpha.5")

    def test_event_model_takes_priority_over_local_codex_state(self):
        with tempfile.TemporaryDirectory() as temp:
            state_db = Path(temp) / "state.sqlite"
            self._write_state_db(state_db, thread_id="thread-1", model="gpt-local")

            identity = codex_model_identity_from_events_and_state(
                '{"type":"thread.started","thread_id":"thread-1"}\n'
                '{"type":"turn.completed","model":"gpt-event"}\n',
                requested_model_name="gpt-requested",
                codex_state_db=state_db,
            )

        self.assertEqual(identity.model_name, "gpt-event")
        self.assertEqual(identity.model_source, "events")
        self.assertEqual(identity.requested_model_name, "gpt-requested")
        self.assertEqual(identity.codex_thread_id, "thread-1")

    def test_recovery_dry_run_reports_changes_without_writing_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_db = root / "state.sqlite"
            self._write_state_db(state_db, thread_id="thread-1", model="gpt-5.5")
            result_path = self._write_run(root, thread_id="thread-1")
            before = result_path.read_text(encoding="utf-8")

            summary = recover_codex_runtime_metadata(
                [result_path],
                codex_state_db=state_db,
                apply=False,
            )

            self.assertEqual(result_path.read_text(encoding="utf-8"), before)

        self.assertEqual(len(summary.entries), 1)
        entry = summary.entries[0]
        self.assertEqual(entry.status, "would_update")
        self.assertTrue(entry.changed)
        self.assertEqual(entry.thread_id, "thread-1")
        self.assertEqual(entry.model_name, "gpt-5.5")

    def test_recovery_apply_writes_result_json_and_config_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_db = root / "state.sqlite"
            self._write_state_db(state_db, thread_id="thread-1", model="gpt-5.5")
            result_path = self._write_run(root, thread_id="thread-1")

            summary = recover_codex_runtime_metadata(
                [result_path],
                codex_state_db=state_db,
                apply=True,
            )

            result = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(summary.entries[0].status, "updated")
        self.assertEqual(result["model_name"], "gpt-5.5")
        config = result["agent_harness_config"]
        self.assertEqual(config["model_name"], "gpt-5.5")
        self.assertEqual(config["model_source"], LOCAL_CODEX_STATE_SOURCE)
        self.assertEqual(config["codex_thread_id"], "thread-1")
        self.assertEqual(config["reasoning_effort"], "xhigh")
        self.assertEqual(config["model_provider"], "openai")
        self.assertEqual(config["codex_thread_source"], "exec")
        self.assertEqual(config["cli_version"], "0.130.0-alpha.5")

    def _write_run(self, root: Path, *, thread_id: str) -> Path:
        run_dir = root / "runs" / "trial-1"
        run_dir.mkdir(parents=True)
        (run_dir / "codex-events.jsonl").write_text(
            f'{{"type":"thread.started","thread_id":"{thread_id}"}}\n'
            '{"type":"turn.completed","usage":{}}\n',
            encoding="utf-8",
        )
        result_path = run_dir / "result.json"
        result_path.write_text(
            json.dumps(
                {
                    "trial_kind": "agent_trial",
                    "trial_id": "trial-1",
                    "run_id": "trial-1",
                    "run_dir": str(run_dir),
                    "agent_name": "codex",
                    "model_name": None,
                    "agent_harness_config": {
                        "agent_harness": "codex",
                        "agent_adapter": "codex_cli",
                        "model_name": None,
                        "model_source": "unknown",
                    },
                }
            ),
            encoding="utf-8",
        )
        return result_path

    def _write_state_db(
        self,
        path: Path,
        *,
        thread_id: str,
        model: str,
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                create table threads (
                  id text primary key,
                  model text,
                  reasoning_effort text,
                  model_provider text,
                  source text,
                  cli_version text
                )
                """
            )
            connection.execute(
                """
                insert into threads (
                  id,
                  model,
                  reasoning_effort,
                  model_provider,
                  source,
                  cli_version
                ) values (?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    model,
                    "xhigh",
                    "openai",
                    "exec",
                    "0.130.0-alpha.5",
                ),
            )


if __name__ == "__main__":
    unittest.main()
