# Capability Evidence Digest

This digest is generated from stored agent-trial results. It reports evidence only; hand-authored agent capability reports should interpret these observations within the evaluated conditions.

Portable Markdown policy: checked-in digests intentionally omit per-trial artifact links because local `runs/` artifacts are ignored and can disappear after temporary worktree cleanup. HTML reports generated from durable snapshot-backed evidence may be checked in when they pass the same no-local-artifact-link portability check.

- Agent trials: `12`
- Evidence set: `Claude Code Opus smoke gate, starter suite, 12 tasks, 1 valid trial per task, 2026-06-04`
- Evidence set source: `evidence-sets/claude-code-opus-smoke-gate-2026-06-04.json`
- Outcome evidence snapshot: `evidence-sets/claude-code-opus-smoke-gate-2026-06-04.outcome-evidence.json`
- Evidence set description: Evidence set for GitHub issue #62. Contains exactly one valid Claude Code Opus smoke trial for each of the 12 starter-suite tasks. Baseline smoke config: --agent claude --claude-model opus --claude-permission-mode acceptEdits --claude-output-format stream-json --claude-timeout-seconds 1800, no max turns. Runtime event model resolved to claude-opus-4-8. Collection stopped after these 12 smoke trials.
- Selected entries: `12`
- Selected result files: `12`
- Selected snapshot records: `12`

## Run Context: starter-coding / claude / claude-opus-4-8 / unknown

- Suite: `starter-coding`
- Agent Harness: `claude`
- Model: `claude-opus-4-8`
- Effort: `unknown`

### Run Surface

| Execution Surface | Runtime Version | Model Source | Sandbox | Approval | Memory | Network | Timeout Seconds | Stop Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local_cli | 2.1.162 (Claude Code) | events | unknown | acceptEdits | no_session_persistence | unknown | 1800 | mixed: grader_failure; success |

### Agent Harness Operability

