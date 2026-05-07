from __future__ import annotations

from typing import TYPE_CHECKING

from agentlab.scoring import CheckResult

if TYPE_CHECKING:
    from agentlab.reference import ReferenceVerification
    from agentlab.runner import EvaluationRun


def render_markdown_report(run: "EvaluationRun") -> str:
    status = "passed" if run.score.tests_passed else "failed"
    lines = [
        f"# Evaluation Trial Report: {run.task.id}",
        "",
        f"- Trial: `{run.run_dir.name}`",
        f"- Evaluation suite: `{run.task.suite}`",
        f"- Evaluation type: `{run.task.eval_type}`",
        f"- Agent harness: `{run.agent_run.agent_name}`",
        f"- Status: `{status}`",
        f"- Outcome: `{status}`",
        f"- Files changed: `{len(run.agent_run.files_changed)}`",
        f"- Transcript/trace: `{run.agent_run.transcript_path.name}`",
        f"- Diff: `{run.agent_run.diff_path.name}`",
        "",
        "## Code-Based Graders",
        "",
    ]

    if not run.score.checks:
        lines.append("No code-based graders were configured.")
    else:
        lines.extend(
            _render_check(command_index, check)
            for command_index, check in enumerate(run.score.checks, 1)
        )

    if run.score.notes:
        lines.extend(["", "## Grader Notes", ""])
        lines.extend(f"- {note}" for note in run.score.notes)

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


def render_reference_report(verification: "ReferenceVerification") -> str:
    status = "passed" if verification.success else "failed"
    artifact = verification.task.reference_artifact
    artifact_summary = "not configured"
    if artifact is not None and artifact.type == "patch":
        artifact_summary = f"patch `{artifact.path}`"
    elif artifact is not None and artifact.type == "commit":
        artifact_summary = f"commit `{artifact.commit}`"

    lines = [
        f"# Reference Verification Report: {verification.task.id}",
        "",
        "- Trial kind: `reference_verification`",
        "- Agent harness: `reference`",
        f"- Evaluation suite: `{verification.task.suite}`",
        f"- Evaluation type: `{verification.task.eval_type}`",
        f"- Reference artifact: {artifact_summary}",
        f"- Status: `{status}`",
        f"- Outcome: `{status}`",
        f"- Files changed: `{len(verification.files_changed)}`",
        "",
        "## Code-Based Graders",
        "",
    ]

    checks = verification.all_checks
    if not checks:
        lines.append("No code-based graders were configured.")
    else:
        lines.extend(
            _render_check(command_index, check)
            for command_index, check in enumerate(checks, 1)
        )

    if verification.notes:
        lines.extend(["", "## Grader Notes", ""])
        lines.extend(f"- {note}" for note in verification.notes)

    lines.extend(["", "## Changed Files", ""])
    if verification.files_changed:
        lines.extend(f"- `{path}`" for path in verification.files_changed)
    else:
        lines.append("No files changed.")

    lines.append("")
    return "\n".join(lines)


def _render_check(index: int, check: CheckResult) -> str:
    passed = "passed" if check.passed else "failed"
    lines = [
        f"{index}. Assertion `{check.command}`: {passed} ({check.returncode})"
    ]
    output = _trim_output(check.stderr or check.stdout)
    if output:
        lines.extend(["", "```text", output, "```", ""])
    return "\n".join(lines)


def _trim_output(output: str, max_chars: int = 2000) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[-max_chars:]
