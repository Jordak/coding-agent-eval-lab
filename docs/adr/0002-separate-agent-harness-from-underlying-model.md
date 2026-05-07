# ADR 0002: Separate Agent Harness From Underlying Model

Status: Accepted

Date: 2026-05-07

## Context

Coding-agent results are easy to misread when the agent product and model are
collapsed into a single label. For example, a Codex CLI trial measures the Codex
CLI harness as configured locally, and the selected model may be explicit,
implicit, or unknown.

## Decision

Represent agent harness and underlying model as separate dimensions.

- `agent_name` identifies the harness or scaffold, such as `manual` or `codex`.
- `model_name` records the explicit model when known.
- Reports and summaries group by agent harness and model separately.
- Runtime accountability gaps belong in `docs/runtime-accountability.md` until
  the harness can capture exact model, account, token, and cost metadata.

## Consequences

- Early results are honest about what was actually measured.
- Model-vs-model comparisons require explicit model configuration and runtime
  metadata before they are publishable.
- New adapters should expose model identity when their harness makes it
  available.
