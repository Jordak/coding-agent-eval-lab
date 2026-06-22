from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from agentlab.tasks.environment import describe_task_environment
from agentlab.tasks import EvalTask, TaskBundle
from agentlab.tasks.boundaries import scope_oracle_metadata


def publish_task_cards(
    paths: Iterable[str],
    *,
    check: bool = False,
):
    from agentlab.tasks.integrity import publish_task_cards as publish

    return publish(paths, check=check)


def render_task_card(bundle: TaskBundle) -> str:
    task = bundle.task
    scope_oracle_section = _scope_oracle_section(task)
    lines = [
        f"# {task.title}",
        "",
        f"- Task ID: `{task.id}`",
        f"- Suite: `{task.suite}`",
        f"- Evaluation type: `{task.eval_type}`",
        f"- Language: `{task.language}`",
        f"- Repository: `{task.repo}`",
        f"- Commit: `{task.commit}`",
        f"- Source: `{bundle.task_file.name}`",
        "",
        "## Prompt",
        "",
        task.prompt,
        "",
        "## Reference",
        "",
        task.reference_solution or "No prose reference solution configured.",
        "",
        "## Reference Artifact",
        "",
        _reference_artifact_text(task, bundle.bundle_dir),
        "",
        "## Environment",
        "",
        _environment_text(task),
        "",
        *_visible_validation_section(task),
        "## Graders",
        "",
        "### Setup",
        "",
        _command_list(task.setup),
        "",
        "### Baseline",
        "",
        _command_list(task.baseline),
        "",
        "### Target",
        "",
        _command_list(task.test),
        "",
        "## Success Criteria",
        "",
        f"- Tests must pass: `{str(task.success.tests_must_pass).lower()}`",
        f"- Max files changed: `{task.success.max_files_changed if task.success.max_files_changed is not None else 'not set'}`",
        *(scope_oracle_section + [""] if scope_oracle_section else [""]),
        "## Tags",
        "",
        _inline_code_list(task.tags),
        "",
        "## Expected Failure Modes",
        "",
        _inline_code_list(task.failure_modes),
        "",
        "_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._",
        "",
    ]
    return "\n".join(lines)


def _command_list(commands: List[str]) -> str:
    if not commands:
        return "None configured."
    return "\n".join(f"- `{command}`" for command in commands)


def _visible_validation_section(task: EvalTask) -> list[str]:
    if not task.visible_validation:
        return []
    return [
        "## Visible Validation",
        "",
        _command_list(task.visible_validation),
        "",
    ]


def _environment_text(task: EvalTask) -> str:
    lines = describe_task_environment(task)
    if not lines:
        return "No task-local environment configured."
    return "\n".join(f"- {line}" for line in lines)


def _inline_code_list(values: List[str]) -> str:
    if not values:
        return "None configured."
    return "\n".join(f"- `{value}`" for value in values)


def _scope_oracle_section(task: EvalTask) -> list[str]:
    metadata = scope_oracle_metadata(
        consent_style=task.consent_style,
        allowed_paths=task.success.allowed_paths,
        forbidden_paths=task.success.forbidden_paths,
    )
    if not metadata:
        return []
    lines = ["", "## Scope Oracle Metadata", ""]
    if task.consent_style is not None:
        lines.append(f"- Consent style: `{task.consent_style}`")
    if task.success.allowed_paths is not None:
        lines.append(
            "- Allowed paths: "
            + ", ".join(f"`{path}`" for path in task.success.allowed_paths)
        )
    if task.success.forbidden_paths:
        lines.append(
            "- Forbidden paths: "
            + ", ".join(f"`{path}`" for path in task.success.forbidden_paths)
        )
    return lines


def _reference_artifact_text(task: EvalTask, bundle_dir: Path) -> str:
    artifact = task.reference_artifact
    if artifact is None:
        return "No verified reference artifact configured yet."
    if artifact.type == "patch":
        exists = artifact.path is not None and (bundle_dir / artifact.path).is_file()
        status = "present" if exists else "missing"
        return "\n".join(
            [
                "- Type: `patch`",
                f"- Path: `{artifact.path}`",
                f"- Status: `{status}`",
            ]
        )
    if artifact.type == "commit":
        return "\n".join(
            [
                "- Type: `commit`",
                f"- Commit: `{artifact.commit}`",
            ]
        )
    return f"Unsupported reference artifact type: `{artifact.type}`"
