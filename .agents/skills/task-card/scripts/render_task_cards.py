#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from agentlab.tasks.integrity import publish_task_cards  # noqa: E402


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render Markdown task cards next to task bundle YAML files.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["tasks"],
        help="Task files, task bundle directories, suite directories, or glob patterns.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated task cards would change.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = publish_task_cards(
        args.paths,
        check=args.check,
    )
    if result.failures:
        for failure in result.failures:
            print(f"ERROR {failure.path}: {failure.message}", file=sys.stderr)
        return 1

    if result.matched_bundles == 0:
        print("No task files matched.", file=sys.stderr)
        return 1

    if args.check and result.changed_paths:
        for path in result.changed_paths:
            print(f"would change {path}")
        return 1

    for path in result.changed_paths:
        print(f"wrote {path}")
    if not result.changed_paths:
        print("Task cards are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
