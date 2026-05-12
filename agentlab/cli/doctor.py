from __future__ import annotations

import argparse
import shlex
import sys

from agentlab.agents.claude_code import run_claude_code_preflight
from agentlab.agents.codex_cli import run_codex_preflight
from agentlab.cli.agent_options import (
    PREFLIGHT_AGENT_CHOICES,
    add_agent_adapter_options,
    add_agent_argument,
    _claude_code_config_from_args,
    _codex_config_from_args,
)
from agentlab.cli.output import _trim_cli_output
from agentlab.terminal import print_error


def add_doctor_command(subcommands: argparse._SubParsersAction) -> None:
    doctor_parser = subcommands.add_parser(
        "doctor",
        help="Check local agent harness prerequisites before running trials.",
    )
    add_agent_argument(
        doctor_parser,
        default="codex",
        choices=PREFLIGHT_AGENT_CHOICES,
        help="Agent harness to check.",
    )
    add_agent_adapter_options(
        doctor_parser,
        codex_timeout_default=15,
        codex_timeout_help="Maximum wall time for each Codex preflight command.",
        claude_timeout_default=15,
    )
    doctor_parser.set_defaults(handler=handle_doctor)


def handle_doctor(args: argparse.Namespace) -> int:
    if args.agent == "codex":
        result = run_codex_preflight(
            _codex_config_from_args(args, show_progress=False),
            timeout_seconds=args.codex_timeout_seconds,
        )
    elif args.agent == "claude":
        result = run_claude_code_preflight(
            _claude_code_config_from_args(args, show_progress=False),
            timeout_seconds=args.claude_timeout_seconds,
        )
    else:
        print_error(f"unknown agent: {args.agent}")
        return 1

    _print_preflight_result(result)
    return 0 if result.passed else 1


def _print_preflight_result(result: object) -> None:
    print(f"Doctor: {result.agent_name}", flush=True)
    for check in result.checks:
        if check.passed:
            print(f"OK {check.name}: {check.message}")
            continue

        print_error(f"{check.name}: {check.message}")
        if check.command:
            print(f"  Command: {shlex.join(check.command)}", file=sys.stderr)
        output = _trim_cli_output(check.stderr or check.stdout)
        if output:
            print(output, file=sys.stderr)

    if result.passed:
        print("Preflight passed.")
    else:
        print("Preflight failed.", file=sys.stderr)
