# Coding Agent Eval Lab

A reproducible evaluation harness for running coding agents on realistic software
engineering tasks, scoring their patches, classifying failure modes, and producing
model-quality reports.

This project is intentionally about evaluation infrastructure, not another chat
wrapper. It keeps four concerns separate:

- **Task**: repository, commit, prompt, setup, and success criteria.
- **Agent runtime**: Cursor Agent, Claude Code, Codex CLI, Aider, manual, etc.
- **Underlying model**: Claude, GPT, Gemini, or another model.
- **Evaluator**: tests, static checks, human review, LLM judge, and taxonomy.

## Current Status

The first scaffold supports:

- Human-editable YAML task files.
- `agentlab task validate` for schema checks.
- A starter task file under `tasks/starter/`.
- `agentlab run --agent manual --task ...` for proving the harness before SDK work.
- Git checkout preparation, configured command execution, diff capture, and a
  Markdown report.
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
capture the diff and run the task checks. Use `--no-pause` for a negative-control
run where the manual adapter intentionally changes nothing.

List runs that have machine-readable metadata:

```bash
python3 -m agentlab runs list
```

The first real project task is:

```bash
python3 -m agentlab task validate tasks/starter/2048_advanced_snake_params_001.yaml
```

## MVP Path

1. Validate task definitions.
2. Create isolated workspaces from task repos and commits.
3. Add a manual adapter that lets a human edit the checkout.
4. Capture diffs and command results.
5. Generate a Markdown report.
6. Add Cursor SDK, Claude Code, and Codex CLI adapters.

See [docs/design.md](docs/design.md) for architecture notes and
[docs/failure-taxonomy.md](docs/failure-taxonomy.md) for the initial review
taxonomy.
