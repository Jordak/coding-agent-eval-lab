#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from agentlab.tasks import EvalTask, discover_task_files, load_task  # noqa: E402
from agentlab.environment import describe_task_environment  # noqa: E402


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render Markdown task cards next to task bundle YAML files.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["tasks"],
        help="Task files, task bundle directories, suite directories, or glob patterns.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated task cards or suite indexes would change.",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Do not render suite README.md index files.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    task_files = discover_task_files(args.paths)
    if not task_files:
        print("No task files matched.", file=sys.stderr)
        return 1

    changed: List[Path] = []
    tasks_by_suite: dict[Path, list[tuple[EvalTask, Path]]] = defaultdict(list)
    for task_file in task_files:
        task = load_task(task_file)
        card_path = task_file.parent / "task-card.md"
        changed.extend(_write_or_check(card_path, render_task_card(task), args.check))
        tasks_by_suite[task_file.parent.parent].append((task, card_path))

    if not args.no_index:
        for suite_dir, task_cards in sorted(tasks_by_suite.items()):
            index_path = suite_dir / "README.md"
            changed.extend(
                _write_or_check(
                    index_path,
                    render_suite_index(suite_dir, task_cards),
                    args.check,
                )
            )

    if args.check and changed:
        for path in changed:
            print(f"would change {path}")
        return 1

    for path in changed:
        print(f"wrote {path}")
    if not changed:
        print("Task cards are up to date.")
    return 0


def render_task_card(task: EvalTask) -> str:
    task_path = task.source_path or Path("task.yaml")
    bundle_dir = task_path.parent
    lines = [
        f"# {task.title}",
        "",
        f"- Task ID: `{task.id}`",
        f"- Suite: `{task.suite}`",
        f"- Evaluation type: `{task.eval_type}`",
        f"- Language: `{task.language}`",
        f"- Repository: `{task.repo}`",
        f"- Commit: `{task.commit}`",
        f"- Source: `{task_path.name}`",
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
        _reference_artifact_text(task, bundle_dir),
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
    task_cards: list[tuple[EvalTask, Path]],
) -> str:
    rows = [
        "| Task | Type | Language | Tags |",
        "| --- | --- | --- | --- |",
    ]
    for task, card_path in sorted(task_cards, key=lambda item: item[0].id):
        rel_card = card_path.relative_to(suite_dir)
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


if __name__ == "__main__":
    raise SystemExit(main())
