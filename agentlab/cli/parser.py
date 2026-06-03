from __future__ import annotations

import argparse

from agentlab.cli.doctor import add_doctor_command
from agentlab.cli.recover import add_recover_command
from agentlab.cli.reports import add_report_commands
from agentlab.cli.review import add_review_command
from agentlab.cli.review_proposals import add_review_proposal_commands
from agentlab.cli.run import add_run_command
from agentlab.cli.task import add_task_commands
from agentlab.cli.trials import add_trial_commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentlab",
        description="Evaluate coding agents on reproducible software tasks.",
    )
    subcommands = parser.add_subparsers(dest="command")

    add_task_commands(subcommands)
    add_doctor_command(subcommands)
    add_run_command(subcommands)
    add_trial_commands(subcommands)
    add_report_commands(subcommands)
    add_review_command(subcommands)
    add_review_proposal_commands(subcommands)
    add_recover_command(subcommands)

    return parser
