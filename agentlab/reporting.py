from __future__ import annotations

from typing import TYPE_CHECKING

from agentlab.scoring import CheckResult

if TYPE_CHECKING:
    from agentlab.runner import EvaluationRun


def render_markdown_report(run: "EvaluationRun") -> str:
    status = "passed" if run.score.tests_passed else "failed"
    lines = [
        f"# Evaluation Report: {run.task.id}",
        "",
        f"- Agent: `{run.agent_run.agent_name}`",
        f"- Status: `{status}`",
        f"- Files changed: `{len(run.agent_run.files_changed)}`",
        f"- Transcript: `{run.agent_run.transcript_path.name}`",
        f"- Diff: `{run.agent_run.diff_path.name}`",
        "",
        "## Checks",
        "",
    ]

    if not run.score.checks:
        lines.append("No checks were configured.")
    else:
        lines.extend(
            _render_check(command_index, check)
            for command_index, check in enumerate(run.score.checks, 1)
        )

    lines.extend(
        [
            "",
            "## Changed Files",
            "",
        ]
    )

    if run.agent_run.files_changed:
        lines.extend(f"- `{path}`" for path in run.agent_run.files_changed)
    else:
        lines.append("No files changed.")

    lines.append("")
    return "\n".join(lines)


def _render_check(index: int, check: CheckResult) -> str:
    passed = "passed" if check.passed else "failed"
    lines = [f"{index}. `{check.command}`: {passed} ({check.returncode})"]
    output = _trim_output(check.stderr or check.stdout)
    if output:
        lines.extend(["", "```text", output, "```", ""])
    return "\n".join(lines)


def _trim_output(output: str, max_chars: int = 2000) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[-max_chars:]
