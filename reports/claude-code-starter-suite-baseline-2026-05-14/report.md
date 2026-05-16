# Claude Code Starter Suite Baseline Report

Date: 2026-05-15

## Scope

This report answers a narrow question: how did Claude Code perform on a small
suite of realistic starter maintenance tasks? The answer is scoped to this
twelve-task `starter-coding` suite, the local `claude` agent harness, the
deterministic graders, and the human review labels captured for these runs.

It should not be read as a universal Claude Code ranking or as a guarantee
about how Claude Code will behave on every software project. It is a practical
evidence summary for readers who want to understand how Claude Code did on
these tasks and what caveats showed up in review.

The selected evidence set is tracked at
[`evidence-sets/claude-code-starter-suite-baseline-2026-05-14.json`](../../evidence-sets/claude-code-starter-suite-baseline-2026-05-14.json).
The generated capability evidence digest is
[`capability-evidence-digest.md`](capability-evidence-digest.md).

The evaluated runtime metadata captured from Claude Code events is:

- Agent harness: `claude`
- Agent adapter: `claude_code_cli`
- Model: `claude-haiku-4-5-20251001`
- Model source: `events`
- Claude Code CLI version: `2.1.139 (Claude Code)`
- Permission mode: `acceptEdits`
- Output format: `stream-json`
- Timeout seconds: `1800`
- Max turns: none configured

The model name came from the event stream, not only from the requested CLI
argument. Reasoning effort is reported as `unknown` because this Claude Code
configuration did not expose a comparable effort setting in the stored trial
metadata.

## Summary

The selected fair evidence set contains 60 Claude Code trials: five fair trials
for each of twelve starter-suite tasks. Claude Code passed 53 of the 60 selected
fair trials. Ten tasks passed all five trials, one task passed three of five
trials, and one task failed all five trials.

| Task | Fair Trials | Passes | Min Tokens | Max Tokens | Mean Tokens | Median Tokens | Recorded Cost | Review Summary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| [2048-advanced-snake-params-001](../../tasks/starter/2048-advanced-snake-params-001/task-card.md) | 5 | 5 | 5,781 | 9,083 | 7,340 | 6,674 | $0.70 | none |
| [click-help-option-refactor-001](../../tasks/starter/click-help-option-refactor-001/task-card.md) | 5 | 5 | 16,574 | 26,333 | 20,089 | 19,342 | $2.49 | `success_clean:1`; one success also carries secondary `resource_inefficient` |
| [click-default-map-nargs-001](../../tasks/starter/click-default-map-nargs-001/task-card.md) | 5 | 5 | 15,954 | 25,080 | 20,706 | 21,800 | $2.50 | `success_clean:2`; two successes also carry secondary `resource_inefficient` |
| [click-help-shadowed-option-001](../../tasks/starter/click-help-shadowed-option-001/task-card.md) | 5 | 5 | 15,025 | 23,426 | 20,152 | 21,065 | $2.13 | `success_clean:1`; one success also carries secondary `resource_inefficient` |
| [click-should-strip-ansi-tests-001](../../tasks/starter/click-should-strip-ansi-tests-001/task-card.md) | 5 | 0 | 11,539 | 27,410 | 15,379 | 12,223 | $1.13 | `bad_local_fix:5`; all five failures carry secondary `test_gap` |
| [datawrapper-mcp-docker-requirements-001](../../tasks/starter/datawrapper-mcp-docker-requirements-001/task-card.md) | 5 | 5 | 3,005 | 5,545 | 4,347 | 4,777 | $0.45 | none |
| [httpx-verify-false-client-cert-001](../../tasks/starter/httpx-verify-false-client-cert-001/task-card.md) | 5 | 5 | 6,657 | 11,154 | 8,729 | 8,514 | $0.74 | none |
| [prettier-duplicate-dangling-comments-001](../../tasks/starter/prettier-duplicate-dangling-comments-001/task-card.md) | 5 | 5 | 13,736 | 18,920 | 17,017 | 17,841 | $2.07 | `success_clean:1`; one success also carries secondary `resource_inefficient` |
| [react-tabs-selected-focus-overlay-001](../../tasks/starter/react-tabs-selected-focus-overlay-001/task-card.md) | 5 | 5 | 4,126 | 4,993 | 4,501 | 4,326 | $0.40 | none |
| [remotion-audio-context-autoplay-muted-001](../../tasks/starter/remotion-audio-context-autoplay-muted-001/task-card.md) | 5 | 3 | 11,028 | 16,941 | 12,987 | 11,487 | $1.09 | `bad_local_fix:2`; both failures carry secondary `test_gap` |
| [todomvc-toggle-all-checkbox-001](../../tasks/starter/todomvc-toggle-all-checkbox-001/task-card.md) | 5 | 5 | 8,667 | 12,589 | 10,562 | 10,496 | $1.11 | none |
| [vite-deno-workspace-root-001](../../tasks/starter/vite-deno-workspace-root-001/task-card.md) | 5 | 5 | 12,223 | 18,228 | 15,225 | 14,390 | $1.53 | none |

