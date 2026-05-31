# Codex Starter Suite 12-Task Baseline Report

Date: 2026-05-13

## Scope

This report answers a narrow question: how did Codex CLI perform on a small
suite of realistic starter maintenance tasks? The answer is scoped to this
twelve-task `starter-coding` suite, the local `codex` agent harness, the
deterministic graders, and the human review labels captured for these runs.

It should not be read as a universal Codex ranking or as a guarantee about how
Codex will behave on every software project. It is a practical evidence summary
for readers who want to understand how Codex did on these tasks and what caveats
showed up in review.

The selected evidence set is tracked at
[`evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json`](../../evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json).
The generated capability evidence digest is
[`digest.md`](digest.md).
Recovered model attribution is documented in
[`model-attribution.md`](model-attribution.md).

The evaluated runtime metadata recovered from local Codex thread state is:

- Agent harness: `codex`
- Model: `gpt-5.5`
- Reasoning effort: `xhigh`
- Model source: `local_codex_state`
- Provider: `openai`

The model and effort metadata were recovered from the local Codex state
database. The saved `codex-events.jsonl` streams expose thread IDs and usage, but
not portable event-derived model identity for these historical runs.

## Summary

The selected fair evidence set contains 60 Codex trials: five fair trials for
each of twelve starter-suite tasks. All 60 selected fair trials passed their
deterministic graders.

| Task | Fair Trials | Passes | Min Tokens | Max Tokens | Mean Tokens | Median Tokens | Review Summary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| [2048-advanced-snake-params-001](../../tasks/starter/2048-advanced-snake-params-001/task-card.md) | 5 | 5 | 268,240 | 411,238 | 366,351 | 381,095 | `success_clean:5` |
| [click-help-option-refactor-001](../../tasks/starter/click-help-option-refactor-001/task-card.md) | 5 | 5 | 943,087 | 1,457,954 | 1,271,460 | 1,346,975 | `success_clean:4`, `resource_inefficient:1`; four successes also carry secondary `resource_inefficient` |
| [click-default-map-nargs-001](../../tasks/starter/click-default-map-nargs-001/task-card.md) | 5 | 5 | 1,033,731 | 2,633,274 | 1,439,604 | 1,172,964 | `success_clean:5` |
| [click-help-shadowed-option-001](../../tasks/starter/click-help-shadowed-option-001/task-card.md) | 5 | 5 | 871,139 | 1,388,262 | 1,139,998 | 1,251,156 | `success_clean:5` |
| [click-should-strip-ansi-tests-001](../../tasks/starter/click-should-strip-ansi-tests-001/task-card.md) | 5 | 5 | 173,833 | 263,159 | 214,517 | 218,181 | `success_clean:4`, `success_messy:1` |
| [datawrapper-mcp-docker-requirements-001](../../tasks/starter/datawrapper-mcp-docker-requirements-001/task-card.md) | 5 | 5 | 96,750 | 160,424 | 115,318 | 99,050 | `success_clean:5` |
| [httpx-verify-false-client-cert-001](../../tasks/starter/httpx-verify-false-client-cert-001/task-card.md) | 5 | 5 | 337,334 | 492,890 | 422,981 | 454,487 | `success_clean:5` |
| [prettier-duplicate-dangling-comments-001](../../tasks/starter/prettier-duplicate-dangling-comments-001/task-card.md) | 5 | 5 | 1,266,853 | 2,255,681 | 1,879,731 | 2,040,878 | `success_clean:5`; all five successes carry secondary `resource_inefficient` |
| [react-tabs-selected-focus-overlay-001](../../tasks/starter/react-tabs-selected-focus-overlay-001/task-card.md) | 5 | 5 | 86,318 | 133,722 | 104,893 | 108,012 | `success_clean:3`, `resource_inefficient:2` |
| [remotion-audio-context-autoplay-muted-001](../../tasks/starter/remotion-audio-context-autoplay-muted-001/task-card.md) | 5 | 5 | 544,950 | 1,066,964 | 798,024 | 876,546 | `success_clean:5`; all five successes carry secondary `resource_inefficient` |
| [todomvc-toggle-all-checkbox-001](../../tasks/starter/todomvc-toggle-all-checkbox-001/task-card.md) | 5 | 5 | 140,101 | 374,510 | 221,222 | 199,938 | `success_clean:5` |
| [vite-deno-workspace-root-001](../../tasks/starter/vite-deno-workspace-root-001/task-card.md) | 5 | 5 | 303,865 | 453,661 | 391,216 | 396,890 | `success_clean:5` |

