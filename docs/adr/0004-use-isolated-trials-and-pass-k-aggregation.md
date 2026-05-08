# ADR 0004: Use Isolated Trials And pass@k/pass^k Aggregation

Status: Accepted

Date: 2026-05-07

## Context

Agent behavior is non-deterministic. A single successful or failed trial is
useful for debugging, but it is not enough to characterize reliability.

## Decision

Each `agentlab run` invocation executes one or more independent trials. Every
trial receives its own run directory and isolated workspace checkout. Multiple
trials may run concurrently when the caller passes `--jobs N`, but aggregation
still treats each trial as an independent attempt.

For multi-trial summaries, group stored results by evaluation suite, eval type,
task, agent harness, and model. Report:

- pass rate: passed fair trials divided by total fair trials
- pass@k: whether at least one fair trial in the group passed
- pass^k: whether every fair trial in the group passed

See [ADR 0007](0007-exclude-invalid-trials-from-capability-summaries.md) for
trial-validity metadata and excluded-trial handling.

## Consequences

- The project can evaluate both "can it eventually solve this?" and "does it
  solve this consistently?"
- Trial storage remains append-only and inspectable.
- Summary statistics are meaningful only when grouped trials share comparable
  task, harness, model, and runtime configuration.
