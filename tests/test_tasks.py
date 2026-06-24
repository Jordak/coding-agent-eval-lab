import textwrap
import tempfile
import unittest
from pathlib import Path

from agentlab.tasks import (
    EvalTask,
    HiddenVerifier,
    TaskLoadError,
    discover_task_bundles,
    discover_task_files,
    load_task_bundle,
    load_task,
    load_task_mapping,
)


class TaskLoadingTest(unittest.TestCase):
    def test_loads_yaml_task(self):
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

    def test_loads_folded_command_list_items(self):
        task = EvalTask.from_mapping(
            load_task_mapping(
                textwrap.dedent(
                    """
                    id: demo-001
                    title: Demo task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    baseline:
                      - >-
                        python -c "assert {'key': 'value'}['key'] == 'value'"
                    visible_validation:
                      - >-
                        python -m pytest tests/test_demo.py -q
                    test:
                      - >-
                        python -c "print('still one command')"
                    """
                )
            )
        )

        self.assertEqual(
            task.baseline,
            ['python -c "assert {\'key\': \'value\'}[\'key\'] == \'value\'"'],
        )
        self.assertEqual(
            task.visible_validation,
            ["python -m pytest tests/test_demo.py -q"],
        )
        self.assertEqual(task.test, ['python -c "print(\'still one command\')"'])

    def test_loads_hidden_verifier_from_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp)
            (bundle / "verifier.patch").write_text(
                "diff --git a/tests/hidden.py b/tests/hidden.py\n",
                encoding="utf-8",
            )
            task_file = bundle / "task.yaml"
            task_file.write_text(
                textwrap.dedent(
                    """
                    id: hidden-task
                    title: Hidden verifier task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    hidden_verifier:
                      patch: verifier.patch
                      commands:
                        - pytest tests/hidden.py
                    """
                ),
                encoding="utf-8",
            )

            task = load_task(task_file)

            self.assertEqual(
                task.hidden_verifier,
                HiddenVerifier(
                    patch="verifier.patch",
                    commands=["pytest tests/hidden.py"],
                ),
            )

    def test_rejects_invalid_hidden_verifier(self):
        base = {
            "id": "demo-001",
            "title": "Demo task",
            "repo": "https://github.com/example/demo",
            "commit": "abc123",
            "language": "python",
            "prompt": "Fix it.",
        }
        invalid_values = [
            {"patch": "/tmp/verifier.patch", "commands": ["pytest"]},
            {"patch": "../verifier.patch", "commands": ["pytest"]},
            {"patch": "verifier.txt", "commands": ["pytest"]},
            {"patch": "verifier.patch", "commands": [123]},
            {"patch": "verifier.patch", "commands": []},
            {"commands": ["pytest"]},
            {"patch": "verifier.patch"},
        ]
        for hidden_verifier in invalid_values:
            with self.subTest(hidden_verifier=hidden_verifier):
                with self.assertRaises(TaskLoadError):
                    EvalTask.from_mapping(
                        {
                            **base,
                            "hidden_verifier": hidden_verifier,
                        }
                    )

    def test_rejects_missing_hidden_verifier_patch_file_for_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            task_file = Path(temp) / "task.yaml"
            task_file.write_text(
                textwrap.dedent(
                    """
                    id: hidden-task
                    title: Hidden verifier task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    hidden_verifier:
                      patch: verifier.patch
                      commands:
                        - pytest tests/hidden.py
                    """
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(TaskLoadError, "does not exist"):
                load_task(task_file)

    def test_loads_boundary_metadata_and_consent_style(self):
        task = EvalTask.from_mapping(
            load_task_mapping(
                textwrap.dedent(
                    """
                    id: demo-001
                    title: Demo task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    consent_style: explicit_allow
                    success:
                      allowed_paths:
                        - src/
                        - tests/**/*.py
                      forbidden_paths:
                        - src/private/
                    """
                )
            )
        )

        self.assertEqual(task.consent_style, "explicit_allow")
        self.assertEqual(task.success.allowed_paths, ["src/", "tests/**/*.py"])
        self.assertEqual(task.success.forbidden_paths, ["src/private/"])

    def test_missing_allowed_paths_has_no_allow_list(self):
        task = EvalTask.from_mapping(
            load_task_mapping(
                textwrap.dedent(
                    """
                    id: demo-001
                    title: Demo task
                    repo: https://github.com/example/demo
                    commit: abc123
                    language: python
                    prompt: Fix it.
                    success:
                      forbidden_paths: []
                    """
                )
            )
        )

        self.assertIsNone(task.success.allowed_paths)
        self.assertEqual(task.success.forbidden_paths, [])

    def test_rejects_empty_allowed_paths(self):
        with self.assertRaisesRegex(TaskLoadError, "success.allowed_paths"):
            EvalTask.from_mapping(
                load_task_mapping(
                    textwrap.dedent(
                        """
                        id: demo-001
                        title: Demo task
                        repo: https://github.com/example/demo
                        commit: abc123
                        language: python
                        prompt: Fix it.
                        success:
                          allowed_paths: []
                        """
                    )
                )
            )

    def test_rejects_unknown_consent_style(self):
        with self.assertRaisesRegex(TaskLoadError, "consent_style"):
            EvalTask.from_mapping(
                {
                    "id": "demo-001",
                    "title": "Demo task",
                    "repo": "https://github.com/example/demo",
                    "commit": "abc123",
                    "language": "python",
                    "prompt": "Fix it.",
                    "consent_style": "maybe",
                }
            )

    def test_rejects_invalid_boundary_globs(self):
        invalid_patterns = [
            "!src/**",
            "./!src/**",
            "././!src/**",
            "./src/",
            "./*.py",
            " src/",
            "src/ ",
            "src\\app.py",
            "../secret",
            "/absolute/path",
            "src//app.py",
            "src/./private/",
            "[!a]*.py",
            "src/[ab].py",
        ]
        for pattern in invalid_patterns:
            for field_name in ("allowed_paths", "forbidden_paths"):
                with self.subTest(pattern=pattern, field_name=field_name):
                    with self.assertRaises(TaskLoadError):
                        EvalTask.from_mapping(
                            {
                                "id": "demo-001",
                                "title": "Demo task",
                                "repo": "https://github.com/example/demo",
                                "commit": "abc123",
                                "language": "python",
                                "prompt": "Fix it.",
                                "success": {field_name: [pattern]},
                            }
                        )

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
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            _write_minimal_task_bundle(suite_dir, "demo-002")
            _write_minimal_task_bundle(suite_dir, "demo-001")

            files = discover_task_files([suite_dir.as_posix()])

        self.assertEqual(
            [path.relative_to(suite_dir).as_posix() for path in files],
            [
                "demo-001/task.yaml",
                "demo-002/task.yaml",
            ],
        )

    def test_discovers_loaded_task_bundle_models_from_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            suite_dir = Path(temp) / "example-suite"
            _write_minimal_task_bundle(suite_dir, "demo-002")
            _write_minimal_task_bundle(suite_dir, "demo-001")

            bundles = discover_task_bundles([suite_dir.as_posix()])

        self.assertEqual(
            [bundle.task.id for bundle in bundles],
            [
                "demo-001",
                "demo-002",
            ],
        )
        self.assertEqual(bundles[0].task_file.name, "task.yaml")
        self.assertEqual(bundles[0].bundle_dir.name, "demo-001")
        self.assertEqual(bundles[0].suite_dir, suite_dir)
        self.assertEqual(bundles[0].task_card_path.name, "task-card.md")

    def test_starter_task_bundles_are_valid_without_enumerating_ids(self):
        bundles = discover_task_bundles(["tasks/starter"])

        self.assertGreater(len(bundles), 0)
        self.assertEqual(
            [bundle.task.id for bundle in bundles],
            sorted(bundle.task.id for bundle in bundles),
        )
        for bundle in bundles:
            self.assertEqual(bundle.task.id, bundle.bundle_dir.name)
            self.assertEqual(bundle.task.suite, "starter-coding")
            self.assertIsNotNone(bundle.task.reference_artifact)

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


def _write_minimal_task_bundle(suite_dir: Path, task_id: str) -> Path:
    bundle_dir = suite_dir / task_id
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "task.yaml").write_text(
        textwrap.dedent(
            f"""
            id: {task_id}
            title: Demo task
            repo: https://github.com/example/demo
            commit: abc123
            language: python
            prompt: Fix it.
            """
        ),
        encoding="utf-8",
    )
    return bundle_dir


if __name__ == "__main__":
    unittest.main()
