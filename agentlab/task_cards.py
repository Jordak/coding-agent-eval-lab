from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from agentlab.environment import describe_task_environment
from agentlab.tasks import EvalTask, TaskBundle, discover_task_bundles


@dataclass(frozen=True)
class TaskCardPublicationResult:
    matched_bundles: int
    changed_paths: List[Path]


def publish_task_cards(
    paths: Iterable[str],
    *,
    check: bool = False,
    render_indexes: bool = True,
) -> TaskCardPublicationResult:
    bundles = discover_task_bundles(paths)
    changed: List[Path] = []
    bundles_by_suite: dict[Path, list[TaskBundle]] = defaultdict(list)

    for bundle in bundles:
        changed.extend(
            _write_or_check(
                bundle.task_card_path,
                render_task_card(bundle),
                check,
            )
        )
        bundles_by_suite[bundle.suite_dir].append(bundle)

    if render_indexes:
        for suite_dir, suite_bundles in sorted(bundles_by_suite.items()):
            index_path = suite_dir / "README.md"
            changed.extend(
                _write_or_check(
                    index_path,
                    render_suite_index(suite_dir, suite_bundles),
                    check,
                )
            )

    return TaskCardPublicationResult(
        matched_bundles=len(bundles),
        changed_paths=changed,
    )


def render_task_card(bundle: TaskBundle) -> str:
    task = bundle.task
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
        "",
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


def render_suite_index(
    suite_dir: Path,
    bundles: list[TaskBundle],
) -> str:
    rows = [
        "| Task | Type | Language | Tags |",
        "| --- | --- | --- | --- |",
    ]
    for bundle in sorted(bundles, key=lambda item: item.task.id):
        task = bundle.task
        rel_card = bundle.task_card_path.relative_to(suite_dir)
        tags = ", ".join(f"`{tag}`" for tag in task.tags) or ""
        rows.append(
            f"| [{task.title}]({rel_card.as_posix()}) | `{task.eval_type}` | `{task.language}` | {tags} |"
        )
    return "\n".join(
        [
            f"# {_display_name(suite_dir.name)} Task Cards",
            "",
            "_Generated from task bundles. Do not edit by hand; regenerate with the task-card skill._",
            "",
            *rows,
            "",
        ]
    )


def _write_or_check(path: Path, content: str, check: bool) -> List[Path]:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return []
    if not check:
        path.write_text(content, encoding="utf-8")
    return [path]


def _command_list(commands: List[str]) -> str:
    if not commands:
        return "None configured."
    return "\n".join(f"- `{command}`" for command in commands)


def _environment_text(task: EvalTask) -> str:
    lines = describe_task_environment(task)
    if not lines:
        return "No task-local environment configured."
    return "\n".join(f"- {line}" for line in lines)


def _inline_code_list(values: List[str]) -> str:
    if not values:
        return "None configured."
    return "\n".join(f"- `{value}`" for value in values)


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


def _display_name(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()
