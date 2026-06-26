from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from agentlab.tasks.boundaries import find_boundary_violations
from agentlab.tasks import EvalTask


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

    @property
    def passed(self) -> bool:
        return self.tests_passed


def calculate_grader_outcome(
    task: EvalTask,
    checks: Iterable[CheckResult],
    files_changed: Sequence[str],
    agent_error: Optional[str] = None,
    hidden_checks: Iterable[CheckResult] = (),
) -> Score:
    check_results = list(checks)
    hidden_check_results = list(hidden_checks)
    notes = _outcome_notes(task, files_changed)
    public_checks_passed = (
        all(check.passed for check in check_results)
        if task.success.tests_must_pass
        else True
    )
    hidden_checks_passed = all(check.passed for check in hidden_check_results)

    return Score(
        tests_passed=(
            agent_error is None
            and public_checks_passed
            and hidden_checks_passed
            and not notes
        ),
        checks=check_results,
        notes=notes,
    )


def _outcome_notes(task: EvalTask, files_changed: Sequence[str]) -> List[str]:
    notes: List[str] = []
    max_files_changed = task.success.max_files_changed
    if max_files_changed is not None and len(files_changed) > max_files_changed:
        notes.append(
            "changed "
            f"{len(files_changed)} files; limit is {max_files_changed}"
        )
    notes.extend(
        violation.note()
        for violation in find_boundary_violations(
            files_changed,
            allowed_paths=task.success.allowed_paths,
            forbidden_paths=task.success.forbidden_paths,
        )
    )
    return notes
