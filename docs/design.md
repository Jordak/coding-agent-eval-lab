# Design Notes

## Core Entities

The lab separates task design, agent runtime, underlying model, and evaluation.
This keeps reports honest when, for example, Cursor uses Claude as a model but
still runs inside Cursor's agent harness.

## MVP Architecture

- `agentlab.tasks` loads and validates task YAML.
- `agentlab.workspace` will prepare clean checkouts for each task.
- `agentlab.agents` defines runtime adapters.
- `agentlab.runner` will coordinate workspace setup, agent execution, scoring,
  and artifact capture.
- `agentlab.reporting` will render Markdown and later static HTML reports.

## Agent Adapters

The manual adapter is the positive/negative-control baseline. It can pause for a
human edit or run with `--no-pause` to intentionally make no changes.

The Codex CLI adapter uses `codex exec` non-interactively against the isolated
workspace. It captures JSONL events, the final agent message, the resulting diff,
and the same deterministic checks as every other adapter.

## Early Constraint

The first implementation avoids mandatory third-party dependencies so the lab is
usable immediately in a fresh local folder. If PyYAML is installed, task loading
uses it. Otherwise, a small fallback parser supports the task-schema subset used
by this project.
