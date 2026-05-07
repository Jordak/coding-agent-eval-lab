# ADR 0005: Use Evidence-Based Reporting

Status: Accepted

Date: 2026-05-07

## Context

Agent capability reports could easily drift into leaderboard-style or global
model claims that the evaluated evidence does not support.

## Decision

Reports should make evidence-based claims scoped to the evaluated tasks, agent
harness configuration, runtime conditions, graders, and observed trials.

Prefer statements like:

> Under these conditions, this Codex CLI configuration passed 4/5 trials on this
> task and failures mostly showed specification misreads.

Avoid statements like:

> Codex is better than another agent harness.

or:

> This proves the model has the capability globally.

## Consequences

- Reports remain useful without overgeneralizing.
- Comparisons require shared suites, comparable harness configurations, and
  explicit caveats.
- Solo developers get practical evidence rather than false certainty.
