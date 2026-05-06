import textwrap
import unittest

from agentlab.tasks import EvalTask, TaskLoadError, load_task, load_task_mapping


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
                    prompt: >
                      Fix the small bug.
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
                    """
                )
            )
        )

        self.assertEqual(task.id, "demo-001")
        self.assertEqual(task.prompt, "Fix the small bug.")
        self.assertEqual(task.setup, ["python -m pip install -e ."])
        self.assertTrue(task.success.tests_must_pass)
        self.assertEqual(task.success.max_files_changed, 2)

    def test_requires_core_fields(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping({"id": "missing-fields"})

    def test_starter_task_is_valid(self):
        task = load_task("tasks/starter/python_bugfix_001.yaml")
        self.assertEqual(task.id, "python-bugfix-001")


if __name__ == "__main__":
    unittest.main()
