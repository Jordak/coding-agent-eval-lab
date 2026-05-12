from __future__ import annotations

import argparse
from typing import Callable, Sequence

from agentlab.agents.claude_code import ClaudeCodeAdapter, ClaudeCodeConfig
from agentlab.agents.codex_cli import CodexCliAdapter, CodexCliConfig
from agentlab.agents.manual import ManualAgentAdapter


AGENT_CHOICES = ("manual", "codex", "claude")
PREFLIGHT_AGENT_CHOICES = ("codex", "claude")


def add_agent_argument(
    parser: argparse.ArgumentParser,
    *,
    default: str,
    choices: Sequence[str],
    help: str,
) -> None:
    parser.add_argument(
        "--agent",
        default=default,
        choices=list(choices),
        help=help,
    )


def add_agent_adapter_options(
    parser: argparse.ArgumentParser,
    *,
    codex_timeout_default: int,
    codex_timeout_help: str = "Maximum wall time for `codex exec`.",
    claude_timeout_default: int,
) -> None:
    add_codex_options(
        parser,
        timeout_default=codex_timeout_default,
        timeout_help=codex_timeout_help,
    )
    add_claude_options(parser, timeout_default=claude_timeout_default)


def add_codex_options(
    parser: argparse.ArgumentParser,
    *,
    timeout_default: int,
    timeout_help: str,
) -> None:
    parser.add_argument(
        "--codex-command",
        default="codex",
        help="Codex CLI executable to use when --agent codex.",
    )
    parser.add_argument(
        "--codex-model",
        default=None,
        help="Optional model passed to `codex exec --model`.",
    )
    parser.add_argument(
        "--codex-profile",
        default=None,
        help="Optional profile passed to `codex exec --profile`.",
    )
    parser.add_argument(
        "--codex-sandbox",
        default="workspace-write",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode passed to `codex exec --sandbox`.",
    )
    parser.add_argument(
        "--codex-approval",
        default="never",
        choices=["untrusted", "on-failure", "on-request", "never"],
        help="Approval policy passed to `codex exec --ask-for-approval`.",
    )
    parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=timeout_default,
        help=timeout_help,
    )


def add_claude_options(
    parser: argparse.ArgumentParser,
    *,
    timeout_default: int,
) -> None:
    parser.add_argument(
        "--claude-command",
        default="claude",
        help="Claude Code CLI executable to use when --agent claude.",
    )
    parser.add_argument(
        "--claude-model",
        default=None,
        help="Optional model passed to `claude --model`.",
    )
    parser.add_argument(
        "--claude-permission-mode",
        default="acceptEdits",
        choices=[
            "default",
            "acceptEdits",
            "plan",
            "auto",
            "dontAsk",
            "bypassPermissions",
        ],
        help="Permission mode passed to Claude Code.",
    )
    parser.add_argument(
        "--claude-output-format",
        default="stream-json",
        choices=["text", "json", "stream-json"],
        help="Print-mode output format passed to Claude Code.",
    )
    parser.add_argument(
        "--claude-max-turns",
        type=int,
        default=None,
        help="Optional maximum agentic turns for Claude Code print mode.",
    )
    parser.add_argument(
        "--claude-allowed-tool",
        action="append",
        default=[],
        help=(
            "Tool permission rule passed as `--allowedTools`. Can be repeated, "
            "for example `Read` or `Bash(pytest *)`."
        ),
    )
    parser.add_argument(
        "--claude-disallowed-tool",
        action="append",
        default=[],
        help=(
            "Tool permission rule passed as `--disallowedTools`. Can be "
            "repeated, for example `Bash(git push *)`."
        ),
    )
    parser.add_argument(
        "--claude-timeout-seconds",
        type=int,
        default=timeout_default,
        help="Maximum wall time for `claude -p`.",
    )
    parser.add_argument(
        "--claude-session-persistence",
        action="store_true",
        help=(
            "Allow Claude Code to persist its local session. By default "
            "agentlab passes `--no-session-persistence` for isolated trials."
        ),
    )


_add_claude_options = add_claude_options


def _build_agent(args: argparse.Namespace, show_progress: bool = True) -> object:
    if args.agent == "manual":
        return ManualAgentAdapter(pause=not args.no_pause)
    if args.agent == "codex":
        return CodexCliAdapter(_codex_config_from_args(args, show_progress))
    if args.agent == "claude":
        return ClaudeCodeAdapter(_claude_code_config_from_args(args, show_progress))
    raise RuntimeError(f"unknown agent: {args.agent}")


def _codex_config_from_args(
    args: argparse.Namespace,
    show_progress: bool = True,
) -> CodexCliConfig:
    return CodexCliConfig(
        command=args.codex_command,
        model=args.codex_model,
        profile=args.codex_profile,
        sandbox=args.codex_sandbox,
        approval_policy=args.codex_approval,
        timeout_seconds=args.codex_timeout_seconds,
        show_progress=show_progress,
    )


def _claude_code_config_from_args(
    args: argparse.Namespace,
    show_progress: bool = True,
) -> ClaudeCodeConfig:
    return ClaudeCodeConfig(
        command=args.claude_command,
        model=args.claude_model,
        permission_mode=args.claude_permission_mode,
        output_format=args.claude_output_format,
        max_turns=args.claude_max_turns,
        allowed_tools=tuple(args.claude_allowed_tool),
        disallowed_tools=tuple(args.claude_disallowed_tool),
        timeout_seconds=args.claude_timeout_seconds,
        show_progress=show_progress,
        no_session_persistence=not args.claude_session_persistence,
    )


def _agent_factory(args: argparse.Namespace) -> Callable[[bool], object]:
    def build(show_progress: bool) -> object:
        return _build_agent(args, show_progress=show_progress)

    return build
