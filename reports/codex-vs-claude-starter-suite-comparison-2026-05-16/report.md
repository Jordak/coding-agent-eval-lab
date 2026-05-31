# Codex vs Claude Code Starter Suite Comparison

Date: 2026-05-16

Review status: reviewed and published.

## Scope

This report compares two completed Agent Eval Lab baselines on the same
twelve-task Solo Dev Starter Suite:

- Codex CLI baseline:
  [`reports/codex-starter-suite-12-task-baseline-2026-05-11/report.md`](../codex-starter-suite-12-task-baseline-2026-05-11/report.md)
- Claude Code baseline:
  [`reports/claude-code-starter-suite-baseline-2026-05-14/report.md`](../claude-code-starter-suite-baseline-2026-05-14/report.md)

Both baselines use selected fair evidence sets with five fair trials per task:

- Codex evidence set:
  [`evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json`](../../evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json)
- Claude Code evidence set:
  [`evidence-sets/claude-code-starter-suite-baseline-2026-05-14.json`](../../evidence-sets/claude-code-starter-suite-baseline-2026-05-14.json)

The comparison is scoped to these agent harness configurations, task prompts,
graders, local runtime conditions, selected trial artifacts, and human review
labels. It is not a universal ranking of Codex, Claude Code, OpenAI models,
Anthropic models, or coding agents in general.

## Configuration Caveat

The most important interpretive caveat is configuration asymmetry.

The Codex baseline used Codex CLI with recovered runtime metadata:

- Model: `gpt-5.5`
- Reasoning effort: `xhigh`
- Model source: local Codex state, documented in
  [`model-attribution.md`](../codex-starter-suite-12-task-baseline-2026-05-11/model-attribution.md)

The Claude Code baseline used Claude Code with event-derived runtime metadata:

- Model: `claude-haiku-4-5-20251001`
- Reasoning effort: not exposed as a comparable field
- Model source: Claude Code event stream
- Config note:
  [`readiness.md`](../claude-code-starter-suite-baseline-2026-05-14/readiness.md)

That means this is not a balanced "best OpenAI configuration vs best Anthropic
configuration" comparison. It is a comparison between a high-effort Codex CLI
configuration and a cheap proof-of-concept Claude Code configuration. At
readiness time, the Claude baseline intentionally used the smallest, cheapest
first-party Claude model verified for the local Claude Code account. A stronger
Claude model, lower-effort Codex model, or different
permission/turn configuration could produce different results.

This asymmetry should stay attached to every takeaway below. Where Codex looks
more reliable, the evidence supports "this high-effort Codex configuration was
more reliable on this suite," not "Codex is always better." Where Claude Code
looks cheaper or faster, the evidence supports "this Haiku baseline was lighter
under these conditions," not "Claude Code is always more efficient."

## Aggregate Result

| Baseline | Agent Harness Configuration | Fair Trials | Grader Passes | Accepted Results | Tasks At 5/5 | pass@5 By Task | pass^5 By Task | IO Tok / Verified | IO Tok / Accepted | Resource Evidence |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Codex CLI | `codex`, `gpt-5.5`, `xhigh` | 60 | 60 | 56 | 12/12 | 12/12 | 12/12 | 697,110 | 746,903 | Median trial duration about 173s; billed cost not captured |
| Claude Code | `claude`, `claude-haiku-4-5-20251001`, no comparable effort field | 60 | 53 | 5 | 10/12 | 11/12 | 10/12 | 14,815 | 157,034 | Median trial duration about 111s; recorded selected-set usage $16.35 |

Codex produced the stronger correctness result: 60 of 60 selected fair trials
passed deterministic graders, and every task reached 5/5. Claude Code produced
a useful but less uniform result: 53 of 60 selected fair trials passed, ten
tasks reached 5/5, one task reached 3/5, and one task reached 0/5.

The high-level difference is reliability, especially on tasks that require
precise test structure or subtle shared-state behavior. The high-level
efficiency story is less direct. Claude Code's selected fair set records a real
dollar cost and lower median duration, but Codex cost was not captured and the
two harnesses expose token/cache/reasoning metadata differently. Resource
signals are useful for caveats, but they are not enough to compute a fair
dollars-per-solved-task comparison. Reported input-plus-output tokens per
verified result provide a useful middle-ground resource signal, but they still
do not collapse cached-input, reasoning-output, and billing semantics into one
universal cost unit.

## Task Comparison

