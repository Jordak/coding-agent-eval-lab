from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agentlab.agents.base import AgentAdapter
from agentlab.runner import EvaluationRun, run_task
from agentlab.tasks import EvalTask
from agentlab.terminal import ProgressBar


AgentFactory = Callable[[bool], AgentAdapter]
TrialRunner = Callable[[EvalTask, AgentFactory, Path, bool, int], EvaluationRun]


@dataclass(frozen=True)
class TrialExecutionConfig:
    runs_dir: Path
    trials: int = 1
    jobs: int = 1
    agent_name: str = ""
    manual_parallel_allowed: bool = False


def execute_trials(
    task: EvalTask,
    agent_factory: AgentFactory,
    config: TrialExecutionConfig,
    trial_runner: TrialRunner | None = None,
) -> list[EvaluationRun]:
    _validate_config(config)
    trial_runner = trial_runner or _run_single_trial
    runs_dir = Path(config.runs_dir)
    jobs = min(config.jobs, config.trials)

    if jobs == 1:
        evaluations = []
        for trial_index in range(config.trials):
            if config.trials > 1:
                print(f"Starting trial {trial_index + 1}/{config.trials}...")
            evaluations.append(
                trial_runner(
                    task,
                    agent_factory,
                    runs_dir,
                    True,
                    trial_index,
                )
            )
        return evaluations

    print(f"Starting {config.trials} trials with {jobs} jobs...")
    indexed_evaluations = []
    failures = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        future_indexes = {}
        for trial_index in range(config.trials):
            future = executor.submit(
                trial_runner,
                task,
                agent_factory,
                runs_dir,
                False,
                trial_index,
            )
            future_indexes[future] = trial_index

        progress = ProgressBar("Trials")
        pending = set(future_indexes)
        while pending:
            done, pending = wait(
                pending,
                timeout=progress.interval_seconds,
                return_when=FIRST_COMPLETED,
            )
            if not done:
                progress.update(f"waiting for {len(pending)} trial(s)")
                continue

            for future in done:
                trial_index = future_indexes[future]
                trial_label = f"trial {trial_index + 1}/{config.trials}"
                try:
                    evaluation = future.result()
                except Exception as exc:
                    failures.append(f"{trial_label}: {exc}")
                    continue

                indexed_evaluations.append((trial_index, evaluation))
        progress.finish("all trials finished")

    if failures:
        raise RuntimeError(
            "parallel trial failure(s): "
            + "; ".join(str(failure) for failure in failures)
        )

    return [
        evaluation
        for _trial_index, evaluation in sorted(
            indexed_evaluations,
            key=lambda indexed: indexed[0],
        )
    ]


def _validate_config(config: TrialExecutionConfig) -> None:
    if config.trials < 1:
        raise RuntimeError("--trials must be at least 1")
    if config.jobs < 1:
        raise RuntimeError("--jobs must be at least 1")
    if (
        config.agent_name == "manual"
        and not config.manual_parallel_allowed
        and config.jobs > 1
    ):
        raise RuntimeError("parallel manual trials require --no-pause")


def _run_single_trial(
    task: EvalTask,
    agent_factory: AgentFactory,
    runs_dir: Path,
    show_agent_progress: bool,
    trial_index: int,
) -> EvaluationRun:
    del trial_index
    agent = agent_factory(show_agent_progress)
    return run_task(task, agent, runs_dir)
