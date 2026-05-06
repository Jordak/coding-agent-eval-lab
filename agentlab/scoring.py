from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CheckResult:
    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class Score:
    tests_passed: bool
    checks: List[CheckResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
