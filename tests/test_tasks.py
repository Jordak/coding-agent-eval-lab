import textwrap
import tempfile
import unittest
from pathlib import Path

from agentlab.tasks import (
    EvalTask,
    TaskLoadError,
    discover_task_bundles,
    discover_task_files,
    load_task_bundle,
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
                    reference_artifact:
                      type: commit
                      commit: def456
                    setup:
                      - python -m pip install -e .
                    baseline:
                      - pytest
                    test:
                      - pytest tests/test_demo.py
                    environment_path:
                      - .agentlab/venv/bin
                    environment:
                      VIRTUAL_ENV: "{workspace}/.agentlab/venv"
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
        self.assertIsNotNone(task.reference_artifact)
        assert task.reference_artifact is not None
        self.assertEqual(task.reference_artifact.type, "commit")
        self.assertEqual(task.reference_artifact.commit, "def456")
        self.assertEqual(task.prompt, "Fix the small bug.")
        self.assertEqual(task.setup, ["python -m pip install -e ."])
        self.assertEqual(task.environment_path, [".agentlab/venv/bin"])
        self.assertEqual(
            task.environment,
            {"VIRTUAL_ENV": "{workspace}/.agentlab/venv"},
        )
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

    def test_rejects_malformed_reference_artifact(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping(
                {
                    "id": "demo-001",
                    "title": "Demo task",
                    "repo": "https://github.com/example/demo",
                    "commit": "abc123",
                    "language": "python",
                    "prompt": "Fix it.",
                    "reference_artifact": {"type": "patch"},
                }
            )

    def test_rejects_reference_artifact_outside_bundle(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping(
                {
                    "id": "demo-001",
                    "title": "Demo task",
                    "repo": "https://github.com/example/demo",
                    "commit": "abc123",
                    "language": "python",
                    "prompt": "Fix it.",
                    "reference_artifact": {
                        "type": "patch",
                        "path": "../reference.patch",
                    },
                }
            )

    def test_rejects_environment_path_outside_workspace(self):
        with self.assertRaises(TaskLoadError):
            EvalTask.from_mapping(
                {
                    "id": "demo-001",
                    "title": "Demo task",
                    "repo": "https://github.com/example/demo",
                    "commit": "abc123",
                    "language": "python",
                    "prompt": "Fix it.",
                    "environment_path": ["../bin"],
                }
            )

    def test_loads_reference_patch_from_task_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / "demo-task"
            bundle.mkdir()
            (bundle / "reference.patch").write_text("diff --git a/a b/a\n", encoding="utf-8")
            (bundle / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo-001
                    title: Demo task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    reference_artifact:
                      type: patch
                      path: reference.patch
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(bundle)

        self.assertIsNotNone(task.reference_artifact)
        assert task.reference_artifact is not None
        self.assertEqual(task.reference_artifact.type, "patch")
        self.assertEqual(task.reference_artifact.path, "reference.patch")

    def test_rejects_missing_reference_patch_file(self):
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
                    reference_artifact:
                      type: patch
                      path: missing.patch
                    """
                ),
                encoding="utf-8",
            )

            with self.assertRaises(TaskLoadError):
                load_task(bundle)

    def test_draft_task_is_valid(self):
        task = load_task("tasks/drafts/python-bugfix-001")
        self.assertEqual(task.id, "python-bugfix-001")
        self.assertEqual(task.suite, "draft-coding")

    def test_discovers_task_bundles_from_directory(self):
        files = discover_task_files(["tasks/starter"])
        self.assertEqual(
            [path.as_posix() for path in files],
            [
                "tasks/starter/2048-advanced-snake-params-001/task.yaml",
                "tasks/starter/click-default-map-nargs-001/task.yaml",
                "tasks/starter/click-help-option-refactor-001/task.yaml",
                "tasks/starter/click-help-shadowed-option-001/task.yaml",
                "tasks/starter/click-should-strip-ansi-tests-001/task.yaml",
                "tasks/starter/datawrapper-mcp-docker-requirements-001/task.yaml",
                "tasks/starter/httpx-verify-false-client-cert-001/task.yaml",
                "tasks/starter/react-tabs-selected-focus-overlay-001/task.yaml",
                "tasks/starter/todomvc-toggle-all-checkbox-001/task.yaml",
            ],
        )

    def test_discovers_loaded_task_bundle_models_from_directory(self):
        bundles = discover_task_bundles(["tasks/starter"])

        self.assertEqual(
            [bundle.task.id for bundle in bundles],
            [
                "2048-advanced-snake-params-001",
                "click-default-map-nargs-001",
                "click-help-option-refactor-001",
                "click-help-shadowed-option-001",
                "click-should-strip-ansi-tests-001",
                "datawrapper-mcp-docker-requirements-001",
                "httpx-verify-false-client-cert-001",
                "react-tabs-selected-focus-overlay-001",
                "todomvc-toggle-all-checkbox-001",
            ],
        )
        self.assertEqual(bundles[0].task_file.name, "task.yaml")
        self.assertEqual(bundles[0].bundle_dir.name, "2048-advanced-snake-params-001")
        self.assertEqual(bundles[0].suite_dir.as_posix(), "tasks/starter")
        self.assertEqual(bundles[0].task_card_path.name, "task-card.md")

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

    def test_loads_task_bundle_model(self):
        with tempfile.TemporaryDirectory() as temp:
            suite = Path(temp) / "suite"
            bundle = suite / "demo-task"
            bundle.mkdir(parents=True)
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

            task_bundle = load_task_bundle(bundle)

        self.assertEqual(task_bundle.task.id, "demo-001")
        self.assertEqual(task_bundle.task_file, bundle / "task.yaml")
        self.assertEqual(task_bundle.bundle_dir, bundle)
        self.assertEqual(task_bundle.suite_dir, suite)
        self.assertEqual(task_bundle.task_card_path, bundle / "task-card.md")

    def test_rejects_directory_without_task_yaml(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(TaskLoadError):
                load_task(temp)


if __name__ == "__main__":
    unittest.main()
