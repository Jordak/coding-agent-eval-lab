# Coding Agent Eval Lab

A reproducible evaluation harness for running coding-agent trials on realistic
software engineering tasks, grading their outcomes, classifying failure modes,
and producing model-quality reports.

This project is intentionally about evaluation infrastructure, not another chat
wrapper. It keeps the key evaluation concerns separate:

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

- Human-editable task bundles with YAML source and generated Markdown cards.
- `agentlab task validate` for schema checks.
- Starter task bundles under `tasks/starter/`.
- `agentlab run --agent manual --task ...` for one manual trial.
- Git checkout preparation, configured command execution, diff capture, and
  Markdown/JSON trial artifacts.
- Codex CLI and manual agent adapters.
- Multi-trial execution and pass@k/pass^k summaries.
- Human review labels using the failure taxonomy.
- Standard-library unit tests.

## Quick Start

Validate the starter task:

```bash
python3 -m agentlab task validate tasks/starter
```

Verify a task's reference artifact:

```bash
python3 -m agentlab task verify-reference tasks/starter/2048-advanced-snake-params-001
```

Write positive-control reference artifacts next to the task bundle:

```bash
python3 -m agentlab task verify-reference \
  --write-artifacts \
  tasks/starter/2048-advanced-snake-params-001
```

Run the self-tests:

```bash
python3 -m unittest discover
```

Run a real task through the manual adapter once its `repo` and `commit` point to
an accessible Git repository:

```bash
python3 -m agentlab run --agent manual --task path/to/task-bundle
```

The manual adapter pauses after workspace setup so a human can edit the cloned
repo. Press Enter in the terminal when edits are complete; the harness will then
capture the diff and run the task graders. Use `--no-pause` for a
negative-control trial where the manual adapter intentionally changes nothing.

Run a task through Codex CLI:

```bash
python3 -m agentlab run --agent codex --task tasks/starter/2048-advanced-snake-params-001
```

Run multiple independent trials:

```bash
python3 -m agentlab run \
  --agent codex \
  --trials 5 \
  --task tasks/starter/2048-advanced-snake-params-001
```

Useful Codex options:

```bash
python3 -m agentlab run \
  --agent codex \
  --codex-model gpt-5.2 \
  --codex-timeout-seconds 1800 \
  --task tasks/starter/2048-advanced-snake-params-001
```

The Codex adapter stores `codex-events.jsonl`, `codex-last-message.md`,
`transcript.md`, `diff.patch`, `report.md`, and `result.json` in the run
directory.

Reference verification uses the same report/result shape, marked with
`trial_kind: reference_verification`, and writes `reference-report.md`,
`reference-result.json`, and `reference.diff` when `--write-artifacts` is used.

List trials that have machine-readable metadata:

```bash
python3 -m agentlab trials list
```

Summarize trials by suite, task, agent harness, and model:

```bash
python3 -m agentlab trials summarize
```

`pass@k` means at least one trial in the group passed. `pass^k` means every trial
in the group passed.

Attach a human review label to a trial:

```bash
python3 -m agentlab review --trial latest --label success_clean --note "Focused one-line fix; graders pass."
```

The first real project task is:

```bash
python3 -m agentlab task validate tasks/starter/2048-advanced-snake-params-001
```

Regenerate task cards and suite indexes after changing task metadata or
reference artifacts:

```bash
python3 .agents/skills/task-card/scripts/render_task_cards.py tasks
```

Enable the repo-local pre-commit hook:

```bash
git config core.hooksPath .githooks
```

The hook fails commits when generated task cards or suite indexes drift from
`task.yaml`, and it validates all task bundles.

## MVP Path

1. Validate task bundles, including suite/type/reference-artifact metadata.
2. Create isolated workspaces from task repos and commits.
3. Add a manual adapter that lets a human edit the checkout for positive-control trials.
4. Capture diffs and command results.
5. Generate a Markdown report.
6. Add Cursor SDK, Claude Code, and Codex CLI adapters.

See [CONTEXT.md](CONTEXT.md) for project vocabulary,
[docs/design.md](docs/design.md) for architecture notes,
[docs/adr/](docs/adr/) for accepted architectural decisions,
[docs/anthropic-eval-principles.md](docs/anthropic-eval-principles.md) for the
terminology and practices this project follows,
[docs/failure-taxonomy.md](docs/failure-taxonomy.md) for the initial review
taxonomy, and [docs/runtime-accountability.md](docs/runtime-accountability.md)
for open work around model identity, account context, token usage, and cost. See
[docs/first-eval.md](docs/first-eval.md) for the first completed
positive/negative control evaluation.
