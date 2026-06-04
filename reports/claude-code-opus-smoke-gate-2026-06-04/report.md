# Claude Code Opus Smoke Gate Report

Date: 2026-06-04

Scope: GitHub issue #62, prerequisite evidence for the later #50 starter-suite comparison.

## Verdict

The 12-task Claude Code Opus smoke gate completed and should proceed to a human approval checkpoint before collecting the remaining four fair trials per task.

Result: 12 valid trials, 0 excluded trials, 11 grader-passing trials, and 1 fair failure. Collection stopped after exactly one smoke trial per starter-suite task.

#50 cannot use this as a full comparison baseline yet. It can use this as readiness evidence that Opus is operable locally, but the full #50 comparison still needs explicit approval for four more fair Opus trials per task.

## Configuration

| Field | Value |
| --- | --- |
| Agent harness | `claude` |
| Claude Code version | `2.1.162 (Claude Code)` |
| Requested model | `opus` |
| Runtime model | `claude-opus-4-8` |
| Auth/account route | `claude.ai`, first-party provider, Pro subscription, `apiKeySource=none` in probe |
| API/cloud-provider env routes | none present by name |
| Permission mode | `acceptEdits` |
| Output format | `stream-json` |
| Session persistence | disabled |
| Max turns | unset |
| Timeout | `1800` seconds |
| Trials/jobs | exactly one trial and one job per task |

The tiny model probe resolved `opus` to `claude-opus-4-8`. It returned `ready` and then exited with `error_max_budget_usd` because the local probe cap was set to `0.02` USD while Claude Code estimated `0.02145` USD. That cap failure was probe-only and did not occur during the smoke trials.

## Results

| Task | Status | Review | Duration ms | Cost USD |
| --- | --- | --- | ---: | ---: |
| `2048-advanced-snake-params-001` | passed | `success_clean` | 122067 | 0.5481505 |
| `click-default-map-nargs-001` | passed | `success_clean` | 133938 | 0.60867075 |
| `click-help-option-refactor-001` | passed | `success_clean` | 180085 | 0.91465725 |
| `click-help-shadowed-option-001` | passed | `success_clean` | 134321 | 0.6556645 |
| `click-should-strip-ansi-tests-001` | failed | `test_gap`, `spec_misread` | 119317 | 0.479942 |
| `datawrapper-mcp-docker-requirements-001` | passed | `success_clean` | 80202 | 0.3952555 |
| `httpx-verify-false-client-cert-001` | passed | `success_clean` | 70077 | 0.341875 |
| `prettier-duplicate-dangling-comments-001` | passed | `success_clean`, `resource_inefficient` | 335034 | 1.51575625 |
| `react-tabs-selected-focus-overlay-001` | passed | `success_clean` | 38484 | 0.2143215 |
| `remotion-audio-context-autoplay-muted-001` | passed | `success_clean`, `resource_inefficient` | 128744 | 0.62159625 |
| `todomvc-toggle-all-checkbox-001` | passed | `success_clean` | 123307 | 0.656058 |
| `vite-deno-workspace-root-001` | passed | `success_clean` | 165940 | 0.7889065 |

Aggregate evidence:

- Fair pass rate: 11/12, 91.7%.
- Accepted results: 11/12.
- Excluded trials: 0.
- Median recorded agent duration: 126025 ms.
- Total recorded agent duration: 1631516 ms.
- Total input-plus-output tokens: 159075.
- Total cached input tokens: 5646719.
- Total Claude Code reported cost: 7.740854 USD.

Cost caveat: the auth guard verified first-party Claude.ai Pro subscription routing with no API-key route present. The `cost_usd` values above are Claude Code reported estimates and useful for relative resource comparison, not proof of API billing.

## Failure

`click-should-strip-ansi-tests-001` is a fair capability failure. Setup passed, the targeted pytest command passed, and the final structural grader failed. The patch imported `should_strip_ansi` directly and called `should_strip_ansi(...)`; the grader required an attribute call whose function attribute is `should_strip_ansi`, matching the task/reference expectation to exercise `click._compat.should_strip_ansi(...)`.

This was reviewed as valid `test_gap` with secondary `spec_misread`, not excluded.

## Resource Notes

`prettier-duplicate-dangling-comments-001` was the largest recorded agent trial by duration, token use, and reported estimated cost: 335034 ms, 24952 input-plus-output tokens, 1370044 cached input tokens, and 1.51575625 USD reported cost.

`remotion-audio-context-autoplay-muted-001` had unusually heavy pre-agent setup. The standard smoke-test path spent several minutes in `git clone` and `index-pack` before Claude Code started. The recorded agent trial then passed in 128744 ms. Treat that as setup operability evidence before scaling repeated trials.

No subscription quota stop, auth prompt, MFA prompt, API-key fallback, or cloud-provider routing appeared during the 12 smoke trials.

## Evidence

- Evidence set: `evidence-sets/claude-code-opus-smoke-gate-2026-06-04.json`
- Outcome evidence snapshot: `evidence-sets/claude-code-opus-smoke-gate-2026-06-04.outcome-evidence.json`
- Generated digest: `reports/claude-code-opus-smoke-gate-2026-06-04/digest.md`
- Snapshot-backed HTML digest: `reports/claude-code-opus-smoke-gate-2026-06-04/digest.html`
- Readiness note: `reports/claude-code-opus-smoke-gate-2026-06-04/readiness.md`
- Raw local trial artifacts: `runs/claude-code-opus-smoke-gate-2026-06-04`

## Recommendation

Ask Jordan before collecting the remaining four fair Opus trials per task. The smoke gate supports proceeding, but the approval should explicitly accept the observed resource profile, especially the Prettier token/cost outlier and the Remotion setup overhead.
