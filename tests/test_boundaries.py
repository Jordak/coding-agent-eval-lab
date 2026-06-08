import unittest

from agentlab.tasks.boundaries import (
    find_boundary_violations,
    path_matches_boundary_glob,
)


class BoundaryGlobTest(unittest.TestCase):
    def test_segment_globs_are_repo_root_relative(self):
        self.assertTrue(path_matches_boundary_glob("src/app.py", "src/*.py"))
        self.assertFalse(path_matches_boundary_glob("src/nested/app.py", "src/*.py"))
        self.assertTrue(path_matches_boundary_glob("src/nested/app.py", "src/**/*.py"))
        self.assertTrue(path_matches_boundary_glob("app.py", "**/*.py"))

    def test_trailing_slash_is_recursive_directory_match(self):
        self.assertTrue(path_matches_boundary_glob("docs/design.md", "docs/"))
        self.assertTrue(path_matches_boundary_glob("docs/nested/design.md", "docs/"))
        self.assertTrue(
            path_matches_boundary_glob(
                "packages/app/private/secret.py",
                "packages/*/private/",
            )
        )
        self.assertTrue(
            path_matches_boundary_glob(
                "apps/web/routes/generated/out.js",
                "apps/**/generated/",
            )
        )
        self.assertFalse(path_matches_boundary_glob("docs", "docs/"))
        self.assertFalse(path_matches_boundary_glob("docs2/design.md", "docs/"))

    def test_changed_paths_only_strip_leading_current_directory_prefix(self):
        self.assertTrue(path_matches_boundary_glob("./docs/design.md", "docs/"))
        self.assertFalse(path_matches_boundary_glob(" docs/design.md", "docs/"))
        self.assertFalse(
            path_matches_boundary_glob("docs/design.md ", "docs/design.md")
        )
        self.assertFalse(path_matches_boundary_glob("docs\\design.md", "docs/"))

    def test_forbidden_paths_win_over_allowed_paths(self):
        violations = find_boundary_violations(
            ["src/app.py", "src/private/secret.py", "README.md"],
            allowed_paths=["src/"],
            forbidden_paths=["src/private/"],
        )

        self.assertEqual(
            [violation.note() for violation in violations],
            [
                "scope boundary violation: `src/private/secret.py` "
                "matches forbidden_paths pattern `src/private/`",
                "scope boundary violation: `README.md` is outside allowed_paths",
            ],
        )

    def test_missing_allowed_paths_adds_no_allow_list_constraint(self):
        violations = find_boundary_violations(
            ["README.md"],
            allowed_paths=None,
            forbidden_paths=[],
        )

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
