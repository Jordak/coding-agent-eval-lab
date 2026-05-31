from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatchStats:
    lines_added: int = 0
    lines_deleted: int = 0


def count_patch_lines(diff_text: str) -> PatchStats:
    lines_added = 0
    lines_deleted = 0
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            lines_added += 1
        elif line.startswith("-"):
            lines_deleted += 1
    return PatchStats(lines_added=lines_added, lines_deleted=lines_deleted)
