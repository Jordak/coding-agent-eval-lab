from __future__ import annotations

import json
from typing import TYPE_CHECKING

from agentlab.execution.scoring import CheckResult
from agentlab.runtime.run_surface import normalize_run_surface
from agentlab.tasks.boundaries import scope_oracle_metadata

if TYPE_CHECKING:
    from agentlab.tasks.reference import ReferenceVerification
    from agentlab.execution.runner import EvaluationRun


def render_markdown_report(run: "EvaluationRun") -> str:
    status = "passed" if run.score.tests_passed else "failed"
    setup_untracked_caveat_paths = _setup_created_untracked_changed_paths(
        run.agent_run
    )
    lines = [
        f"# Evaluation Trial Report: {run.task.id}",
        "",
        f"- Trial: `{run.run_dir.name}`",
        f"- Evaluation suite: `{run.task.suite}`",
        f"- Evaluation type: `{run.task.eval_type}`",
        f"- Task repository: `{run.task.repo}`",
        f"- Task commit: `{run.task.commit}`",
        f"- Agent harness: `{run.agent_run.agent_name}`",
        f"- Status: `{status}`",
        f"- Outcome: `{status}`",
        f"- Files changed: `{len(run.agent_run.files_changed)}`",
        f"- Lines added: {_patch_stat(run.agent_run.lines_added, setup_untracked_caveat_paths)}",
        f"- Lines deleted: {_patch_stat(run.agent_run.lines_deleted, setup_untracked_caveat_paths)}",
        f"- Transcript/trace: `{run.agent_run.transcript_path.name}`",
        f"- Diff: `{run.agent_run.diff_path.name}`",
    ]
    lines.extend(_patch_size_caveat_lines(setup_untracked_caveat_paths))

    agent_harness_config = getattr(run.agent_run, "agent_harness_config", {})
    run_surface = normalize_run_surface(
        _workspace_run_surface(run),
        agent_harness_config=agent_harness_config,
        agent_name=run.agent_run.agent_name,
        status=status,
        success=run.score.tests_passed,
        error=run.agent_run.error,
    )
    surface_lines = _render_run_surface(run_surface)
    if surface_lines:
        lines.extend(["", "## Run Surface", ""])
        lines.extend(surface_lines)

    config_lines = _render_agent_harness_config(agent_harness_config)
    if config_lines:
        lines.extend(["", "## Agent Harness Configuration", ""])
        lines.extend(config_lines)

    scope_oracle_lines = _render_scope_oracle_metadata(run.task)
    if scope_oracle_lines:
        lines.extend(["", "## Scope Oracle Metadata", ""])
        lines.extend(scope_oracle_lines)

    lines.extend(["", "## Code-Based Graders", ""])

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
            "## Resource Usage",
            "",
            f"- Duration ms: `{run.agent_run.duration_ms}`",
            f"- Input tokens: `{_display_optional(run.agent_run.input_tokens)}`",
            (
                "- Cached input tokens: "
                f"`{_display_optional(run.agent_run.cached_input_tokens)}`"
            ),
            f"- Output tokens: `{_display_optional(run.agent_run.output_tokens)}`",
            (
                "- Reasoning output tokens: "
                f"`{_display_optional(run.agent_run.reasoning_output_tokens)}`"
            ),
            f"- Cost USD: `{_display_optional(run.agent_run.cost_usd)}`",
        ]
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


def render_reference_report(verification: "ReferenceVerification") -> str:
    status = "passed" if verification.success else "failed"
    setup_untracked_caveat_paths = _setup_created_untracked_changed_paths(
        verification
    )
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
        f"- Task repository: `{verification.task.repo}`",
        f"- Task commit: `{verification.task.commit}`",
        f"- Reference artifact: {artifact_summary}",
        f"- Status: `{status}`",
        f"- Outcome: `{status}`",
        f"- Files changed: `{len(verification.files_changed)}`",
        f"- Lines added: {_patch_stat(verification.lines_added, setup_untracked_caveat_paths)}",
        f"- Lines deleted: {_patch_stat(verification.lines_deleted, setup_untracked_caveat_paths)}",
    ]
    lines.extend(_patch_size_caveat_lines(setup_untracked_caveat_paths))
    lines.extend(
        [
            "",
            "## Run Surface",
            "",
            *_render_run_surface(
                normalize_run_surface(
                    _workspace_run_surface(verification),
                    agent_name="reference",
                    status=status,
                    success=verification.success,
                    error=None,
                )
            ),
        ]
    )

    scope_oracle_lines = _render_scope_oracle_metadata(verification.task)
    if scope_oracle_lines:
        lines.extend(["", "## Scope Oracle Metadata", ""])
        lines.extend(scope_oracle_lines)

    lines.extend(["", "## Code-Based Graders", ""])

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


