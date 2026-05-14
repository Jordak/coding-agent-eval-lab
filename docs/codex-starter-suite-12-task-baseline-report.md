# Codex Starter Suite 12-Task Baseline Report

Date: 2026-05-13

## Scope

This report covers Codex CLI as the local `codex` agent harness on the
twelve-task `starter-coding` suite selected for
[Issue #10](https://github.com/Jordak/coding-agent-eval-lab/issues/10). It is
evidence-scoped: these are observations about this local harness configuration,
task set, deterministic graders, and human review protocol, not global claims
about Codex or any underlying model.

The selected evidence set is tracked at
[`evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json`](../evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json).
The generated capability evidence digest is
[`reports/codex-starter-suite-12-task-baseline-2026-05-11-digest.md`](../reports/codex-starter-suite-12-task-baseline-2026-05-11-digest.md).
Recovered model attribution is documented in
[`docs/codex-starter-suite-12-task-model-attribution.md`](codex-starter-suite-12-task-model-attribution.md).

The evaluated runtime metadata recovered from local Codex thread state is:

- Agent harness: `codex`
- Model: `gpt-5.5`
- Reasoning effort: `xhigh`
- Model source: `local_codex_state`
- Provider: `openai`

The model and effort metadata were recovered from Jordan's local Codex state
database. The saved `codex-events.jsonl` streams expose thread IDs and usage, but
not portable event-derived model identity for these historical runs.

## Summary

The selected fair evidence set contains 60 Codex trials: five fair trials for
each of twelve starter-suite tasks. All 60 selected fair trials passed their
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
| `prettier-duplicate-dangling-comments-001` | 5 | 5 | `success_clean:5`; all five successes carry secondary `resource_inefficient` |
| `react-tabs-selected-focus-overlay-001` | 5 | 5 | `success_clean:3`, `resource_inefficient:2` |
| `remotion-audio-context-autoplay-muted-001` | 5 | 5 | `success_clean:5`; all five successes carry secondary `resource_inefficient` |
| `todomvc-toggle-all-checkbox-001` | 5 | 5 | `success_clean:5` |
| `vite-deno-workspace-root-001` | 5 | 5 | `success_clean:5` |

Every aggregate task row has pass rate `1.00`, pass@k `1.00`, and pass^k
`1.00` across the selected fair trials.

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
reader cares about latency, token budget, review burden, or cost.

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
review burden. Cost is still not interpreted here because selected result rows
record cost as `unknown`.

Finally, deterministic grader success does not prove that every patch is ideal.
The human review labels are part of the evidence precisely because a
grader-passing patch can still be resource-heavy, messy, over-edited, or risky.

## Recommendation

Treat this as a strong Codex starter-suite baseline and a clean closeout
artifact for Issue #10. The evidence supports saying that this Codex CLI
configuration was highly reliable on these twelve bounded maintenance tasks
under fair trial conditions.

The next product step should not be to broaden the Codex claim further from this
same evidence. It should be to run a comparable Claude Code baseline on the same
starter-suite tasks, then write a separate comparison report that references
both baselines and keeps model, effort, harness, and review caveats visible.