| Operability Dimension | Evidence |
| --- | --- |
| Agent harness configuration | agent_harness: `claude`<br>model: `claude-opus-4-8`<br>reasoning_effort: `unknown`<br>trials: `12` |
| Budget controls | timeout_seconds: `1800`<br>turn_or_step_budget: `unknown`<br>observed_input_output_tokens: `12/12`<br>observed_cost_usd: `12/12`<br>configured_token_cost_quota_limits: `unknown` |
| Approval boundaries | sandbox_mode: `unknown`<br>approval_policy: `acceptEdits`<br>tool_policy: `{"allowed_tools": [], "disallowed_tools": []}`<br>memory_scope: `no_session_persistence`<br>network_policy: `unknown` |
| Verifier state | final_grader_status: `failed; passed`<br>checks_array: `12/12`<br>graders_array: `12/12`<br>intermediate_verifier_movement: `unknown` |
| Halt reasons | normalized_or_derived_stop_reason: `grader_failure; success`<br>first_class_halt_reason_taxonomy: `unknown`<br>error_field: `unknown`<br>budget_operator_interruption_taxonomy: `unknown` |
| Interrupted-run receipt | interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`<br>admission_decision_evidence: `12/12` |
| Tool/patch context | changed_files: `12/12`<br>commands_run: `12/12`<br>human_review_overlay: `12/12`<br>transcript: `12/12`<br>diff_patch: `12/12` |
| Receipt basics | run_dir: `12/12`<br>report_md: `12/12`<br>result_json: `12/12`<br>transcript: `12/12`<br>diff_patch: `12/12` |

### Outcome Summary

| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| click-help-option-refactor-001 | capability | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| click-default-map-nargs-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| click-help-shadowed-option-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| click-should-strip-ansi-tests-001 | regression | 1 | 1 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 |
| datawrapper-mcp-docker-requirements-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| httpx-verify-false-client-cert-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| prettier-duplicate-dangling-comments-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| react-tabs-selected-focus-overlay-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| remotion-audio-context-autoplay-muted-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| todomvc-toggle-all-checkbox-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |
| vite-deno-workspace-root-001 | regression | 1 | 1 | 0 | 1 | 1 | 1.00 | 1.00 | 1.00 |

### Token Summary

| Task | Type | IO Tokens | Cached Tokens | Reason Tokens | IO Tok / Verified | IO Tok / Accepted | Cached Tok / Verified | Reason Tok / Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 10726 | 470649 | unknown | 10726 | 10726 | 470649 | unknown |
| click-help-option-refactor-001 | capability | 16641 | 813122 | unknown | 16641 | 16641 | 813122 | unknown |
| click-default-map-nargs-001 | regression | 13459 | 398579 | unknown | 13459 | 13459 | 398579 | unknown |
| click-help-shadowed-option-001 | regression | 13337 | 523251 | unknown | 13337 | 13337 | 523251 | unknown |
| click-should-strip-ansi-tests-001 | regression | 11130 | 331770 | unknown | unknown | unknown | unknown | unknown |
| datawrapper-mcp-docker-requirements-001 | regression | 9428 | 243339 | unknown | 9428 | 9428 | 243339 | unknown |
| httpx-verify-false-client-cert-001 | regression | 8572 | 184073 | unknown | 8572 | 8572 | 184073 | unknown |
| prettier-duplicate-dangling-comments-001 | regression | 24952 | 1370044 | unknown | 24952 | 24952 | 1370044 | unknown |
| react-tabs-selected-focus-overlay-001 | regression | 6536 | 75117 | unknown | 6536 | 6536 | 75117 | unknown |
| remotion-audio-context-autoplay-muted-001 | regression | 15050 | 205845 | unknown | 15050 | 15050 | 205845 | unknown |
| todomvc-toggle-all-checkbox-001 | regression | 13343 | 426337 | unknown | 13343 | 13343 | 426337 | unknown |
| vite-deno-workspace-root-001 | regression | 15901 | 604593 | unknown | 15901 | 15901 | 604593 | unknown |

### Review and Patch Summary

| Task | Type | Median ms | Median Files | Median +Lines | Median -Lines | Primary Review Labels | Secondary Review Labels | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 122067 | 2 | 8 | 6 | success_clean:1 |  |  |
| click-help-option-refactor-001 | capability | 180085 | 3 | 34 | 29 | success_clean:1 |  |  |
| click-default-map-nargs-001 | regression | 133938 | 1 | 6 | 0 | success_clean:1 |  |  |
| click-help-shadowed-option-001 | regression | 134321 | 1 | 17 | 3 | success_clean:1 |  |  |
| click-should-strip-ansi-tests-001 | regression | 119317 | 1 | 46 | 0 | test_gap:1 | spec_misread:1 |  |
| datawrapper-mcp-docker-requirements-001 | regression | 80202 | 1 | 6 | 3 | success_clean:1 |  |  |
| httpx-verify-false-client-cert-001 | regression | 70077 | 1 | 5 | 4 | success_clean:1 |  |  |
| prettier-duplicate-dangling-comments-001 | regression | 335034 | 1 | 11 | 0 | success_clean:1 | resource_inefficient:1 |  |
| react-tabs-selected-focus-overlay-001 | regression | 38484 | 3 | 0 | 30 | success_clean:1 |  |  |
| remotion-audio-context-autoplay-muted-001 | regression | 128744 | 2 | 40 | 15 | success_clean:1 | resource_inefficient:1 |  |
| todomvc-toggle-all-checkbox-001 | regression | 123307 | 4 | 8 | 10 | success_clean:1 |  |  |
| vite-deno-workspace-root-001 | regression | 165940 | 6 | 58 | 0 | success_clean:1 |  |  |

### Trial Evidence

| Task | Type | Trial | Grader Outcome | Validity | Primary Review Label | Secondary Review Labels | Exclusion | Files | +Lines | -Lines | Input Tokens | Cached Input Tokens | Output Tokens | Reasoning Tokens | Cost USD | Duration ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 20260604-111544-2048-advanced-snake-params-001-claude-606ff781 | passed | valid | success_clean |  |  | 2 | 8 | 6 | 3562 | 470649 | 7164 | unknown | 0.5481504999999999 | 122067 |
| click-default-map-nargs-001 | regression | 20260604-111807-click-default-map-nargs-001-claude-07effe6e | passed | valid | success_clean |  |  | 1 | 6 | 0 | 3423 | 398579 | 10036 | unknown | 0.60867075 | 133938 |
| click-help-option-refactor-001 | capability | 20260604-112042-click-help-option-refactor-001-claude-c86536e8 | passed | valid | success_clean |  |  | 3 | 34 | 29 | 3711 | 813122 | 12930 | unknown | 0.91465725 | 180085 |
| click-help-shadowed-option-001 | regression | 20260604-112359-click-help-shadowed-option-001-claude-28fa6afc | passed | valid | success_clean |  |  | 1 | 17 | 3 | 3435 | 523251 | 9902 | unknown | 0.6556644999999999 | 134321 |
| click-should-strip-ansi-tests-001 | regression | 20260604-112633-click-should-strip-ansi-tests-001-claude-f93003c0 | failed | valid | test_gap | spec_misread |  | 1 | 46 | 0 | 3292 | 331770 | 7838 | unknown | 0.47994200000000015 | 119317 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260604-112914-datawrapper-mcp-docker-requirements-001-claude-e159e640 | passed | valid | success_clean |  |  | 1 | 6 | 3 | 3284 | 243339 | 6144 | unknown | 0.39525550000000004 | 80202 |
| httpx-verify-false-client-cert-001 | regression | 20260604-113059-httpx-verify-false-client-cert-001-claude-d1937af8 | passed | valid | success_clean |  |  | 1 | 5 | 4 | 3278 | 184073 | 5294 | unknown | 0.341875 | 70077 |
| prettier-duplicate-dangling-comments-001 | regression | 20260604-113240-prettier-duplicate-dangling-comments-001-claude-c89fa9a6 | passed | valid | success_clean | resource_inefficient |  | 1 | 11 | 0 | 3852 | 1370044 | 21100 | unknown | 1.5157562500000001 | 335034 |
| react-tabs-selected-focus-overlay-001 | regression | 20260604-113840-react-tabs-selected-focus-overlay-001-claude-254b9850 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 3268 | 75117 | 3268 | unknown | 0.2143215 | 38484 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260604-114530-remotion-audio-context-autoplay-muted-001-claude-785a8318 | passed | valid | success_clean | resource_inefficient |  | 2 | 40 | 15 | 3827 | 205845 | 11223 | unknown | 0.62159625 | 128744 |
| todomvc-toggle-all-checkbox-001 | regression | 20260604-115522-todomvc-toggle-all-checkbox-001-claude-7613ddbd | passed | valid | success_clean |  |  | 4 | 8 | 10 | 3417 | 426337 | 9926 | unknown | 0.6560580000000001 | 123307 |
| vite-deno-workspace-root-001 | regression | 20260604-115750-vite-deno-workspace-root-001-claude-0c83c058 | passed | valid | success_clean |  |  | 6 | 58 | 0 | 3437 | 604593 | 12464 | unknown | 0.7889065000000001 | 165940 |
