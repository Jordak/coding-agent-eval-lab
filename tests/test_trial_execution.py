import contextlib
import io
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from agentlab.trial_execution import TrialExecutionConfig, execute_trials


class TrialExecutionTest(unittest.TestCase):
    def test_single_trial_uses_agent_progress(self):
        progress_values = []

        def agent_factory(show_progress):
            progress_values.append(show_progress)
            return SimpleNamespace(name="codex")

        def trial_runner(task, agent_factory, runs_dir, show_agent_progress, index):
            agent_factory(show_agent_progress)
            return _evaluation(runs_dir, index)

        with tempfile.TemporaryDirectory() as temp:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                evaluations = execute_trials(
                    SimpleNamespace(id="task"),
                    agent_factory,
                    TrialExecutionConfig(
                        runs_dir=Path(temp),
                        trials=1,
                        jobs=1,
                        agent_name="codex",
                    ),
                    trial_runner=trial_runner,
                )

        self.assertEqual(len(evaluations), 1)
        self.assertEqual(progress_values, [True])
        self.assertEqual(stdout.getvalue(), "")

    def test_repeated_trials_run_serially_in_order(self):
        trial_indexes = []

        def agent_factory(show_progress):
            return SimpleNamespace(name="codex", show_progress=show_progress)

        def trial_runner(task, agent_factory, runs_dir, show_agent_progress, index):
            agent = agent_factory(show_agent_progress)
            self.assertTrue(agent.show_progress)
            trial_indexes.append(index)
            return _evaluation(runs_dir, index)

        with tempfile.TemporaryDirectory() as temp:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                evaluations = execute_trials(
                    SimpleNamespace(id="task"),
                    agent_factory,
                    TrialExecutionConfig(
                        runs_dir=Path(temp),
                        trials=3,
                        jobs=1,
                        agent_name="codex",
                    ),
                    trial_runner=trial_runner,
                )

        self.assertEqual(trial_indexes, [0, 1, 2])
        self.assertEqual(
            [evaluation.run_dir.name for evaluation in evaluations],
            ["trial-0", "trial-1", "trial-2"],
        )
        self.assertIn("Starting trial 1/3...", stdout.getvalue())
        self.assertIn("Starting trial 3/3...", stdout.getvalue())

    def test_parallel_trials_preserve_result_order_and_disable_agent_progress(self):
        progress_values = []

        def agent_factory(show_progress):
            progress_values.append(show_progress)
            return SimpleNamespace(name="codex")

        def trial_runner(task, agent_factory, runs_dir, show_agent_progress, index):
            if index == 0:
                time.sleep(0.02)
            agent_factory(show_agent_progress)
            return _evaluation(runs_dir, index)

        with tempfile.TemporaryDirectory() as temp:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                evaluations = execute_trials(
                    SimpleNamespace(id="task"),
                    agent_factory,
                    TrialExecutionConfig(
                        runs_dir=Path(temp),
                        trials=3,
                        jobs=2,
                        agent_name="codex",
                    ),
                    trial_runner=trial_runner,
                )

        self.assertEqual(
            [evaluation.run_dir.name for evaluation in evaluations],
            ["trial-0", "trial-1", "trial-2"],
        )
        self.assertEqual(progress_values, [False, False, False])
        self.assertIn("Starting 3 trials with 2 jobs...", stdout.getvalue())

    def test_parallel_failure_reports_trial_label(self):
        def agent_factory(show_progress):
            return SimpleNamespace(name="codex")

        def trial_runner(task, agent_factory, runs_dir, show_agent_progress, index):
            agent_factory(show_agent_progress)
            if index == 1:
                raise RuntimeError("agent failed before artifact write")
            return _evaluation(runs_dir, index)

        with tempfile.TemporaryDirectory() as temp:
            stdout = io.StringIO()
            with self.assertRaisesRegex(
                RuntimeError,
                "parallel trial failure\\(s\\): trial 2/3: "
                "agent failed before artifact write",
            ):
                with contextlib.redirect_stdout(stdout):
                    execute_trials(
                        SimpleNamespace(id="task"),
                        agent_factory,
                        TrialExecutionConfig(
                            runs_dir=Path(temp),
                            trials=3,
                            jobs=2,
                            agent_name="codex",
                        ),
                        trial_runner=trial_runner,
                    )

    def test_parallel_manual_trials_require_no_pause(self):
        def agent_factory(show_progress):
            return SimpleNamespace(name="manual")

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(
                RuntimeError,
                "parallel manual trials require --no-pause",
            ):
                execute_trials(
                    SimpleNamespace(id="task"),
                    agent_factory,
                    TrialExecutionConfig(
                        runs_dir=Path(temp),
                        trials=2,
                        jobs=2,
                        agent_name="manual",
                        manual_parallel_allowed=False,
                    ),
                )


def _evaluation(runs_dir, index):
    run_dir = Path(runs_dir) / f"trial-{index}"
    return SimpleNamespace(
        agent_run=SimpleNamespace(agent_name="codex", error=None),
        run_dir=run_dir,
        report_path=run_dir / "report.md",
        result_path=run_dir / "result.json",
        score=SimpleNamespace(tests_passed=True),
    )


if __name__ == "__main__":
    unittest.main()
