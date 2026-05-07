# Anthropic-Aligned Eval Principles

This project follows the terminology and design guidance from Anthropic's
January 2026 post, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

## Terminology

- **Task**: one test case with defined inputs and success criteria.
- **Trial**: one attempt at a task by an agent harness. Because agent behavior is
  non-deterministic, publishable comparisons should run multiple trials per task.
- **Grader**: logic that scores an aspect of performance. Code-based graders are
  the default for coding tasks; model-based and human graders are added when they
  provide signal that deterministic checks cannot.
- **Assertion**: an individual check inside a grader, such as a command that must
  exit successfully.
- **Transcript / trace / trajectory**: the record of the trial, including agent
  outputs, tool calls, command output, and intermediate state.
- **Outcome**: the final environment state after the trial. For coding tasks, the
  core outcome is the resulting patch plus whether deterministic graders pass.
- **Evaluation harness**: this project. It prepares environments, invokes agent
  harnesses, captures traces/outcomes, runs graders, and aggregates results.
- **Agent harness / scaffold**: the system being evaluated together with its
  model, such as Codex CLI, Claude Code, Cursor Agent, or the manual adapter.
- **Evaluation suite**: a collection of tasks designed to measure a capability or
  regression surface.

## Practices We Aim To Follow

- Start from real failures and manual checks, not synthetic puzzles alone.
- Keep tasks unambiguous enough that two domain experts would reach the same
  pass/fail verdict.
- Maintain a reference solution for each real task to prove the task is solvable
  and the graders are configured correctly.
- Prefer deterministic code-based graders for coding correctness.
- Grade the outcome first; avoid over-constraining the exact path or tool order
  unless tool behavior is the thing under evaluation.
- Use transcript review to check whether failures are fair and whether graders
  rejected a valid solution.
- Track capability suites separately from regression suites.
- Run multiple trials when comparing non-deterministic agents, then report
  pass@k or pass^k depending on whether the product values one successful attempt
  or consistency across attempts.
- Keep environments isolated so shared state does not create correlated failures
  or inflate performance.
- Add model-based graders only with clear rubrics and human calibration.

## Project Conventions

- CLI subcommand `run` executes one **trial**.
- `result.json` includes both legacy `run_id` and preferred `trial_id`.
- Existing `runs` commands remain for compatibility; new docs should prefer
  `trials`.
- YAML task files should set `suite`, `eval_type`, and `reference_solution` for
  real tasks.
- Reports use "code-based graders" and "assertions" for deterministic commands.