def _render_scope_oracle_metadata(task: object) -> list[str]:
    success = getattr(task, "success", None)
    consent_style = getattr(task, "consent_style", None)
    allowed_paths = getattr(success, "allowed_paths", None)
    forbidden_paths = getattr(success, "forbidden_paths", [])
    metadata = scope_oracle_metadata(
        consent_style=consent_style,
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
    )
    if not metadata:
        return []
    lines: list[str] = []
    if consent_style is not None:
        lines.append(f"- Consent style: `{consent_style}`")
    if allowed_paths is not None:
        lines.append(
            "- Allowed paths: "
            + ", ".join(f"`{path}`" for path in allowed_paths)
        )
    if forbidden_paths:
        lines.append(
            "- Forbidden paths: "
            + ", ".join(f"`{path}`" for path in forbidden_paths)
        )
    return lines


def _patch_stat(value: int, caveat_paths: list[str]) -> str:
    suffix = "*" if caveat_paths else ""
    return f"`{value}`{suffix}"


def _patch_size_caveat_lines(caveat_paths: list[str]) -> list[str]:
    if not caveat_paths:
        return []
    return [
        "",
        (
            "Patch size metrics marked with `*` include setup-created "
            "untracked path changes; line counts may not fully represent "
            f"{_inline_code_list(caveat_paths)}."
        ),
    ]


def _setup_created_untracked_changed_paths(value: object) -> list[str]:
    paths = getattr(value, "setup_created_untracked_changed_paths", [])
    return [str(path) for path in paths]


def _inline_code_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def _trim_output(output: str, max_chars: int = 2000) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[-max_chars:]


def _display_optional(value: object) -> str:
    if value is None:
        return "unknown"
    return str(value)


def _render_agent_harness_config(config: object) -> list[str]:
    if not isinstance(config, dict) or not config:
        return []
    runtime_accountability = config.get("runtime_accountability")
    if not isinstance(runtime_accountability, dict):
        runtime_accountability = {}

    fields = [
        ("Agent adapter", config.get("agent_adapter")),
        ("Command", config.get("command")),
        ("Command identity", config.get("command_identity")),
        ("Model", config.get("model_name")),
        ("Model source", config.get("model_source")),
        ("Requested model", config.get("requested_model_name")),
        ("Reasoning effort", config.get("reasoning_effort")),
        ("Model provider", config.get("model_provider")),
        ("Codex thread", config.get("codex_thread_id")),
        ("Codex thread source", config.get("codex_thread_source")),
        ("Profile", config.get("profile")),
        ("Sandbox", config.get("sandbox")),
        ("Approval policy", config.get("approval_policy")),
        ("Permission mode", config.get("permission_mode")),
        ("Output format", config.get("output_format")),
        ("Max turns", config.get("max_turns")),
        ("Allowed tools", config.get("allowed_tools")),
        ("Disallowed tools", config.get("disallowed_tools")),
        ("No session persistence", config.get("no_session_persistence")),
        ("Timeout seconds", config.get("timeout_seconds")),
        ("CLI version", config.get("cli_version")),
        ("Auth status", config.get("auth_status")),
        ("Account", runtime_accountability.get("account")),
        ("Billing context", runtime_accountability.get("billing_context")),
    ]
    return [
        f"- {label}: `{_display_optional(value)}`"
        for label, value in fields
    ]


def _render_run_surface(run_surface: object) -> list[str]:
    if not isinstance(run_surface, dict) or not run_surface:
        return []

    fields = [
        ("Execution surface", run_surface.get("execution_surface")),
        ("Runtime version", run_surface.get("runtime_version")),
        ("Model identity source", run_surface.get("model_identity_source")),
        ("Sandbox mode", run_surface.get("sandbox_mode")),
        ("Approval policy", run_surface.get("approval_policy")),
        ("Tool policy", run_surface.get("tool_policy")),
        ("Memory scope", run_surface.get("memory_scope")),
        ("Network policy", run_surface.get("network_policy")),
        ("Timeout seconds", run_surface.get("timeout_seconds")),
        ("Turn or step budget", run_surface.get("turn_or_step_budget")),
        ("Stop reason", run_surface.get("stop_reason")),
        (
            "Human intervention events",
            run_surface.get("human_intervention_events"),
        ),
        (
            "Workspace history policy",
            run_surface.get("workspace_history_policy"),
        ),
        ("Workspace base ref", run_surface.get("workspace_base_ref")),
    ]
    return [
        f"- {label}: `{_display_run_surface_value(value)}`"
        for label, value in fields
    ]


def _display_run_surface_value(value: object) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, list):
        if not value:
            return "none"
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _workspace_run_surface(source: object) -> dict[str, object]:
    return {
        "workspace_history_policy": getattr(
            source,
            "workspace_history_policy",
            None,
        ),
        "workspace_base_ref": getattr(source, "workspace_base_ref", None),
    }