| Task | Codex CLI | Claude Code | Comparison Signal |
| --- | ---: | ---: | --- |
| [`2048-advanced-snake-params-001`](../../tasks/starter/2048-advanced-snake-params-001/task-card.md) | 5/5 | 5/5 | Both configurations handled the small Python behavior fix reliably. |
| [`click-default-map-nargs-001`](../../tasks/starter/click-default-map-nargs-001/task-card.md) | 5/5 | 5/5 | Both handled the Click regression; Claude had two reviewed successes with secondary `resource_inefficient` labels. |
| [`click-help-option-refactor-001`](../../tasks/starter/click-help-option-refactor-001/task-card.md) | 5/5 | 5/5 | Both passed consistently; Codex carried broader resource caveats, while Claude had one reviewed resource caveat. |
| [`click-help-shadowed-option-001`](../../tasks/starter/click-help-shadowed-option-001/task-card.md) | 5/5 | 5/5 | Both handled the shadowed-option help regression reliably. |
| [`click-should-strip-ansi-tests-001`](../../tasks/starter/click-should-strip-ansi-tests-001/task-card.md) | 5/5 | 0/5 | Strongest separation. Codex consistently produced grader-passing test coverage; Claude repeatedly produced valid `bad_local_fix` / `test_gap` failures. |
| [`datawrapper-mcp-docker-requirements-001`](../../tasks/starter/datawrapper-mcp-docker-requirements-001/task-card.md) | 5/5 | 5/5 | Both handled the deterministic dependency/setup task reliably. |
| [`httpx-verify-false-client-cert-001`](../../tasks/starter/httpx-verify-false-client-cert-001/task-card.md) | 5/5 | 5/5 | Both handled the HTTPX edge-case behavior task reliably. |
| [`prettier-duplicate-dangling-comments-001`](../../tasks/starter/prettier-duplicate-dangling-comments-001/task-card.md) | 5/5 | 5/5 | Both passed; both baselines record resource caveats, heavier on Codex. |
| [`react-tabs-selected-focus-overlay-001`](../../tasks/starter/react-tabs-selected-focus-overlay-001/task-card.md) | 5/5 | 5/5 | Both solved the frontend style/behavior task; Codex had two primary `resource_inefficient` labels. |
| [`remotion-audio-context-autoplay-muted-001`](../../tasks/starter/remotion-audio-context-autoplay-muted-001/task-card.md) | 5/5 | 3/5 | Codex was more consistent on the subtle shared `AudioContext` behavior; Claude often found the local muted-playback shape but missed the full shared-control contract twice. |
| [`todomvc-toggle-all-checkbox-001`](../../tasks/starter/todomvc-toggle-all-checkbox-001/task-card.md) | 5/5 | 5/5 | Both handled the frontend DOM/state task reliably. |
| [`vite-deno-workspace-root-001`](../../tasks/starter/vite-deno-workspace-root-001/task-card.md) | 5/5 | 5/5 | Both handled the Vite/Deno workspace-root regression reliably. |

The suite has ten tasks where the two evaluated configurations are
indistinguishable by deterministic pass count. The comparison signal comes from
the remaining two tasks and from review/resource caveats. Codex separated
itself on the tests-only Click task and the Remotion shared-state task. Claude
Code still solved most of the suite with the cheap Haiku configuration, which
is a meaningful practical signal even though it did not match Codex's
high-effort reliability.

## Human Review Signals

Codex review labels in the selected fair set:

- Primary labels: `success_clean:56`, `success_messy:1`,
  `resource_inefficient:3`
- Secondary labels: `resource_inefficient:14`

Claude Code review labels in the selected fair set:

- Primary labels: `success_clean:5`, `bad_local_fix:7`
- Secondary labels: `resource_inefficient:5`, `test_gap:7`

These label counts should not be read as a pure cleanliness leaderboard. The
Codex selected set records a primary review label for every selected trial. The
Claude Code selected set records labels most visibly on failures, first-fair
reviewed successes, and resource-heavy successes. That makes failure-mode
comparison useful, but it makes "clean success" counts less symmetric than the
deterministic grader table.

The strongest qualitative contrast is not that Codex never needed caveats.
Codex had resource-efficiency caveats on 17 selected trials and one messy
success. The sharper contrast is that Codex's caveats usually appeared on
passing patches, while Claude Code's largest caveats included seven
grader-failing patches: five on `click-should-strip-ansi-tests-001` and two on
`remotion-audio-context-autoplay-muted-001`.

## Resource Signals

The resource evidence supports caution, not a simple winner.

Codex:

- Median selected-trial duration was about 173 seconds.
- The selected fair set used 41,826,575 reported input-plus-output tokens:
  about 697,110 per verified result and 746,903 per accepted result.
- Cached-input and reasoning-output buckets totaled 38,018,304 and 186,585.
- Billed cost was not captured in the stored Codex results.
- Seventeen selected trials carried `resource_inefficient` as either a primary
  or secondary human review label.

Claude Code:

