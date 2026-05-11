from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentlab.task_cards import (
    publish_task_cards,
    render_task_card,
)
from agentlab.tasks import load_task_bundle


class TaskCardPublicationTest(unittest.TestCase):
    def test_renders_task_card_from_task_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle_dir = _write_task_bundle(Path(temp) / "example-suite", "demo-001")
            bundle = load_task_bundle(bundle_dir)

            card = render_task_card(bundle)

        self.assertEqual(
            card,
            textwrap.dedent(
                """\
                # Demo task

                - Task ID: `demo-001`
                - Suite: `example-suite`
                - Evaluation type: `regression`
                - Language: `python`
                - Repository: `https://github.com/example/demo`
                - Commit: `abc123`
                - Source: `task.yaml`

                ## Prompt

                Fix the bug.

                ## Reference

                Change the focused branch and preserve surrounding behavior.

                ## Reference Artifact

                - Type: `patch`
                - Path: `reference.patch`
                - Status: `present`

                ## Environment

                - PATH prepends: `.agentlab/venv/bin`
                - VIRTUAL_ENV={workspace}/.agentlab/venv

                ## Graders

                ### Setup

                - `python -m pip install -e .`

                ### Baseline

                - `pytest`

                ### Target

                - `pytest tests/test_demo.py`

                ## Success Criteria

                - Tests must pass: `true`
                - Max files changed: `2`

                ## Tags

                - `bugfix`
                - `python`

                ## Expected Failure Modes

                - `context_miss`
                - `test_gap`

                _Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
                """
            ),
        )

    def test_check_mode_reports_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            bundle_dir = _write_task_bundle(suite_dir, "demo-001")
            card_path = bundle_dir / "task-card.md"
            card_path.write_text("stale card\n", encoding="utf-8")

            check_result = publish_task_cards([suite_dir.as_posix()], check=True)

            self.assertEqual(check_result.matched_bundles, 1)
            self.assertEqual(check_result.changed_paths, [card_path])
            self.assertEqual(card_path.read_text(encoding="utf-8"), "stale card\n")

            write_result = publish_task_cards([suite_dir.as_posix()])
            clean_result = publish_task_cards([suite_dir.as_posix()], check=True)

            self.assertEqual(write_result.changed_paths, [card_path])
            self.assertEqual(clean_result.changed_paths, [])

    def test_publisher_leaves_suite_readme_alone(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            bundle_dir = _write_task_bundle(suite_dir, "demo-001")
            card_path = bundle_dir / "task-card.md"
            index_path = suite_dir / "README.md"
            card_path.write_text("stale card\n", encoding="utf-8")
            index_path.write_text("stale index\n", encoding="utf-8")

            check_result = publish_task_cards(
                [suite_dir.as_posix()],
                check=True,
            )

            self.assertEqual(check_result.changed_paths, [card_path])
            self.assertEqual(card_path.read_text(encoding="utf-8"), "stale card\n")
            self.assertEqual(index_path.read_text(encoding="utf-8"), "stale index\n")

            write_result = publish_task_cards(
                [suite_dir.as_posix()],
            )

            self.assertEqual(write_result.changed_paths, [card_path])
            self.assertNotEqual(card_path.read_text(encoding="utf-8"), "stale card\n")
            self.assertEqual(index_path.read_text(encoding="utf-8"), "stale index\n")


def _write_task_bundle(
    suite_dir: Path,
    task_id: str,
    *,
    title: str = "Demo task",
    eval_type: str = "regression",
    tags: list[str] | None = None,
) -> Path:
    bundle_dir = suite_dir / task_id
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "reference.patch").write_text("diff --git a/demo.py b/demo.py\n")
    tag_lines = "\n".join(f"  - {tag}" for tag in (tags or ["bugfix", "python"]))
    (bundle_dir / "task.yaml").write_text(
        f"""\
id: {task_id}
title: {title}
repo: https://github.com/example/demo
commit: abc123
language: python
suite: example-suite
eval_type: {eval_type}
prompt: Fix the bug.
reference_solution: Change the focused branch and preserve surrounding behavior.
reference_artifact:
  type: patch
  path: reference.patch
setup:
  - python -m pip install -e .
baseline:
  - pytest
test:
  - pytest tests/test_demo.py
environment_path:
  - .agentlab/venv/bin
environment:
  VIRTUAL_ENV: "{{workspace}}/.agentlab/venv"
success:
  tests_must_pass: true
  max_files_changed: 2
tags:
{tag_lines}
failure_modes:
  - context_miss
  - test_gap
""",
        encoding="utf-8",
    )
    return bundle_dir


if __name__ == "__main__":
    unittest.main()