Token columns report per-trial `input_tokens + output_tokens`. They do not add
cached input tokens or reasoning tokens. Across the full selected evidence set,
the stored results captured 785,170 non-cached input-plus-output tokens,
99,305,237 cached input tokens, and $16.35 in recorded Claude Code usage. The
generated digest links the underlying per-trial reports, transcripts, diffs,
and result JSON files.

## Interpretation

Claude Code was effective on most of this starter suite, but the result is not
uniform. The strongest supported claim is that, under the local `claude`
harness with `claude-haiku-4-5-20251001`, Claude Code solved ten of twelve
tasks in all five fair trials.

The clearest strengths are bounded maintenance tasks with deterministic local
graders: dependency/setup fixes, small application behavior repairs, focused
Python library regressions, and JavaScript/TypeScript ecosystem regressions.
Claude Code passed all selected trials for the 2048, Datawrapper, HTTPX,
Prettier, React Tabs, TodoMVC, Vite, and most Click tasks.

The clearest weakness is `click-should-strip-ansi-tests-001`. Claude Code failed
all five fair trials. The review labels record the same pattern each time:
the patch attempted the requested test coverage, but the final result either
failed the grader or missed the structural coverage expected by the task.

`remotion-audio-context-autoplay-muted-001` is a partial success. Claude Code
passed three of five fair trials. The two valid failures guarded muted playback
behavior but missed the shared `AudioContext` resume rejection behavior required
by the final grader. That makes this task a useful signal that Claude Code can
often find the local shape of an async browser/media fix, but did not
consistently preserve the full shared-control contract.

The resource picture is mixed. The total recorded usage for the selected fair
set is $16.35, and the median trial duration is about 111 seconds. A few
successful Click and Prettier trials were labeled `resource_inefficient` because
they passed while consuming noticeably more recorded usage than the rest of the
selected Claude Code evidence set. Those labels do not negate the passing
outcome, but they matter for readers who care about cost, latency, or review
burden.

The selected evidence set excludes quota-hit/operator-error runs. Those runs are
not counted as capability failures because they do not represent fair task
attempts, but they are still an operational caveat for running Claude Code
evaluations at this scale.

## Limitations

This report should not be read as a multi-harness comparison. It says nothing
by itself about Codex, Cursor, GitHub Copilot, or other agent harnesses on the
same tasks.

This report should also not be read as a model-only evaluation. The measured
unit is the configured Claude Code agent harness, including its terminal
behavior, permission mode, prompts, local tool use, event streaming, and model
selection.

The selected runs used a cheap Claude model selected for proof-of-concept
baseline work. A larger or slower Claude model might have different pass rates,
resource usage, and review burden. Conversely, a stricter turn limit or
different permission mode might make the same tasks harder.

Finally, deterministic grader success does not prove that every patch is ideal.
The human review labels are part of the evidence precisely because a
grader-passing patch can still be resource-heavy, messy, over-edited, or risky.

## Reader Takeaway

This is a useful, moderately strong baseline for Claude Code on this starter
suite. It passed 53 of 60 fair trials, solved ten tasks perfectly across five
trials, and produced credible partial evidence on one more task.

The main caveats are reliability on tests-only or subtle shared-state tasks,
plus operational quota/resource constraints. A reader should treat Claude Code
as capable on this class of bounded maintenance work, but not as uniformly
reliable across the whole suite under this cheap baseline configuration.
