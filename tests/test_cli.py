import unittest
from unittest.mock import patch

from agentlab.cli import build_parser


class CliParserTest(unittest.TestCase):
    def test_codex_command_defaults_to_environment_variable(self):
        with patch.dict(
            "os.environ",
            {"AGENTLAB_CODEX_COMMAND": "/opt/codex/bin/codex"},
        ):
            args = build_parser().parse_args(
                [
                    "run",
                    "--agent",
                    "codex",
                    "--task",
                    "tasks/starter/python-bugfix-001",
                ]
            )

        self.assertEqual(args.codex_command, "/opt/codex/bin/codex")


if __name__ == "__main__":
    unittest.main()
