import shutil
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from agentlab.tasks import EvalTask
from agentlab.execution.workspace import capture_diff, prepare_workspace
from tests.git_fixtures import assert_base_only_repository
from tests.git_fixtures import commit_all
from tests.git_fixtures import commit_file
from tests.git_fixtures import eval_task
from tests.git_fixtures import git
from tests.git_fixtures import head
from tests.git_fixtures import init_repo


class WorkspaceTest(unittest.TestCase):
    def test_prepare_workspace_accepts_relative_root(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "README.md", "# Fixture\n", message="initial")

            original_cwd = Path.cwd()
            try:
                # Reproduce CLI behavior where runs-dir is provided as a relative path.
                import os

                os.chdir(temp_path)
                task = eval_task(
                    task_id="fixture-task",
                    repo=str(repo),
                    commit=commit,
                    title="Fixture task",
                    language="python",
                )

                prepared = prepare_workspace(task, Path("runs/relative-root"))
            finally:
                os.chdir(original_cwd)

            self.assertTrue(prepared.path.exists())
            self.assertEqual(prepared.workspace_history_policy, "base_only")
            assert_base_only_repository(self, prepared.path)
            self.assertEqual(
                git(["rev-parse", "HEAD"], prepared.path).stdout.strip(),
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
            init_repo(repo)
            base_commit = commit_file(repo, "app.txt", "base\n", message="base")

            (repo / "app.txt").write_text("gold\n", encoding="utf-8")
            gold_commit = commit_all(repo, "gold")
            git(["tag", "gold-fix"], repo)

            task = eval_task(
                task_id="leakage-task",
                repo=str(repo),
                commit=base_commit,
                title="Leakage task",
                prompt="Do not inspect future commits.",
            )

            prepared = prepare_workspace(task, temp_path / "workspace")

            assert_base_only_repository(self, prepared.path)
            self.assertNotIn(
                gold_commit,
                git(["log", "--all", "--format=%H"], prepared.path).stdout,
            )
            self.assertEqual(
                git(["remote"], prepared.path).stdout.strip(),
                "",
            )
            self.assertEqual(
                git(["tag"], prepared.path).stdout.strip(),
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
            init_repo(repo)
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
            git(
                [
                    "add",
                    ".gitignore",
                    ".gitattributes",
                    "exported.txt",
                    "substituted.txt",
                ],
                repo,
            )
            git(["add", "-f", "ignored.txt"], repo)
            git(["commit", "-m", "base"], repo)
            commit = git(["rev-parse", "HEAD"], repo).stdout.strip()

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
                git(["rev-parse", f"{commit}^{{tree}}"], repo).stdout.strip(),
                git(["rev-parse", "HEAD^{tree}"], prepared.path).stdout.strip(),
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
            init_repo(repo)
            bad_config = temp_path / "bad-config"
            bad_config.write_text(
                '[remote "origin"]\n    url = https://example.com/source.git\n',
                encoding="utf-8",
            )
            blob = git(
                ["hash-object", "-w", str(bad_config)],
                repo,
            ).stdout.strip()
            subtree = git(
                ["mktree"],
                repo,
                f"100644 blob {blob}\tconfig\n",
            ).stdout.strip()
            tree = git(
                ["mktree"],
                repo,
                f"040000 tree {subtree}\t.GIT\n",
            ).stdout.strip()
            commit = git(
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

    def test_prepare_workspace_invalid_commit_does_not_reserve_workspace(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "base\n", message="base")
            task = eval_task(
                task_id="missing-commit-task",
                repo=str(repo),
                commit="0" * 40,
                title="Missing commit task",
            )

            with self.assertRaisesRegex(RuntimeError, "git rev-parse failed"):
                prepare_workspace(task, temp_path / "workspace")

            self.assertFalse((temp_path / "workspace" / task.id).exists())

            retry_task = eval_task(
                task_id=task.id,
                repo=str(repo),
                commit=commit,
                title="Missing commit task",
            )
            prepared = prepare_workspace(retry_task, temp_path / "workspace")

            self.assertTrue(prepared.path.exists())

    def test_synthetic_commit_uses_fixed_identity_and_date(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "base\n", message="base")
            task = eval_task(
                task_id="stable-base-task",
                repo=str(repo),
                commit=commit,
                title="Stable base task",
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
                git(
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

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                init_repo(repo)
                (repo / ".gitattributes").write_text(
                    "asset.dat filter=hydrate\n",
                    encoding="utf-8",
                )
                (repo / "asset.dat").write_text("pointer\n", encoding="utf-8")
                git(["add", ".gitattributes", "asset.dat"], repo)
                git(["commit", "-m", "base"], repo)
                commit = head(repo)
                task = eval_task(
                    task_id="filter-task",
                    repo=str(repo),
                    commit=commit,
                    title="Filter task",
                )

                prepared = prepare_workspace(task, temp_path / "workspace")

            source_blob = git(
                ["cat-file", "blob", f"{commit}:asset.dat"],
                repo,
            ).stdout
            self.assertEqual(source_blob, "pointer\n")
            self.assertEqual(
                (prepared.path / "asset.dat").read_text(encoding="utf-8"),
                source_blob,
            )
            self.assertEqual(
                git(["status", "--short"], prepared.path).stdout.strip(),
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

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                    "HOME": str(home),
                    "XDG_CONFIG_HOME": str(xdg_config),
                },
            ):
                init_repo(repo)
                (repo / ".gitattributes").write_text(
                    "asset.dat filter=block\n",
                    encoding="utf-8",
                )
                (repo / "asset.dat").write_text("pointer\n", encoding="utf-8")
                git(["add", ".gitattributes", "asset.dat"], repo)
                git(["commit", "-m", "base"], repo)
                commit = head(repo)
                task = eval_task(
                    task_id="no-prep-checkout-task",
                    repo=str(repo),
                    commit=commit,
                    title="No prep checkout task",
                )

                prepared = prepare_workspace(task, temp_path / "workspace")

            self.assertFalse(sentinel.exists())
            self.assertEqual(
                (prepared.path / "asset.dat").read_text(encoding="utf-8"),
                "pointer\n",
            )
            self.assertEqual(
                git(["status", "--short"], prepared.path).stdout.strip(),
                "",
            )

    def test_prepare_workspace_ignores_clone_time_git_config(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "base\n", message="base")

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
            task = eval_task(
                task_id="clone-config-task",
                repo=repo.as_uri(),
                commit=commit,
                title="Clone config task",
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
                git(["status", "--short"], prepared.path).stdout.strip(),
                "",
            )

    def test_synthetic_commit_ignores_global_hooks_and_templates(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "base\n", message="base")

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

            task = eval_task(
                task_id="global-hooks-task",
                repo=str(repo),
                commit=commit,
                title="Global hooks task",
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
                git(["config", "--get", "core.hooksPath"], prepared.path)
                .stdout.strip(),
                ".git/hooks",
            )
            self.assertEqual(
                git(
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
            init_repo(repo)
            commit = commit_file(repo, "app.txt", "base\n", message="base")

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
            task = eval_task(
                task_id="global-object-config-task",
                repo=str(repo),
                commit=commit,
                title="Global object config task",
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
                git(
                    ["rev-parse", "--show-object-format"],
                    prepared_a.path,
                ).stdout.strip(),
                git(
                    ["rev-parse", "--show-object-format"],
                    repo,
                ).stdout.strip(),
            )
            self.assertEqual(
                git(["status", "--short"], prepared_a.path).stdout.strip(),
                "",
            )

    def test_capture_diff_uses_explicit_synthetic_base_ref(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            repo = temp_path / "repo"
            init_repo(repo)
            base_commit = commit_file(repo, "app.txt", "before\n", message="base")
            task = eval_task(
                task_id="diff-base-task",
                repo=str(repo),
                commit=base_commit,
                title="Diff base task",
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

    def test_capture_diff_records_all_final_changed_paths(self):
        if shutil.which("git") is None:
            self.skipTest("git is required for workspace preparation")

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            init_repo(repo)
            (repo / "staged.txt").write_text("before\n", encoding="utf-8")
            (repo / "unstaged.txt").write_text("before\n", encoding="utf-8")
            (repo / "delete.txt").write_text("before\n", encoding="utf-8")
            (repo / "rename-old.txt").write_text("before\n", encoding="utf-8")
            git(["add", "."], repo)
            git(["commit", "-m", "initial"], repo)

            (repo / "staged.txt").write_text("after\n", encoding="utf-8")
            git(["add", "staged.txt"], repo)
            (repo / "unstaged.txt").write_text("after\n", encoding="utf-8")
            (repo / "delete.txt").unlink()
            git(["mv", "rename-old.txt", "rename-new.txt"], repo)
            (repo / "new.txt").write_text("new\n", encoding="utf-8")

            diff_path = Path(temp) / "diff.patch"
            files_changed = capture_diff(repo, diff_path)
            diff_text = diff_path.read_text(encoding="utf-8")

            self.assertCountEqual(
                files_changed,
                [
                    "delete.txt",
                    "new.txt",
                    "rename-new.txt",
                    "rename-old.txt",
                    "staged.txt",
                    "unstaged.txt",
                ],
            )
            self.assertIn("new.txt", diff_text)
            self.assertEqual(
                self._git(["ls-files", "--stage", "new.txt"], repo).stdout,
                "",
            )
            self.assertIn(
                "new.txt",
                self._git(["ls-files", "--others"], repo).stdout.splitlines(),
            )

if __name__ == "__main__":
    unittest.main()
