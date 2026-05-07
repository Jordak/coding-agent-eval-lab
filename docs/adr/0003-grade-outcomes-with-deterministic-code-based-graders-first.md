# ADR 0003: Grade Outcomes With Deterministic Code-Based Graders First

Status: Accepted

Date: 2026-05-07

## Context

The project follows Anthropic-aligned eval practice: grade the final outcome
first and avoid over-constraining the exact agent path unless path behavior is
the thing being evaluated.

## Decision

Use deterministic code-based graders as the default grading mechanism for early
coding tasks.

Task files may define setup, baseline, target, and post-change assertions as
commands. The runner captures command results, final diff, changed files, and
score notes, then writes those outcomes to `report.md` and `result.json`.

Transcript review and human labels supplement outcome grading. Model-based
graders should be added only when they provide signal that deterministic checks
cannot capture and have a clear rubric.

## Consequences

- Early trials are reproducible, cheap, and easy to debug.
- The harness can support positive and negative controls for each task.
- Some patch-quality concerns still require human review labels until richer
  graders exist.
- Tool-call and transcript graders remain optional and targeted.
