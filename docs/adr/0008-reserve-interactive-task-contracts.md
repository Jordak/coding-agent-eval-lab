# ADR 0008: Reserve Interactive Task Contracts

Status: Accepted

Date: 2026-05-08

## Context

The Solo Dev Starter Suite v1 is intentionally non-interactive. A trial should
start from a fixed prompt, run one agent harness attempt, and grade the final
outcome without a clarification loop.

Future suites may need tasks where asking follow-up questions is part of the
behavior being evaluated. Those tasks need a clear contract so question quality
can be reviewed without contaminating non-interactive capability metrics.

## Decision

Keep non-interactive tasks as the default. A task that omits interaction
metadata is interpreted as:

```yaml
interaction:
  mode: none
```

Reserve this future schema shape for interactive tasks, but do not implement it
in the v1 runner yet:

```yaml
interaction:
  mode: followup_allowed
  max_questions: 2
  answer_source:
    type: scripted
    path: followup-answers.md
  grading:
    followup_quality: human
```

`mode: none` means the agent harness should proceed from the fixed prompt.
`mode: followup_allowed` means the agent harness may ask bounded follow-up
questions before editing. The answer source must be deterministic for
publishable trials:
initially a scripted Markdown or JSON artifact committed with the task bundle.

Interactive trial evidence should capture:

- The follow-up questions asked, in order.
- The scripted answers returned.
- Whether the agent proceeded without using its full question budget.
- The final transcript, patch, grader outcomes, and normal outcome evidence.

Follow-up-question quality should be graded later with an explicit rubric. The
first likely rubric dimensions are relevance, necessity, specificity,
information gain, and whether the question blocks progress unnecessarily. This
can start as a human review field and later become a calibrated model-based
grader if the rubric proves stable.

Interactive tasks must be grouped separately from non-interactive tasks in
summaries, either by `interaction.mode` or by a dedicated suite/eval type. A
non-interactive suite summary must not mix in interactive trials because the
agent harness received different affordances.

## Consequences

- Current task behavior and all v1 starter tasks remain unchanged.
- Future interactive support has a named schema direction before implementation
  begins.
- Follow-up questions become first-class trial evidence instead of disappearing
  into a transcript.
- Pass-rate, pass@k, and pass^k summaries remain comparable because interactive
  and non-interactive trials are not aggregated together by accident.
