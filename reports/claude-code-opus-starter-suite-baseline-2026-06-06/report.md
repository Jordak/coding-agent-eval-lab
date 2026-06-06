# Claude Code Opus Starter Suite Baseline Report

Date: 2026-06-06

Scope: GitHub issue #62, prerequisite evidence for the later #50 starter-suite comparison.

## Verdict

The Claude Code Opus starter-suite baseline is complete. The selected portable evidence set contains 60 valid fair trials: five fair trials for each of the 12 starter-suite tasks.

Result: 55 grader-passing trials, 5 fair failures, and 11 excluded quota/session-limit artifacts preserved in local `runs/` with exclusion metadata. The full Opus baseline can proceed into the #50 final comparison work.

This did not skip the #62 smoke-gate approval step. The first committed bundle stopped after the 12 sequential smoke trials; the remaining repeated trials were collected only after Jordan explicitly approved continuing, including the later two-job parallel collection shape.

## Configuration

| Field | Value |
| --- | --- |
| Agent harness | `claude` |
| Agent adapter | `claude_code_cli` |
| Requested model | `opus` |
| Runtime model | `claude-opus-4-8` |
| Claude Code versions | mixed: `2.1.162 (Claude Code)` for the smoke run; `2.1.165 (Claude Code)` for later top-up runs |
| Auth/account route | `claude.ai`, first-party provider, Pro subscription, `apiKeySource=none` in trial events |
| API/cloud-provider env routes | none present by name in preflight checks |
| Permission mode | `acceptEdits` |
| Output format | `stream-json` |
| Session persistence | disabled |
| Max turns | unset |
| Timeout | `1800` seconds |
| Final parallelization shape | task-bounded batches, `--trials 4 --jobs 2` for remaining fair trials after the smoke gate |

Cost caveat: the auth guard verified first-party Claude.ai Pro subscription routing with no API-key route present. The `cost_usd` values in the trial results are Claude Code reported estimates and useful for relative resource comparison, not proof of API billing.

## Results

| Task | Fair Trials | Passes | Fair Failures | Notes |
| --- | ---: | ---: | ---: | --- |
| `2048-advanced-snake-params-001` | 5 | 5 | 0 | all passed |
| `click-default-map-nargs-001` | 5 | 5 | 0 | all passed |
| `click-help-option-refactor-001` | 5 | 5 | 0 | all passed |
| `click-help-shadowed-option-001` | 5 | 5 | 0 | all passed; four quota/session artifacts excluded |
| `click-should-strip-ansi-tests-001` | 5 | 1 | 4 | fair failures reviewed as `test_gap` with secondary `spec_misread` |
| `datawrapper-mcp-docker-requirements-001` | 5 | 4 | 1 | fair failure reviewed as `context_miss` |
| `httpx-verify-false-client-cert-001` | 5 | 5 | 0 | all passed; two quota/session artifacts excluded |
| `prettier-duplicate-dangling-comments-001` | 5 | 5 | 0 | all passed; one quota/session artifact excluded |
| `react-tabs-selected-focus-overlay-001` | 5 | 5 | 0 | all passed |
| `remotion-audio-context-autoplay-muted-001` | 5 | 5 | 0 | all passed |
| `todomvc-toggle-all-checkbox-001` | 5 | 5 | 0 | all passed |
| `vite-deno-workspace-root-001` | 5 | 5 | 0 | all passed; four quota/session artifacts excluded |

Aggregate selected fair evidence:

- Fair pass rate: 55/60, 91.7%.
- Tasks with five passing trials: 10/12.
- Tasks with at least four passing trials: 11/12.
- Total input-plus-output tokens: 823,584.
- Total cached input tokens: 30,909,120.
- Total recorded agent duration: 8,535,759 ms.
- Total Claude Code reported cost: 40.822930 USD.

## Failure Notes

`click-should-strip-ansi-tests-001` produced four valid fair failures and one pass. The failures were retained and reviewed as `test_gap` with secondary `spec_misread`, matching the smoke-trial failure pattern: Claude added tests, but missed the exact structural coverage the task expected around `click._compat.should_strip_ansi(...)`.

`datawrapper-mcp-docker-requirements-001` produced one valid fair failure reviewed as `context_miss`. The failure made no patch and did not satisfy the grader, so it remains a fair capability miss rather than an exclusion.

## Resource and Quota Notes

The largest selected fair task by recorded cost was `prettier-duplicate-dangling-comments-001`, with 8.527827 USD reported across five fair trials. Its smoke trial also carried the secondary `resource_inefficient` review label.

The Opus collection repeatedly encountered Claude Code subscription session limits. Eleven artifacts were preserved but excluded with `dependency_issue` metadata:

- `click-help-shadowed-option-001`: 4 excluded artifacts.
- `httpx-verify-false-client-cert-001`: 2 excluded artifacts.
- `prettier-duplicate-dangling-comments-001`: 1 excluded artifact.
- `vite-deno-workspace-root-001`: 4 excluded artifacts.

Those artifacts are not counted as fair failures because Claude Code reported a quota/session reset condition, in some cases before any model tokens were recorded.

## Evidence

- Evidence set: `evidence-sets/claude-code-opus-starter-suite-baseline-2026-06-06.json`
- Outcome evidence snapshot: `evidence-sets/claude-code-opus-starter-suite-baseline-2026-06-06.outcome-evidence.json`
- Generated digest: `reports/claude-code-opus-starter-suite-baseline-2026-06-06/digest.md`
- Snapshot-backed HTML digest: `reports/claude-code-opus-starter-suite-baseline-2026-06-06/digest.html`
- Raw local trial artifacts: `runs/claude-code-opus-smoke-gate-2026-06-04`, `runs/claude-code-opus-parallel-confirmation-2026-06-04`, and `runs/claude-code-opus-starter-suite-baseline-2026-06-04`

The digest was regenerated with `--runs-dir /tmp/agentlab-missing-runs`, and `check-evidence-portability` passed for the manifest.

## Recommendation

#50 can proceed to the full comparison phase using this Opus evidence set. The comparison should explicitly separate model capability results from Claude Code subscription operability, because quota/session limits materially affected collection wall-clock time even though they are excluded from fair pass-rate accounting.
