from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentlab.tasks.integrity import (
    TaskBundleIntegrityError,
    check_reference_artifact_ready,
    check_task_bundle_integrity,
    load_smoke_test_ready_bundle,
    publish_task_cards,
    validate_task_bundle_sources,
)
from agentlab.tasks import load_task_bundle


class TaskBundleIntegrityTest(unittest.TestCase):
    def test_validates_source_yaml_through_shared_interface(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            valid_bundle = _write_task_bundle(suite_dir, "demo-001")
            invalid_bundle = suite_dir / "demo-002"
            invalid_bundle.mkdir(parents=True)
            (invalid_bundle / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo-002
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    """
                ),
                encoding="utf-8",
            )

            result = validate_task_bundle_sources([suite_dir.as_posix()])

        self.assertEqual(result.matched_files, 2)
        self.assertEqual([bundle.bundle_dir for bundle in result.bundles], [valid_bundle])
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].path, invalid_bundle / "task.yaml")
        self.assertIn("missing required field(s): title", result.failures[0].message)

    def test_detects_generated_task_card_drift_without_suite_indexes(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            bundle_dir = _write_task_bundle(suite_dir, "demo-001")
            card_path = bundle_dir / "task-card.md"
            index_path = suite_dir / "README.md"
            card_path.write_text("stale card\n", encoding="utf-8")
            index_path.write_text("suite index is not generated\n", encoding="utf-8")

            result = check_task_bundle_integrity(
                [suite_dir.as_posix()],
                check_task_cards=True,
            )

            self.assertEqual(result.task_card_changes, [card_path])
            self.assertEqual(card_path.read_text(encoding="utf-8"), "stale card\n")
            self.assertEqual(
                index_path.read_text(encoding="utf-8"),
                "suite index is not generated\n",
            )

    def test_checks_reference_artifact_readiness(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            ready_bundle_dir = _write_task_bundle(suite_dir, "demo-001")
            missing_ref_bundle_dir = _write_task_bundle(
                suite_dir,
                "demo-002",
                reference_artifact=False,
            )

            ready = check_reference_artifact_ready(load_task_bundle(ready_bundle_dir))
            missing = check_reference_artifact_ready(
                load_task_bundle(missing_ref_bundle_dir)
            )

        self.assertTrue(ready.ready)
        self.assertEqual(ready.message, "reference_artifact ready")
        self.assertFalse(missing.ready)
        self.assertEqual(missing.message, "task has no reference_artifact: demo-002")

    def test_smoke_test_readiness_requires_reference_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            ready_bundle_dir = _write_task_bundle(suite_dir, "demo-001")
            missing_ref_bundle_dir = _write_task_bundle(
                suite_dir,
                "demo-002",
                reference_artifact=False,
            )

            ready_bundle = load_smoke_test_ready_bundle(ready_bundle_dir)

            with self.assertRaises(TaskBundleIntegrityError):
                load_smoke_test_ready_bundle(missing_ref_bundle_dir)

        self.assertEqual(ready_bundle.task.id, "demo-001")

    def test_task_card_publication_does_not_write_when_source_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            valid_bundle = _write_task_bundle(suite_dir, "demo-001")
            invalid_bundle = suite_dir / "demo-002"
            invalid_bundle.mkdir(parents=True)
            (invalid_bundle / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo-002
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    """
                ),
                encoding="utf-8",
            )
            card_path = valid_bundle / "task-card.md"
            card_path.write_text("stale card\n", encoding="utf-8")

            result = publish_task_cards([suite_dir.as_posix()])

            self.assertEqual(result.matched_bundles, 1)
            self.assertEqual(result.changed_paths, [])
            self.assertEqual(len(result.failures), 1)
            self.assertEqual(card_path.read_text(encoding="utf-8"), "stale card\n")


def _write_task_bundle(
    suite_dir: Path,
    task_id: str,
    *,
    reference_artifact: bool = True,
) -> Path:
    bundle_dir = suite_dir / task_id
    bundle_dir.mkdir(parents=True)
    lines = [
        f"id: {task_id}",
        "title: Demo task",
        "repo: https://github.com/example/demo",
        "commit: abc123",
        "language: python",
        "suite: example-suite",
        "eval_type: regression",
        "prompt: Fix it.",
        "reference_solution: Change the focused branch.",
    ]
    if reference_artifact:
        (bundle_dir / "reference.patch").write_text(
            "diff --git a/demo.py b/demo.py\n",
            encoding="utf-8",
        )
        lines.extend(
            [
                "reference_artifact:",
                "  type: patch",
                "  path: reference.patch",
            ]
        )

    (bundle_dir / "task.yaml").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return bundle_dir


if __name__ == "__main__":
    unittest.main()
