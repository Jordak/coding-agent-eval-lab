import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_timeout_kills_process_and_persists_partial_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            events_path = temp_path / "events.jsonl"
            slow_agent = temp_path / "slow-agent"
            slow_agent.write_text(
                f"#!{sys.executable}\n"
                "import sys\n"
                "import time\n"
                "sys.stdout.write('partial\\n')\n"
                "sys.stdout.flush()\n"
                "time.sleep(3)\n",
                encoding="utf-8",
            )
            slow_agent.chmod(0o755)

            with self.assertRaises(subprocess.TimeoutExpired):
                run_agent_process(
                    AgentProcessRequest(
                        command=[str(slow_agent)],
                        executable_name=str(slow_agent),
                        timeout_seconds=1.0,
                        stdout_path=events_path,
                        progress_label="Agent",
                        show_progress=False,
                        progress_interval_seconds=0.05,
                    )
                )

            self.assertEqual(
                events_path.read_text(encoding="utf-8"),
                "partial\n",
            )


if __name__ == "__main__":
    unittest.main()
