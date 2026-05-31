from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    passed: bool
    command: List[str] = field(default_factory=list)
    message: str = ""
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class PreflightResult:
    agent_name: str
    checks: List[PreflightCheck]
    agent_harness_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)
