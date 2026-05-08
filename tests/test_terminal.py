import io
import unittest
from unittest.mock import patch

from agentlab.terminal import ProgressBar, red


class _TtyStringIO(io.StringIO):
    def isatty(self):
        return True


class TerminalOutputTest(unittest.TestCase):
    def test_red_uses_ansi_color_for_tty_streams(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                red("ERROR boom", _TtyStringIO()),
                "\033[31mERROR boom\033[0m",
            )

    def test_red_omits_ansi_color_for_non_tty_streams(self):
        self.assertEqual(red("ERROR boom", io.StringIO()), "ERROR boom")

    def test_progress_bar_writes_waiting_message_for_tty_streams(self):
        stream = _TtyStringIO()
        progress = ProgressBar("Codex", stream=stream, interval_seconds=0.001)

        progress.update("waiting for agent response")

        self.assertIn("Codex [", stream.getvalue())
        self.assertIn("waiting for agent response", stream.getvalue())

    def test_progress_bar_clear_removes_current_line(self):
        stream = _TtyStringIO()
        progress = ProgressBar("Codex", stream=stream)

        progress.clear()

        self.assertTrue(stream.getvalue().startswith("\r"))
        self.assertTrue(stream.getvalue().endswith("\r"))


if __name__ == "__main__":
    unittest.main()
