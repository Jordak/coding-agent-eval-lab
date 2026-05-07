# Coding Agent Eval Lab

A reproducible evaluation harness for running coding-agent trials on realistic
software engineering tasks, grading their outcomes, classifying failure modes,
and producing model-quality reports.

This project is intentionally about evaluation infrastructure, not another chat
wrapper. It keeps four concerns separate:

- **Task**: a single test case with repository, commit, prompt, environment, and
  success criteria.
- **Trial**: one attempt at a task by an agent harness.
- **Agent harness / scaffold**: Cursor Agent, Claude Code, Codex CLI, Aider,
  manual, etc.
- **Underlying model**: Claude, GPT, Gemini, or another model.
- **Grader**: tests, static checks, human review, LLM judge, and taxonomy.
- **Outcome**: the final environment state, including patch and grader results.

## Current Status

The first scaffold supports:

- Human-editable YAML task files.
- `agentlab task validate` for schema checks.
- A starter task file under `tasks/starter/`.
- `agentlab run --agent manual --task ...` for one manual trial.
- Git checkout preparation, configured command execution, diff capture, and a
  Markdown trial report.
- Standard-library unit tests.

## Quick Start

Validate the starter task:

```bash
python3 -m agentlab task validate "tasks/starter/*.yaml"
```

Run the self-tests:

```bash
python3 -m unittest discover
```

Run a real task through the manual adapter once its `repo` and `commit` point to
an accessible Git repository:

```bash
python3 -m agentlab run --agent manual --task path/to/task.yaml
```

The manual adapter pauses after workspace setup so a human can edit the cloned
repo. Press Enter in the terminal when edits are complete; the harness will then
capture the diff and run the task graders. Use `--no-pause` for a
negative-control trial where the manual adapter intentionally changes nothing.

Run a task through Codex CLI:

```bash
python3 -m agentlab run --agent codex --task tasks/starter/2048_advanced_snake_params_001.yaml
```

Useful Codex options:

```bash
python3 -m agentlab run \
  --agent codex \
  --codex-model gpt-5.2 \
  --codex-timeout-seconds 1800 \
  --task tasks/starter/2048_advanced_snake_params_001.yaml
```

The Codex adapter stores `codex-events.jsonl`, `codex-last-message.md`,
`transcript.md`, `diff.patch`, `report.md`, and `result.json` in the run
directory.

List trials that have machine-readable metadata:

```bash
python3 -m agentlab trials list
```

Attach a human review label to a trial:

```bash
python3 -m agentlab review --trial latest --label success_clean --note "Focused one-line fix; graders pass."
```

The first real project task is:

```bash
python3 -m agentlab task validate tasks/starter/2048_advanced_snake_params_001.yaml
```

## MVP Path

1. Validate task definitions, including suite/type/reference-solution metadata.
2. Create isolated workspaces from task repos and commits.
3. Add a manual adapter that lets a human edit the checkout for positive-control trials.
4. Capture diffs and command results.
5. Generate a Markdown report.
6. Add Cursor SDK, Claude Code, and Codex CLI adapters.

See [docs/design.md](docs/design.md) for architecture notes,
[docs/anthropic-eval-principles.md](docs/anthropic-eval-principles.md) for the
terminology and practices this project follows,
[docs/failure-taxonomy.md](docs/failure-taxonomy.md) for the initial review
taxonomy, and [docs/runtime-accountability.md](docs/runtime-accountability.md)
for open work around model identity, account context, token usage, and cost. See
[docs/first-eval.md](docs/first-eval.md) for the first completed
positive/negative control evaluation.