Every aggregate task row has pass rate `1.00`, pass@k `1.00`, and pass^k
`1.00` across the selected fair trials.

Token columns report per-trial `input_tokens + output_tokens` after applying
the same event backfills used by the generated digest. Cached-input and
reasoning-token details are available in the linked digest, but are not added
separately here to avoid double counting.

With the current token-normalized outcome semantics, all 60 trials are verified
results because every selected valid trial passed deterministic graders. The
selected set has 56 accepted results: valid grader-passing trials whose primary
human review label is `success_clean`. The four non-accepted verified results
are three primary `resource_inefficient` outcomes and one `success_messy`
outcome. Across the selected set, Codex used 41,826,575 reported
input-plus-output tokens, or about 697,110 per verified result and 746,903 per
accepted result. Cached-input and reasoning-output buckets totaled 38,018,304
and 186,585 respectively; those remain separate because they are not comparable
to non-cached input/output tokens as a single cost unit.

## Interpretation

Codex was consistently able to produce grader-passing patches across this
starter suite. The strongest supported claim is narrow but useful: under the
local `codex` harness, using recovered `gpt-5.5` with `xhigh` reasoning effort,
Codex solved all twelve selected starter tasks across five fair trials per task.

The result is strongest for deterministic maintenance work with clear local
graders: CLI regressions, dependency/setup fixes, small application behavior
repairs, and focused JavaScript/TypeScript ecosystem regressions. The suite now
covers more than the earlier Click-heavy baseline by adding Prettier, Vite, and
Remotion tasks, alongside the existing Python, HTTPX, Datawrapper, React Tabs,
TodoMVC, and 2048 tasks.

The evidence is not equivalent to "Codex is always cheap or clean." Seventeen
of the 60 selected trials carry `resource_inefficient` either as the primary
label or as a secondary caveat. The most visible resource caveats appear on
`click-help-option-refactor-001`, `prettier-duplicate-dangling-comments-001`,
`react-tabs-selected-focus-overlay-001`, and
`remotion-audio-context-autoplay-muted-001`. These trials still passed their
graders, but pass rate alone would overstate the usefulness of the harness if a
reader cares about latency, token usage, or review burden.

There is also one `success_messy` trial on
`click-should-strip-ansi-tests-001`. That task still passed 5/5, but the review
label records that at least one passing patch was less clean than the others.

The selected evidence set has no excluded trials. Older invalid Codex artifacts
remain outside this fair set, including earlier setup or harness failures and an
earlier Vite run excluded after the task contract was tightened. Those artifacts
remain useful diagnostics for task and harness development, but they are not
counted in the 60-trial capability claim.

## Limitations

This report should not be read as a multi-harness comparison. It says nothing
about Claude Code, Cursor, GitHub Copilot, or other agent harnesses on the same
tasks.

This report should also not be read as a model-only evaluation. The measured
unit is the configured Codex CLI agent harness, including its terminal behavior,
tool use, local permissions, sandboxing, prompts, and recovered runtime model
metadata.

The selected runs used `xhigh` reasoning effort. That matters: a cheaper or
lower-effort Codex configuration might have different pass rates, latency, and
review burden. Token usage is reported above; billed cost is not interpreted
here because the stored Codex events captured token counts but no billed cost or
credit-consumption field.

Finally, deterministic grader success does not prove that every patch is ideal.
The human review labels are part of the evidence precisely because a
grader-passing patch can still be resource-heavy, messy, over-edited, or risky.

## Reader Takeaway

This is a strong result for Codex on this suite. It passed every selected fair
trial across twelve bounded maintenance tasks, including Python CLI regressions,
dependency/setup fixes, frontend behavior repairs, and JavaScript/TypeScript
ecosystem regressions.

The main caveat is efficiency, not correctness. Several tasks passed while
carrying `resource_inefficient` review labels, so a reader should treat Codex as
highly capable on these tasks but still worth monitoring for runtime, token
usage, and review burden.
