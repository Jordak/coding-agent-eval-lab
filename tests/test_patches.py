import unittest

from agentlab.runtime.patches import count_patch_lines


class PatchStatsTest(unittest.TestCase):
    def test_counts_unified_diff_added_and_deleted_lines(self):
        diff = """diff --git a/app.txt b/app.txt
index 0000000..1111111 100644
--- a/app.txt
+++ b/app.txt
@@ -1,2 +1,3 @@
-before
+after
 unchanged
+new
"""

        stats = count_patch_lines(diff)

        self.assertEqual(stats.lines_added, 2)
        self.assertEqual(stats.lines_deleted, 1)


if __name__ == "__main__":
    unittest.main()
