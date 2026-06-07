import shutil
import os
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from agentlab.tasks import EvalTask
from agentlab.execution.workspace import capture_diff, prepare_workspace


class WorkspaceTest(unittest.TestCase):
    def test_prepare_workspace_accepts_relative_root(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "README.md").write_text("# Fixture\n", encoding="utf-8")
            self._git(["add", "README.md"], repo)
            self._git(["commit", "-m", "initial"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            original_cwd = Path.cwd()
            try:
                # Reproduce CLI behavior where runs-dir is provided as a relative path.
                import os

                os.chdir(temp_path)
                task = EvalTask(
                    id="fixture-task",
                    title="Fixture task",
                    repo=str(repo),
                    commit=commit,
                    language="python",
                    prompt="Do nothing.",
                )

                prepared = prepare_workspace(task, Path("runs/relative-root"))
            finally:
                os.chdir(original_cwd)

            self.assertTrue(prepared.path.exists())
            self.assertEqual(prepared.workspace_history_policy, "base_only")
            self._assert_base_only_repository(prepared.path)
            self.assertEqual(
                self._git(["rev-parse", "HEAD"], prepared.path).stdout.strip(),
                prepared.workspace_base_ref,
            )
            self.assertNotEqual(prepared.workspace_base_ref, commit)
            self.assertEqual(
                (prepared.path / "README.md").read_text(encoding="utf-8"),
                "# Fixture\n",
            )

    def test_prepare_workspace_hides_later_source_history(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            (repo / "app.txt").write_text("gold\n", encoding="utf-8")
            self._git(["commit", "-am", "gold"], repo)
            gold_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            self._git(["tag", "gold-fix"], repo)

            task = EvalTask(
                id="leakage-task",
                title="Leakage task",
                repo=str(repo),
                commit=base_commit,
                language="text",
                prompt="Do not inspect future commits.",
            )

            prepared = prepare_workspace(task, temp_path / "workspace")

            self._assert_base_only_repository(prepared.path)
            self.assertNotIn(
                gold_commit,
                self._git(["log", "--all", "--format=%H"], prepared.path).stdout,
            )
            self.assertEqual(
                self._git(["remote"], prepared.path).stdout.strip(),
                "",
            )
            self.assertEqual(
                self._git(["tag"], prepared.path).stdout.strip(),
                "",
            )
            self.assertEqual(
                (prepared.path / "app.txt").read_text(encoding="utf-8"),
                "base\n",
            )

    def test_prepare_workspace_preserves_exact_source_tree(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
            (repo / ".gitattributes").write_text(
                "exported.txt export-ignore\nsubstituted.txt export-subst\n",
                encoding="utf-8",
            )
            (repo / "exported.txt").write_text("must stay\n", encoding="utf-8")
            (repo / "ignored.txt").write_text("tracked anyway\n", encoding="utf-8")
            (repo / "substituted.txt").write_text(
                "$Format:%H$\n",
                encoding="utf-8",
            )
            self._git(
                [
                    "add",
                    ".gitignore",
                    ".gitattributes",
                    "exported.txt",
                    "substituted.txt",
                ],
                repo,
            )
            self._git(["add", "-f", "ignored.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            task = EvalTask(
                id="exact-tree-task",
                title="Exact tree task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            prepared = prepare_workspace(task, temp_path / "workspace")

            self.assertEqual(
                self._git(["rev-parse", f"{commit}^{{tree}}"], repo).stdout.strip(),
                self._git(["rev-parse", "HEAD^{tree}"], prepared.path).stdout.strip(),
            )
            self.assertEqual(
                (prepared.path / "exported.txt").read_text(encoding="utf-8"),
                "must stay\n",
            )
            self.assertEqual(
                (prepared.path / "ignored.txt").read_text(encoding="utf-8"),
                "tracked anyway\n",
            )
            self.assertEqual(
                (prepared.path / "substituted.txt").read_text(encoding="utf-8"),
                "$Format:%H$\n",
            )

    def test_prepare_workspace_rejects_git_control_paths(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            bad_config = temp_path / "bad-config"
            bad_config.write_text(
                '[remote "origin"]\n    url = https://example.com/source.git\n',
                encoding="utf-8",
            )
            blob = self._git(
                ["hash-object", "-w", str(bad_config)],
                repo,
            ).stdout.strip()
            subtree = self._git_with_input(
                ["mktree"],
                repo,
                f"100644 blob {blob}\tconfig\n",
            ).stdout.strip()
            tree = self._git_with_input(
                ["mktree"],
                repo,
                f"040000 tree {subtree}\t.GIT\n",
            ).stdout.strip()
            commit = self._git(
                ["commit-tree", tree, "-m", "malicious tree"],
                repo,
            ).stdout.strip()
            task = EvalTask(
                id="git-control-path-task",
                title="Git control path task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "unsafe git control tree path",
            ):
                prepare_workspace(task, temp_path / "workspace")

    def test_synthetic_commit_uses_fixed_identity_and_date(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            task = EvalTask(
                id="stable-base-task",
                title="Stable base task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_AUTHOR_NAME": "Local User",
                    "GIT_AUTHOR_EMAIL": "local@example.com",
                    "GIT_AUTHOR_DATE": "2026-06-06T12:00:00+00:00",
                    "GIT_COMMITTER_NAME": "Local User",
                    "GIT_COMMITTER_EMAIL": "local@example.com",
                    "GIT_COMMITTER_DATE": "2026-06-06T12:00:00+00:00",
                },
            ):
                prepared_a = prepare_workspace(task, temp_path / "workspace-a")
                prepared_b = prepare_workspace(task, temp_path / "workspace-b")

            self.assertEqual(
                prepared_a.workspace_base_ref,
                prepared_b.workspace_base_ref,
            )
            self.assertEqual(
                self._git(
                    ["log", "-1", "--format=%an <%ae>|%cn <%ce>|%aI|%cI"],
                    prepared_a.path,
                ).stdout.strip(),
                (
                    "Agent Eval Lab <agentlab@example.com>|"
                    "Agent Eval Lab <agentlab@example.com>|"
                    "2000-01-01T00:00:00Z|"
                    "2000-01-01T00:00:00Z"
                ),
            )

    def test_prepare_workspace_uses_source_blob_bytes_without_smudge_filters(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            home = temp_path / "home"
            xdg_config = temp_path / "xdg"
            home.mkdir()
            xdg_config.mkdir()
            (home / ".gitconfig").write_text(
                "\n".join(
                    [
                        '[filter "hydrate"]',
                        "    smudge = sed s/pointer/HYDRATED/",
                        "    clean = sed s/HYDRATED/pointer/",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            repo = temp_path / "repo"
            repo.mkdir()

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                self._git(["init"], repo)
                self._git(["config", "user.email", "agentlab@example.com"], repo)
                self._git(["config", "user.name", "Agent Lab"], repo)
                (repo / ".gitattributes").write_text(
                    "asset.dat filter=hydrate\n",
                    encoding="utf-8",
                )
                (repo / "asset.dat").write_text("pointer\n", encoding="utf-8")
                self._git(["add", ".gitattributes", "asset.dat"], repo)
                self._git(["commit", "-m", "base"], repo)
                commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
                task = EvalTask(
                    id="filter-task",
                    title="Filter task",
                    repo=str(repo),
                    commit=commit,
                    language="text",
                    prompt="Do nothing.",
                )

                prepared = prepare_workspace(task, temp_path / "workspace")

            source_blob = self._git(
                ["cat-file", "blob", f"{commit}:asset.dat"],
                repo,
            ).stdout
            self.assertEqual(source_blob, "pointer\n")
            self.assertEqual(
                (prepared.path / "asset.dat").read_text(encoding="utf-8"),
                source_blob,
            )
            self.assertEqual(
                self._git(["status", "--short"], prepared.path).stdout.strip(),
                "",
            )

    def test_prepare_workspace_does_not_checkout_private_prep_clone(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            home = temp_path / "home"
            xdg_config = temp_path / "xdg"
            template = temp_path / "template"
            sentinel = temp_path / "checkout-invoked"
            home.mkdir()
            xdg_config.mkdir()
            (template / "hooks").mkdir(parents=True)
            smudge = temp_path / "fail-smudge.sh"
            smudge.write_text(
                f"#!/bin/sh\necho smudge > {sentinel}\nexit 1\n",
                encoding="utf-8",
            )
            smudge.chmod(0o755)
            post_checkout = template / "hooks" / "post-checkout"
            post_checkout.write_text(
                f"#!/bin/sh\necho hook > {sentinel}\nexit 1\n",
                encoding="utf-8",
            )
            post_checkout.chmod(0o755)
            (home / ".gitconfig").write_text(
                "\n".join(
                    [
                        '[filter "block"]',
                        f"    smudge = {smudge}",
                        "    clean = cat",
                        "    required = true",
                        "[init]",
                        f"    templateDir = {template}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            repo = temp_path / "repo"
            repo.mkdir()

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                self._git(["init"], repo)
                self._git(["config", "user.email", "agentlab@example.com"], repo)
                self._git(["config", "user.name", "Agent Lab"], repo)
                (repo / ".gitattributes").write_text(
                    "asset.dat filter=block\n",
                    encoding="utf-8",
                )
                (repo / "asset.dat").write_text("pointer\n", encoding="utf-8")
                self._git(["add", ".gitattributes", "asset.dat"], repo)
                self._git(["commit", "-m", "base"], repo)
                commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
                task = EvalTask(
                    id="no-prep-checkout-task",
                    title="No prep checkout task",
                    repo=str(repo),
                    commit=commit,
                    language="text",
                    prompt="Do nothing.",
                )

                prepared = prepare_workspace(task, temp_path / "workspace")

            self.assertFalse(sentinel.exists())
            self.assertEqual(
                (prepared.path / "asset.dat").read_text(encoding="utf-8"),
                "pointer\n",
            )
            self.assertEqual(
                self._git(["status", "--short"], prepared.path).stdout.strip(),
                "",
            )

    def test_prepare_workspace_ignores_clone_time_git_config(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            hostile_config = temp_path / "hostile.gitconfig"
            hostile_config.write_text(
                "\n".join(
                    [
                        '[protocol "file"]',
                        "    allow = never",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            task = EvalTask(
                id="clone-config-task",
                title="Clone config task",
                repo=repo.as_uri(),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(hostile_config),
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "protocol.file.allow",
                    "GIT_CONFIG_VALUE_0": "never",
                },
            ):
                prepared = prepare_workspace(task, temp_path / "workspace")

            self.assertEqual(
                (prepared.path / "app.txt").read_text(encoding="utf-8"),
                "base\n",
            )
            self.assertEqual(
                self._git(["status", "--short"], prepared.path).stdout.strip(),
                "",
            )

    def test_synthetic_commit_ignores_global_hooks_and_templates(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            home = temp_path / "home"
            xdg_config = temp_path / "xdg"
            global_hooks = temp_path / "global-hooks"
            template = temp_path / "template"
            home.mkdir()
            xdg_config.mkdir()
            global_hooks.mkdir()
            (template / "hooks").mkdir(parents=True)
            (home / ".gitconfig").write_text(
                "\n".join(
                    [
                        "[core]",
                        f"    hooksPath = {global_hooks}",
                        "[init]",
                        f"    templateDir = {template}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            hook = global_hooks / "prepare-commit-msg"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            template_hook = template / "hooks" / "template-hook"
            template_hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            template_hook.chmod(0o755)

            task = EvalTask(
                id="global-hooks-task",
                title="Global hooks task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                prepared = prepare_workspace(task, temp_path / "workspace")

            self.assertFalse(
                (prepared.path / ".git" / "hooks" / "template-hook").exists()
            )
            self.assertEqual(
                self._git(["config", "--get", "core.hooksPath"], prepared.path)
                .stdout.strip(),
                ".git/hooks",
            )
            self.assertEqual(
                self._git(
                    ["log", "-1", "--format=%an <%ae>|%cn <%ce>|%aI|%cI"],
                    prepared.path,
                ).stdout.strip(),
                (
                    "Agent Eval Lab <agentlab@example.com>|"
                    "Agent Eval Lab <agentlab@example.com>|"
                    "2000-01-01T00:00:00Z|"
                    "2000-01-01T00:00:00Z"
                ),
            )

    def test_synthetic_commit_ignores_global_object_format_and_git_object_dir(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()

            home = temp_path / "home"
            xdg_config = temp_path / "xdg"
            external_objects = temp_path / "external-objects"
            home.mkdir()
            xdg_config.mkdir()
            external_objects.mkdir()
            (home / ".gitconfig").write_text(
                "\n".join(
                    [
                        "[init]",
                        "    defaultObjectFormat = sha256",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            task = EvalTask(
                id="global-object-config-task",
                title="Global object config task",
                repo=str(repo),
                commit=commit,
                language="text",
                prompt="Do nothing.",
            )

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "GIT_OBJECT_DIRECTORY": str(external_objects),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                prepared_a = prepare_workspace(task, temp_path / "workspace-a")
                prepared_b = prepare_workspace(task, temp_path / "workspace-b")

            self.assertEqual(prepared_a.workspace_base_ref, prepared_b.workspace_base_ref)
            self.assertEqual(
                self._git(
                    ["rev-parse", "--show-object-format"],
                    prepared_a.path,
                ).stdout.strip(),
                self._git(
                    ["rev-parse", "--show-object-format"],
                    repo,
                ).stdout.strip(),
            )
            self.assertEqual(
                self._git(["status", "--short"], prepared_a.path).stdout.strip(),
                "",
            )

    def test_capture_diff_uses_explicit_synthetic_base_ref(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            repo.mkdir()
            self._git(["init"], repo)
            self._git(["config", "user.email", "agentlab@example.com"], repo)
            self._git(["config", "user.name", "Agent Lab"], repo)
            (repo / "app.txt").write_text("before\n", encoding="utf-8")
            self._git(["add", "app.txt"], repo)
            self._git(["commit", "-m", "base"], repo)
            base_commit = self._git(["rev-parse", "HEAD"], repo).stdout.strip()
            task = EvalTask(
                id="diff-base-task",
                title="Diff base task",
                repo=str(repo),
                commit=base_commit,
                language="text",
                prompt="Change the file.",
            )
            prepared = prepare_workspace(task, temp_path / "workspace")
            (prepared.path / "app.txt").write_text("after\n", encoding="utf-8")

            changed = capture_diff(
                prepared.path,
                temp_path / "diff.patch",
                base_ref=prepared.workspace_base_ref,
            )

            self.assertEqual(changed, ["app.txt"])
            self.assertIn(
                "-before",
                (temp_path / "diff.patch").read_text(encoding="utf-8"),
            )

    def _git(self, args, cwd):
        completed = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return completed

    def _git_with_input(self, args, cwd, input_text):
        completed = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            text=True,
            input=input_text,
            capture_output=True,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return completed

    def _assert_base_only_repository(self, workspace):
        self.assertEqual(
            self._git(["rev-list", "--count", "HEAD"], workspace).stdout.strip(),
            "1",
        )
        self.assertEqual(
            self._git(
                [
                    "for-each-ref",
                    "--format=%(refname)",
                    "refs/heads",
                    "refs/remotes",
                    "refs/tags",
                ],
                workspace,
            ).stdout.strip(),
            "",
        )
        self.assertFalse((workspace / ".git" / "logs").exists())


if __name__ == "__main__":
    unittest.main()
