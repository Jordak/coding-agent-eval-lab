import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentlab.agents.process_execution import (
    AgentProcessRequest,
    run_agent_process,
)


class AgentProcessExecutionTest(unittest.TestCase):
    def test_runs_process_with_cwd_env_and_persists_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            workspace = temp_path / "workspace"
            workspace.mkdir()
            events_path = temp_path / "events.jsonl"
            fake_agent = temp_path / "fake-agent"
            fake_agent.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$PWD\"\n"
                "printf '%s\\n' \"$AGENTLAB_TEST_SENTINEL\"\n",
                encoding="utf-8",
            )
            fake_agent.chmod(0o755)

            completed = run_agent_process(
                AgentProcessRequest(
                    command=[str(fake_agent), "--unused"],
                    executable_name=str(fake_agent),
                    timeout_seconds=5,
                    stdout_path=events_path,
                    progress_label="Agent",
                    show_progress=False,
                    cwd=workspace,
                    env={"AGENTLAB_TEST_SENTINEL": "from-env"},
                )
            )

            self.assertEqual(completed.returncode, 0)
            cwd_line, env_line = events_path.read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(Path(cwd_line).resolve(), workspace.resolve())
            self.assertEqual(env_line, "from-env")

    def test_progress_and_stderr_are_captured_on_success(self):
        calls = []

        class FakeProgressBar:
            def __init__(
                self,
                label,
                *,
                enabled=None,
                interval_seconds=0.5,
            ):
                self.interval_seconds = interval_seconds
                calls.append(("init", label, enabled, interval_seconds))

            def update(self, message):
                calls.append(("update", message))

            def finish(self, message):
                calls.append(("finish", message))

            def clear(self):
                calls.append(("clear",))

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            events_path = temp_path / "events.jsonl"
            fake_agent = temp_path / "fake-agent"
            fake_agent.write_text(
                f"#!{sys.executable}\n"
                "import sys\n"
                "import time\n"
                "sys.stdout.write('event\\n')\n"
                "sys.stderr.write('diagnostic\\n')\n"
                "sys.stdout.flush()\n"
                "sys.stderr.flush()\n"
                "time.sleep(0.1)\n",
                encoding="utf-8",
            )
            fake_agent.chmod(0o755)

            with patch(
                "agentlab.agents.process_execution.ProgressBar",
                FakeProgressBar,
            ):
                completed = run_agent_process(
                    AgentProcessRequest(
                        command=[str(fake_agent)],
                        executable_name=str(fake_agent),
                        timeout_seconds=2,
                        stdout_path=events_path,
                        progress_label="Agent",
                        show_progress=True,
                        progress_interval_seconds=0.02,
                    )
                )

            self.assertEqual(completed.stdout, "event\n")
            self.assertEqual(completed.stderr, "diagnostic\n")
            self.assertEqual(events_path.read_text(encoding="utf-8"), "event\n")
            self.assertEqual(calls[0], ("init", "Agent", True, 0.02))
            self.assertIn(("update", "starting agent process"), calls)
            self.assertIn(("update", "waiting for agent response"), calls)
            self.assertIn(("finish", "agent process finished"), calls)

    def test_timeout_kills_process_and_persists_partial_stdout(self):
        calls = []

        class FakeProgressBar:
            def __init__(
                self,
                label,
                *,
                enabled=None,
                interval_seconds=0.5,
            ):
                self.interval_seconds = interval_seconds
                calls.append(("init", label, enabled, interval_seconds))

            def update(self, message):
                calls.append(("update", message))

            def finish(self, message):
                calls.append(("finish", message))

            def clear(self):
                calls.append(("clear",))

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            events_path = temp_path / "events.jsonl"
            slow_agent = temp_path / "slow-agent"
            slow_agent.write_text(
                f"#!{sys.executable}\n"
                "import sys\n"
                "import time\n"
                "sys.stdout.write('partial\\n')\n"
                "sys.stderr.write('timeout diagnostic\\n')\n"
                "sys.stdout.flush()\n"
                "sys.stderr.flush()\n"
                "time.sleep(3)\n",
                encoding="utf-8",
            )
            slow_agent.chmod(0o755)

            with patch(
                "agentlab.agents.process_execution.ProgressBar",
                FakeProgressBar,
            ):
                with self.assertRaises(subprocess.TimeoutExpired) as raised:
                    run_agent_process(
                        AgentProcessRequest(
                            command=[str(slow_agent)],
                            executable_name=str(slow_agent),
                            timeout_seconds=1.0,
                            stdout_path=events_path,
                            progress_label="Agent",
                            show_progress=True,
                            progress_interval_seconds=0.05,
                        )
                    )

            self.assertEqual(
                events_path.read_text(encoding="utf-8"),
                "partial\n",
            )
            self.assertEqual(raised.exception.stderr, "timeout diagnostic\n")
            self.assertIn(("update", "starting agent process"), calls)
            self.assertIn(("update", "waiting for agent response"), calls)
            self.assertIn(("finish", "agent process timed out"), calls)


if __name__ == "__main__":
    unittest.main()
