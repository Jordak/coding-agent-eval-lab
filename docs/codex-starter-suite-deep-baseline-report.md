# Codex Starter Suite Deep Baseline Report

Date: 2026-05-09

Note: this nine-task report is superseded for Issue #10 closeout by
[`docs/codex-starter-suite-12-task-baseline-report.md`](codex-starter-suite-12-task-baseline-report.md),
which extends the selected fair evidence set to twelve tasks and 60 Codex
trials.

## Scope

This report covers Codex CLI as the local `codex` agent harness on the nine-task
`starter-coding` suite selected for Issue #10. It is evidence-scoped: these are
observations about this local harness configuration and task set, not global
claims about Codex or any underlying model.

The selected evidence set is tracked at
`evidence-sets/codex-starter-suite-deep-baseline-2026-05-09.json`. The generated
capability evidence digest is
`reports/codex-starter-suite-deep-baseline-2026-05-09-digest.md`, and the
overnight HTML dashboard is
`reports/codex-starter-suite-overnight-report-2026-05-09.html`.

## Summary

The selected fair evidence set contains 45 Codex trials: five fair trials for
each of the nine starter tasks. All 45 selected fair trials passed their
deterministic graders.

| Task | Fair Trials | Passes | Review Summary |
| --- | ---: | ---: | --- |
| `2048-advanced-snake-params-001` | 5 | 5 | `success_clean:5` |
| `click-help-option-refactor-001` | 5 | 5 | `success_clean:4`, `resource_inefficient:1`; four successes also carry secondary `resource_inefficient` |
| `click-default-map-nargs-001` | 5 | 5 | `success_clean:5` |
| `click-help-shadowed-option-001` | 5 | 5 | `success_clean:5` |
| `click-should-strip-ansi-tests-001` | 5 | 5 | `success_clean:4`, `success_messy:1` |
| `datawrapper-mcp-docker-requirements-001` | 5 | 5 | `success_clean:5` |
| `httpx-verify-false-client-cert-001` | 5 | 5 | `success_clean:5` |
| `react-tabs-selected-focus-overlay-001` | 5 | 5 | `success_clean:3`, `resource_inefficient:2` |
| `todomvc-toggle-all-checkbox-001` | 5 | 5 | `success_clean:5` |

## Interpretation

Codex was consistently able to produce grader-passing patches across this
starter suite. The strongest narrow claim supported here is that, under the
local `codex` harness and these deterministic task contracts, Codex solved all
nine starter tasks across five fair trials per task.

The evidence is not all equally clean. The help-option refactor task passed in
all five fair trials, but every selected trial was resource-heavy enough to
matter when interpreting usefulness. Two React Tabs trials also passed with tiny
patches but disproportionate elapsed time. One Click ANSI test-only trial passed
while making a less clean coverage change by deleting an existing
Jupyter-specific smoke test.

Excluded invalid artifacts remain outside this selected fair set. In particular,
five earlier `click-default-map-nargs-001` setup failures are marked
`setup_error`, and one earlier `click-help-shadowed-option-001` failure is
marked `eval_harness_error`. They are useful diagnostics for the evaluation
harness and task environment, but they do not count in fair capability metrics.

## Recommendation

Treat this as a strong starter-suite baseline, not a broad capability report.
The next high-leverage PRD work is to add more varied tasks before broadening
claims: more application code, frontend component work, dependency/setup tasks,
test-only tasks, refactors, and deterministic real-issue regressions outside the
current Click-heavy slice.
