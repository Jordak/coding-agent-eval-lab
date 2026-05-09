# ADR 0007: Exclude Invalid Trials From Capability Summaries

Status: Accepted

Date: 2026-05-08

## Context

Some stored trials are useful evidence but unfair capability measurements. Early
Click runs failed because task-environment configuration was wrong, not because
the agent harness produced bad patches. Counting those runs in pass rate,
pass@k, or pass^k would make the summary less truthful while deleting them would
hide useful diagnostic evidence.

## Decision

Keep every trial artifact append-only, but attach explicit trial-validity
metadata during human review:

- `valid`: the trial counts in fair capability summaries.
- `excluded`: the trial remains inspectable but does not count in fair pass
  metrics or median outcome metrics.

Excluded trials must record one exclusion reason: `dependency_issue`,
`eval_harness_error`, `setup_error`, `operator_error`, `invalid_task`, or
`unknown`.

`agentlab trials summarize` reports total trials, fair trials, excluded trials,
fair-trial pass rate, pass@k, pass^k, review labels for fair trials, and
exclusion-reason counts for excluded trials.

## Consequences

- Capability reports can separate "the agent harness failed" from "the
  evaluation harness or task setup was invalid" without losing raw evidence.
- Exclusions require an explicit human-review judgment and are visible in
  summaries.
- Aggregate metrics are scoped to fair trials only, so reports must mention
  excluded-trial counts when interpreting reliability.
