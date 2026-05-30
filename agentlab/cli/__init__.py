from __future__ import annotations

import sys
from typing import Iterable

from agentlab.cli.agent_options import (
    _agent_factory,
    _add_claude_options,
    _claude_code_config_from_args,
    _codex_config_from_args,
)
from agentlab.cli.doctor import handle_doctor
from agentlab.cli.parser import build_parser
from agentlab.cli.recover import handle_recover_codex_runtime_metadata
from agentlab.cli.reports import handle_report_capability_evidence_digest
from agentlab.cli.review import handle_review
from agentlab.cli.run import handle_run, _print_run_summaries
from agentlab.cli.task import (
    handle_task_smoke_test,
    handle_task_validate,
    handle_task_verify_reference,
)
from agentlab.cli.trials import (
    handle_runs_list,
    handle_trials_archive_excluded,
    handle_trials_summarize,
)
from agentlab.review import ReviewArtifactError


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 2

    try:
        return args.handler(args)
    except ReviewArtifactError as exc:
        print(exc.cli_message(), file=sys.stderr)
        return exc.exit_code


__all__ = [
    "_agent_factory",
    "_add_claude_options",
    "_claude_code_config_from_args",
    "_codex_config_from_args",
    "_print_run_summaries",
    "build_parser",
    "handle_doctor",
    "handle_recover_codex_runtime_metadata",
    "handle_report_capability_evidence_digest",
    "handle_review",
    "handle_run",
    "handle_runs_list",
    "handle_task_smoke_test",
    "handle_task_validate",
    "handle_task_verify_reference",
    "handle_trials_archive_excluded",
    "handle_trials_summarize",
    "main",
]