- Median selected-trial duration was about 111 seconds.
- The selected fair set recorded $16.35 in Claude Code usage.
- The selected fair set used 785,170 reported input-plus-output tokens: about
  14,815 per verified result and 157,034 per strict accepted result.
- Stored results captured 99,305,237 cached-input tokens. That is about
  1,873,684 cached-input tokens per verified result.
- Five selected trials carried secondary `resource_inefficient` labels.

The accepted-result comparison is less symmetric than the verified-result
comparison because the historical Claude review labels were not attached to
every passing trial. Under the current strict definition, accepted means
valid, grader-passing, and primary `success_clean`; that yields 56 accepted
Codex results and five accepted Claude results. Use that as a review-coverage
signal, not as a standalone quality ranking.

This is consistent with the configuration asymmetry: high-effort Codex produced
the stronger reliability result, while cheap Claude Code produced many correct
patches with lower observed wall-clock median and explicit low-dollar usage.
But the report should avoid claiming that Claude Code is categorically cheaper
or Codex is categorically more expensive. Codex cost was missing, token
accounting differs by harness, and a lower-effort Codex run or stronger Claude
run could change the shape.

## Interpretation

Under these evaluated conditions, Codex CLI with `gpt-5.5` and `xhigh`
reasoning effort was the more reliable configuration on the Solo Dev Starter
Suite. It passed every selected fair trial and had no task-level weak spot in
deterministic grader outcomes.

Claude Code with `claude-haiku-4-5-20251001` was still credible on this suite,
especially given that it was intentionally the cheap proof-of-concept baseline.
It solved ten of twelve tasks perfectly across five fair trials and produced a
partial 3/5 result on one more task. For bounded maintenance tasks with clear
graders, the Haiku Claude Code baseline often looked practically useful.

The main Claude Code reliability gaps were more specific than broad "cannot do
the suite" failure. It struggled on a tests-only Click task where the expected
structural coverage mattered, and it was inconsistent on a Remotion task with
subtle shared async/browser-media behavior. Those are good candidates for future
targeted evaluation because they reveal where cheap baseline success becomes
less dependable.

For a solo developer, the practical read is:

- Choose the high-effort Codex-style configuration when the priority is maximum
  reliability on this class of bounded maintenance work and review/cost budget
  is available.
- Treat the cheap Claude Code baseline as a promising lower-cost configuration
  for many starter-suite tasks, but require stronger validation on tests-only,
  subtle async, shared-state, and browser-media changes.
- Do not use this report to select a universal winner. Use it to decide which
  follow-up baseline would answer the actual question: lower-effort Codex,
  stronger Claude Code, broader tasks, or more resource-sensitive grading.

## Evidence Gaps

The comparison leaves several important questions unanswered:

- A lower-effort Codex baseline would show how much of Codex's reliability came
  from `xhigh` effort versus the Codex CLI harness itself.
- A stronger Claude Code baseline would show whether the two weak tasks were
  Haiku-specific, Claude Code-harness-specific, or suite/task-specific.
- Billed-cost comparison remains incomplete because Codex cost was not captured
  in the selected results.
- Token comparison remains approximate because the harnesses expose cached
  input, reasoning tokens, and model-event metadata differently.
- Human review label coverage is not perfectly symmetric across the selected
  fair sets, especially for clean successes.

## Recommended Next Work

The next implementation slices for #50 should be narrow:

1. Add a generated comparison appendix that aligns the two selected evidence
   sets by task, agent harness configuration, model, fair-trial count,
   deterministic outcomes, review labels, durations, and available resource
   fields.
2. Keep this hand-authored report separate from the generated appendix so
   interpretation remains reviewable prose rather than hidden computation.
3. Decide whether the next empirical baseline should be lower-effort Codex,
   stronger Claude Code, or both. That decision should be explicit before
   turning this comparison into a public recommendation.
4. Add targeted follow-up tasks or trial batches for tests-only coverage quality
   and subtle shared async/browser-media behavior, because those are where the
   current comparison actually separated the configurations.

## Reader Takeaway

This comparison shows a strong high-effort Codex baseline and a useful cheap
Claude Code baseline, not a universal model ranking.

Codex CLI with `gpt-5.5` / `xhigh` was more reliable on this suite: 60/60 fair
trials passed, with all twelve tasks at 5/5. Claude Code with Haiku 4.5 was
less reliable but still practically capable: 53/60 fair trials passed, ten
tasks reached 5/5, and one more reached 3/5.

The headline should be: high-effort Codex bought consistency; cheap Claude Code
delivered many useful successes but exposed real weak spots. The next fair
comparison should vary effort/model choices deliberately rather than treating
this asymmetric baseline pair as the final word.
