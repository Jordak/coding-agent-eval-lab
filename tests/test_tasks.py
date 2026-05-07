import textwrap
import tempfile
import unittest
from pathlib import Path

from agentlab.tasks import (
    EvalTask,
    TaskLoadError,
    discover_task_files,
    load_task,
    load_task_mapping,
)


class TaskLoadingTest(unittest.TestCase):
    def test_loads_yaml_subset_task(self):
        task = EvalTask.from_mapping(
            load_task_mapping(
                textwrap.dedent(
                    """
                    id: demo-001
                    title: Demo task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    suite: demo-suite
                    eval_type: regression
                    prompt: >
                      Fix the small bug.
                    reference_solution: >
                      Change the relevant branch and keep existing behavior intact.
                    setup:
                      - python -m pip install -e .
                    baseline:
                      - pytest
                    test:
                      - pytest tests/test_demo.py
                    success:
                      tests_must_pass: true
                      max_files_changed: 2
                    tags:
                      - bugfix
                    failure_modes:
                      - context_miss
                      - resource_inefficient
                    """
                )
            )
        )

        self.assertEqual(task.id, "demo-001")
        self.assertEqual(task.suite, "demo-suite")
        self.assertEqual(task.eval_type, "regression")
        self.assertEqual(
            task.reference_solution,
            "Change the relevant branch and keep existing behavior intact.",
        )
        self.assertEqual(task.prompt, "Fix the small bug.")
        self.assertEqual(task.setup, ["python -m pip install -e ."])
        self.assertEqual(task.failure_modes, ["context_miss", "resource_inefficient"])
        self.assertTrue(task.success.tests_must_pass)
        self.assertEqual(task.success.max_files_changed, 2)

    def test_requires_core_fields(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping({"id": "missing-fields"})

    def test_rejects_unknown_failure_mode(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping(
                {
                    "id": "demo-001",
                    "title": "Demo task",
                    "repo": "https://github.com/example/demo",
                    "commit": "abc123",
                    "language": "python",
                    "prompt": "Fix it.",
                    "failure_modes": ["not_a_real_label"],
                }
            )

    def test_rejects_unknown_eval_type(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping(
                {
                    "id": "demo-001",
                    "title": "Demo task",
                    "repo": "https://github.com/example/demo",
                    "commit": "abc123",
                    "language": "python",
                    "prompt": "Fix it.",
                    "eval_type": "maybe",
                }
            )

    def test_starter_task_is_valid(self):
        task = load_task("tasks/starter/python-bugfix-001")
        self.assertEqual(task.id, "python-bugfix-001")

    def test_discovers_task_bundles_from_directory(self):
        files = discover_task_files(["tasks/starter"])
        self.assertEqual(
            [path.as_posix() for path in files],
            [
                "tasks/starter/2048-advanced-snake-params-001/task.yaml",
                "tasks/starter/python-bugfix-001/task.yaml",
            ],
        )

    def test_loads_task_bundle_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / "demo-task"
            bundle.mkdir()
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo-001
                    title: Demo task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)

        self.assertEqual(task.id, "demo-001")

    def test_rejects_directory_without_task_yaml(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(TaskLoadError):
                load_task(temp)


if __name__ == "__main__":
    unittest.main()
