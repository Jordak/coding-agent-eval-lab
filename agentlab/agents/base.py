from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from agentlab.tasks import EvalTask


@dataclass(frozen=True)
class AgentRun:
    agent_name: str
    task_id: str
    transcript_path: Path
    diff_path: Path
    files_changed: List[str] = field(default_factory=list)
    commands_run: List[str] = field(default_factory=list)
    duration_ms: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    input_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_output_tokens: Optional[int] = None
    model_name: Optional[str] = None
    agent_harness_config: Dict[str, Any] = field(default_factory=dict)
    success: Optional[bool] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None


class AgentAdapter(Protocol):
    name: str

    def run(self, task: EvalTask, workspace: Path, run_dir: Path) -> AgentRun:
        """Run an agent against a prepared task workspace."""
