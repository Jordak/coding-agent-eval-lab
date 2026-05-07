# ADR 0004: Use Isolated Trials And pass@k/pass^k Aggregation

Status: Accepted

Date: 2026-05-07

## Context

Agent behavior is non-deterministic. A single successful or failed trial is
useful for debugging, but it is not enough to characterize reliability.

## Decision

Each `agentlab run` invocation executes one or more independent trials. Every
trial receives its own run directory and isolated workspace checkout.

For multi-trial summaries, group stored results by evaluation suite, eval type,
task, agent harness, and model. Report:

- pass rate: passed trials divided by total trials
- pass@k: whether at least one trial in the group passed
- pass^k: whether every trial in the group passed

## Consequences

- The project can evaluate both "can it eventually solve this?" and "does it
  solve this consistently?"
- Trial storage remains append-only and inspectable.
- Summary statistics are meaningful only when grouped trials share comparable
  task, harness, model, and runtime configuration.
