# Capability Evidence Digest

This digest is generated from stored agent-trial results. It reports evidence only; hand-authored agent capability reports should interpret these observations within the evaluated conditions.

Portable Markdown policy: checked-in digests intentionally omit per-trial artifact links because local `runs/` artifacts are ignored and can disappear after temporary worktree cleanup. HTML reports generated from durable snapshot-backed evidence may be checked in when they pass the same no-local-artifact-link portability check.

- Agent trials: `60`
- Evidence set: `Claude Code Opus starter suite baseline, 12 tasks, 5 fair trials per task, 2026-06-06`
- Evidence set source: `evidence-sets/claude-code-opus-starter-suite-baseline-2026-06-06.json`
- Outcome evidence snapshot: `evidence-sets/claude-code-opus-starter-suite-baseline-2026-06-06.outcome-evidence.json`
- Evidence set description: Evidence set for GitHub issue #62 and prerequisite for #50. Contains 60 valid Claude Code Opus fair trials across the 12 starter-suite tasks. Quota/session-limit artifacts are preserved under runs/ with review.json exclusion metadata but excluded from this manifest. Baseline config: --agent claude --claude-model opus --claude-permission-mode acceptEdits --claude-output-format stream-json --claude-timeout-seconds 1800, no max turns. Runtime event model resolved to claude-opus-4-8; Claude Code auth route was claude.ai first-party Pro subscription with apiKeySource=none in trial events.
- Selected entries: `60`
- Selected result files: `60`
- Selected snapshot records: `60`

## Run Context: starter-coding / claude / claude-opus-4-8 / unknown

- Suite: `starter-coding`
- Agent Harness: `claude`
- Model: `claude-opus-4-8`
- Effort: `unknown`

### Run Surface

| Execution Surface | Runtime Version | Model Source | Sandbox | Approval | Memory | Network | Timeout Seconds | Stop Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local_cli | mixed: 2.1.162 (Claude Code); 2.1.165 (Claude Code) | events | unknown | acceptEdits | no_session_persistence | unknown | 1800 | mixed: grader_failure; success |

### Agent Harness Operability

| Operability Dimension | Evidence |
| --- | --- |
| Agent harness configuration | agent_harness: `claude`<br>model: `claude-opus-4-8`<br>reasoning_effort: `unknown`<br>trials: `60` |
| Budget controls | timeout_seconds: `1800`<br>turn_or_step_budget: `unknown`<br>observed_input_output_tokens: `60/60`<br>observed_cost_usd: `60/60`<br>configured_token_cost_quota_limits: `unknown` |
| Approval boundaries | sandbox_mode: `unknown`<br>approval_policy: `acceptEdits`<br>tool_policy: `{"allowed_tools": [], "disallowed_tools": []}`<br>memory_scope: `no_session_persistence`<br>network_policy: `unknown` |
| Verifier state | final_grader_status: `failed; passed`<br>checks_array: `60/60`<br>graders_array: `60/60`<br>intermediate_verifier_movement: `unknown` |
| Halt reasons | normalized_or_derived_stop_reason: `grader_failure; success`<br>first_class_halt_reason_taxonomy: `unknown`<br>error_field: `unknown`<br>budget_operator_interruption_taxonomy: `unknown` |
| Interrupted-run receipt | interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`<br>admission_decision_evidence: `16/60` |
| Tool/patch context | changed_files: `59/60`<br>commands_run: `60/60`<br>human_review_overlay: `16/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |
| Receipt basics | run_dir: `60/60`<br>report_md: `60/60`<br>result_json: `60/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |

### Outcome Summary

| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| click-help-option-refactor-001 | capability | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| click-default-map-nargs-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| click-help-shadowed-option-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| click-should-strip-ansi-tests-001 | regression | 5 | 5 | 0 | 1 | 0 | 0.20 | 1.00 | 0.00 |
| datawrapper-mcp-docker-requirements-001 | regression | 5 | 5 | 0 | 4 | 1 | 0.80 | 1.00 | 0.00 |
| httpx-verify-false-client-cert-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| prettier-duplicate-dangling-comments-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| react-tabs-selected-focus-overlay-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| remotion-audio-context-autoplay-muted-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| todomvc-toggle-all-checkbox-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| vite-deno-workspace-root-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |

### Token Summary

| Task | Type | IO Tokens | Cached Tokens | Reason Tokens | IO Tok / Verified | IO Tok / Accepted | Cached Tok / Verified | Reason Tok / Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 43682 | 1443221 | unknown | 8736.40 | 43682 | 288644.20 | unknown |
| click-help-option-refactor-001 | capability | 90367 | 4505495 | unknown | 18073.40 | 90367 | 901099 | unknown |
| click-default-map-nargs-001 | regression | 64773 | 2240469 | unknown | 12954.60 | 64773 | 448093.80 | unknown |
| click-help-shadowed-option-001 | regression | 66832 | 2404408 | unknown | 13366.40 | 66832 | 480881.60 | unknown |
| click-should-strip-ansi-tests-001 | regression | 54946 | 1543626 | unknown | 54946 | unknown | 1543626 | unknown |
| datawrapper-mcp-docker-requirements-001 | regression | 36625 | 753901 | unknown | 9156.25 | 36625 | 188475.25 | unknown |
| httpx-verify-false-client-cert-001 | regression | 48609 | 1259557 | unknown | 9721.80 | 48609 | 251911.40 | unknown |
| prettier-duplicate-dangling-comments-001 | regression | 129321 | 8400964 | unknown | 25864.20 | 129321 | 1680192.80 | unknown |
| react-tabs-selected-focus-overlay-001 | regression | 37137 | 619526 | unknown | 7427.40 | 37137 | 123905.20 | unknown |
| remotion-audio-context-autoplay-muted-001 | regression | 90787 | 2121680 | unknown | 18157.40 | 90787 | 424336 | unknown |
| todomvc-toggle-all-checkbox-001 | regression | 78070 | 2519582 | unknown | 15614 | 78070 | 503916.40 | unknown |
| vite-deno-workspace-root-001 | regression | 82435 | 3096691 | unknown | 16487 | 82435 | 619338.20 | unknown |

### Review and Patch Summary

| Task | Type | Median ms | Median Files | Median +Lines | Median -Lines | Primary Review Labels | Secondary Review Labels | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 76145 | 1 | 1 | 1 | success_clean:1 |  |  |
| click-help-option-refactor-001 | capability | 187504 | 3 | 41 | 29 | success_clean:1 |  |  |
| click-default-map-nargs-001 | regression | 143534 | 1 | 9 | 0 | success_clean:1 |  |  |
| click-help-shadowed-option-001 | regression | 134321 | 2 | 10 | 3 | success_clean:1 |  |  |
| click-should-strip-ansi-tests-001 | regression | 113029 | 1 | 46 | 0 | test_gap:4 | spec_misread:4 |  |
| datawrapper-mcp-docker-requirements-001 | regression | 63500 | 1 | 5 | 2 | context_miss:1, success_clean:1 |  |  |
| httpx-verify-false-client-cert-001 | regression | 99107 | 1 | 5 | 4 | success_clean:1 |  |  |
| prettier-duplicate-dangling-comments-001 | regression | 335034 | 1 | 11 | 0 | success_clean:1 | resource_inefficient:1 |  |
| react-tabs-selected-focus-overlay-001 | regression | 51264 | 3 | 0 | 30 | success_clean:1 |  |  |
| remotion-audio-context-autoplay-muted-001 | regression | 165064 | 2 | 39 | 15 | success_clean:1 | resource_inefficient:1 |  |
| todomvc-toggle-all-checkbox-001 | regression | 128907 | 4 | 6 | 8 | success_clean:1 |  |  |
| vite-deno-workspace-root-001 | regression | 172172 | 6 | 59 | 0 | success_clean:1 |  |  |

### Trial Evidence

| Task | Type | Trial | Grader Outcome | Validity | Primary Review Label | Secondary Review Labels | Exclusion | Files | +Lines | -Lines | Input Tokens | Cached Input Tokens | Output Tokens | Reasoning Tokens | Cost USD | Duration ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 20260604-111544-2048-advanced-snake-params-001-claude-606ff781 | passed | valid | success_clean |  |  | 2 | 8 | 6 | 3562 | 470649 | 7164 | unknown | 0.5481504999999999 | 122067 |
| 2048-advanced-snake-params-001 | capability | 20260604-164354-2048-advanced-snake-params-001-claude-9133d54c | passed | valid |  |  |  | 1 | 1 | 1 | 3286 | 245416 | 5353 | unknown | 0.36228525000000006 | 76145 |
| 2048-advanced-snake-params-001 | capability | 20260604-164354-2048-advanced-snake-params-001-claude-adabfc50 | passed | valid |  |  |  | 1 | 1 | 1 | 3280 | 180758 | 3567 | unknown | 0.27717 | 46962 |
| 2048-advanced-snake-params-001 | capability | 20260604-164442-2048-advanced-snake-params-001-claude-ce49f4e1 | passed | valid |  |  |  | 1 | 1 | 1 | 3286 | 245193 | 4656 | unknown | 0.34041125000000005 | 64659 |
| 2048-advanced-snake-params-001 | capability | 20260604-164511-2048-advanced-snake-params-001-claude-6947f83e | passed | valid |  |  |  | 1 | 1 | 1 | 3417 | 301205 | 6111 | unknown | 0.42873474999999994 | 87417 |
| click-default-map-nargs-001 | regression | 20260604-111807-click-default-map-nargs-001-claude-07effe6e | passed | valid | success_clean |  |  | 1 | 6 | 0 | 3423 | 398579 | 10036 | unknown | 0.60867075 | 133938 |
| click-default-map-nargs-001 | regression | 20260604-164650-click-default-map-nargs-001-claude-af47a44b | passed | valid |  |  |  | 1 | 10 | 0 | 3431 | 528951 | 10664 | unknown | 0.7057217499999999 | 143534 |
| click-default-map-nargs-001 | regression | 20260604-164650-click-default-map-nargs-001-claude-d4462d6a | passed | valid |  |  |  | 1 | 9 | 0 | 3292 | 351380 | 7807 | unknown | 0.5046787500000001 | 125661 |
| click-default-map-nargs-001 | regression | 20260604-164900-click-default-map-nargs-001-claude-0005bf58 | passed | valid |  |  |  | 1 | 6 | 0 | 3433 | 503164 | 9209 | unknown | 0.6314507500000002 | 157520 |
| click-default-map-nargs-001 | regression | 20260604-164918-click-default-map-nargs-001-claude-af5826a9 | passed | valid |  |  |  | 1 | 9 | 0 | 3427 | 458395 | 10051 | unknown | 0.6378537500000001 | 157881 |
| click-help-option-refactor-001 | capability | 20260604-112042-click-help-option-refactor-001-claude-c86536e8 | passed | valid | success_clean |  |  | 3 | 34 | 29 | 3711 | 813122 | 12930 | unknown | 0.91465725 | 180085 |
| click-help-option-refactor-001 | capability | 20260604-165208-click-help-option-refactor-001-claude-18efce87 | passed | valid |  |  |  | 3 | 41 | 29 | 3866 | 1236928 | 15927 | unknown | 1.2213777499999998 | 224420 |
| click-help-option-refactor-001 | capability | 20260604-165208-click-help-option-refactor-001-claude-78228193 | passed | valid |  |  |  | 3 | 44 | 29 | 3717 | 961418 | 15611 | unknown | 1.0763715 | 203791 |
| click-help-option-refactor-001 | capability | 20260604-165535-click-help-option-refactor-001-claude-28802844 | passed | valid |  |  |  | 3 | 37 | 28 | 3572 | 700991 | 13953 | unknown | 0.8900517499999998 | 179587 |
| click-help-option-refactor-001 | capability | 20260604-165556-click-help-option-refactor-001-claude-4413371e | passed | valid |  |  |  | 3 | 43 | 31 | 3709 | 793036 | 13371 | unknown | 0.9138967500000001 | 187504 |
| click-help-shadowed-option-001 | regression | 20260604-112359-click-help-shadowed-option-001-claude-28fa6afc | passed | valid | success_clean |  |  | 1 | 17 | 3 | 3435 | 523251 | 9902 | unknown | 0.6556644999999999 | 134321 |
| click-help-shadowed-option-001 | regression | 20260605-045911-click-help-shadowed-option-001-claude-0adf6fa9 | passed | valid |  |  |  | 2 | 10 | 5 | 3429 | 457069 | 10038 | unknown | 0.6265109999999999 | 169306 |
| click-help-shadowed-option-001 | regression | 20260605-045911-click-help-shadowed-option-001-claude-bd9d8fec | passed | valid |  |  |  | 2 | 9 | 2 | 3423 | 383008 | 8531 | unknown | 0.54385425 | 117148 |
| click-help-shadowed-option-001 | regression | 20260605-050112-click-help-shadowed-option-001-claude-6bd18c71 | passed | valid |  |  |  | 2 | 15 | 9 | 3429 | 456646 | 9946 | unknown | 0.62867075 | 131273 |
| click-help-shadowed-option-001 | regression | 20260605-050204-click-help-shadowed-option-001-claude-060b6403 | passed | valid |  |  |  | 1 | 7 | 1 | 3437 | 584434 | 11262 | unknown | 0.729356 | 163340 |
| click-should-strip-ansi-tests-001 | regression | 20260604-112633-click-should-strip-ansi-tests-001-claude-f93003c0 | failed | valid | test_gap | spec_misread |  | 1 | 46 | 0 | 3292 | 331770 | 7838 | unknown | 0.47994200000000015 | 119317 |
| click-should-strip-ansi-tests-001 | regression | 20260605-050502-click-should-strip-ansi-tests-001-claude-5295c8af | passed | valid |  |  |  | 1 | 39 | 0 | 3423 | 361737 | 8385 | unknown | 0.515023 | 113029 |
| click-should-strip-ansi-tests-001 | regression | 20260605-050502-click-should-strip-ansi-tests-001-claude-cc53eae0 | failed | valid | test_gap | spec_misread |  | 1 | 43 | 0 | 3284 | 235208 | 6456 | unknown | 0.38966975 | 88424 |
| click-should-strip-ansi-tests-001 | regression | 20260605-050634-click-should-strip-ansi-tests-001-claude-f118e369 | failed | valid | test_gap | spec_misread |  | 1 | 48 | 0 | 3288 | 278184 | 6537 | unknown | 0.4085902500000001 | 95719 |
| click-should-strip-ansi-tests-001 | regression | 20260605-050659-click-should-strip-ansi-tests-001-claude-d5f06eb7 | failed | valid | test_gap | spec_misread |  | 1 | 48 | 0 | 3421 | 336727 | 9022 | unknown | 0.51978925 | 114429 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260604-112914-datawrapper-mcp-docker-requirements-001-claude-e159e640 | passed | valid | success_clean |  |  | 1 | 6 | 3 | 3284 | 243339 | 6144 | unknown | 0.39525550000000004 | 80202 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260605-050942-datawrapper-mcp-docker-requirements-001-claude-089cde84 | passed | valid |  |  |  | 1 | 5 | 2 | 3274 | 135312 | 4021 | unknown | 0.27716699999999994 | 63500 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260605-050942-datawrapper-mcp-docker-requirements-001-claude-bd247c14 | failed | valid | context_miss |  |  | 0 | 0 | 0 | 3141 | 89101 | 2233 | unknown | 0.18925275 | 45599 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260605-051038-datawrapper-mcp-docker-requirements-001-claude-6595920f | passed | valid |  |  |  | 1 | 5 | 2 | 3274 | 133170 | 3502 | unknown | 0.25288600000000006 | 46660 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260605-051047-datawrapper-mcp-docker-requirements-001-claude-b6cc3c1d | passed | valid |  |  |  | 1 | 5 | 2 | 3276 | 152979 | 4476 | unknown | 0.29852425000000005 | 67895 |
| httpx-verify-false-client-cert-001 | regression | 20260604-113059-httpx-verify-false-client-cert-001-claude-d1937af8 | passed | valid | success_clean |  |  | 1 | 5 | 4 | 3278 | 184073 | 5294 | unknown | 0.341875 | 70077 |
| httpx-verify-false-client-cert-001 | regression | 20260604-163946-httpx-verify-false-client-cert-001-claude-9348c94a | passed | valid |  |  |  | 1 | 5 | 4 | 3286 | 274136 | 6752 | unknown | 0.42745274999999994 | 99333 |
| httpx-verify-false-client-cert-001 | regression | 20260604-163946-httpx-verify-false-client-cert-001-claude-a2637ff3 | passed | valid |  |  |  | 1 | 5 | 4 | 3282 | 228987 | 6256 | unknown | 0.39454575 | 73891 |
| httpx-verify-false-client-cert-001 | regression | 20260605-095913-httpx-verify-false-client-cert-001-claude-1de69404 | passed | valid |  |  |  | 1 | 5 | 4 | 3433 | 280511 | 7832 | unknown | 0.47243024999999994 | 101505 |
| httpx-verify-false-client-cert-001 | regression | 20260605-095913-httpx-verify-false-client-cert-001-claude-a5df53e0 | passed | valid |  |  |  | 1 | 5 | 4 | 3433 | 291850 | 5763 | unknown | 0.4266447500000001 | 99107 |
| prettier-duplicate-dangling-comments-001 | regression | 20260604-113240-prettier-duplicate-dangling-comments-001-claude-c89fa9a6 | passed | valid | success_clean | resource_inefficient |  | 1 | 11 | 0 | 3852 | 1370044 | 21100 | unknown | 1.5157562500000001 | 335034 |
| prettier-duplicate-dangling-comments-001 | regression | 20260605-100116-prettier-duplicate-dangling-comments-001-claude-cd43c0cc | passed | valid |  |  |  | 1 | 14 | 0 | 4027 | 2145840 | 23772 | unknown | 2.00667425 | 373778 |
| prettier-duplicate-dangling-comments-001 | regression | 20260605-100116-prettier-duplicate-dangling-comments-001-claude-d047a276 | passed | valid |  |  |  | 1 | 11 | 0 | 4011 | 1727561 | 22237 | unknown | 1.7572234999999998 | 322339 |
| prettier-duplicate-dangling-comments-001 | regression | 20260605-100652-prettier-duplicate-dangling-comments-001-claude-69e0fbdd | passed | valid |  |  |  | 1 | 15 | 0 | 3870 | 1282601 | 19730 | unknown | 1.4176885 | 299837 |
| prettier-duplicate-dangling-comments-001 | regression | 20260605-183252-prettier-duplicate-dangling-comments-001-claude-8a104843 | passed | valid |  |  |  | 1 | 11 | 0 | 4025 | 1874918 | 22697 | unknown | 1.8304845000000003 | 336248 |
| react-tabs-selected-focus-overlay-001 | regression | 20260604-113840-react-tabs-selected-focus-overlay-001-claude-254b9850 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 3268 | 75117 | 3268 | unknown | 0.2143215 | 38484 |
| react-tabs-selected-focus-overlay-001 | regression | 20260606-071931-react-tabs-selected-focus-overlay-001-claude-b9a12918 | passed | valid |  |  |  | 3 | 0 | 30 | 3417 | 96550 | 3796 | unknown | 0.2459605 | 51264 |
| react-tabs-selected-focus-overlay-001 | regression | 20260606-071931-react-tabs-selected-focus-overlay-001-claude-e6854948 | passed | valid |  |  |  | 3 | 0 | 30 | 3429 | 232042 | 5706 | unknown | 0.3757777499999999 | 94576 |
| react-tabs-selected-focus-overlay-001 | regression | 20260606-072024-react-tabs-selected-focus-overlay-001-claude-170b4010 | passed | valid |  |  |  | 3 | 0 | 30 | 3421 | 139976 | 4349 | unknown | 0.28619725 | 84105 |
| react-tabs-selected-focus-overlay-001 | regression | 20260606-072108-react-tabs-selected-focus-overlay-001-claude-3cde2925 | passed | valid |  |  |  | 3 | 0 | 30 | 3286 | 75841 | 3197 | unknown | 0.214611 | 41222 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260604-114530-remotion-audio-context-autoplay-muted-001-claude-785a8318 | passed | valid | success_clean | resource_inefficient |  | 2 | 40 | 15 | 3827 | 205845 | 11223 | unknown | 0.62159625 | 128744 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260606-072216-remotion-audio-context-autoplay-muted-001-claude-08e5f4bc | passed | valid |  |  |  | 2 | 41 | 15 | 4115 | 483094 | 17025 | unknown | 0.9562182499999999 | 193730 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260606-072216-remotion-audio-context-autoplay-muted-001-claude-f1d46221 | passed | valid |  |  |  | 2 | 39 | 15 | 4121 | 572050 | 13928 | unknown | 0.8868562499999999 | 165064 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260606-072643-remotion-audio-context-autoplay-muted-001-claude-9dd06eea | passed | valid |  |  |  | 2 | 39 | 15 | 3978 | 297164 | 13011 | unknown | 0.7354482500000001 | 144309 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260606-072746-remotion-audio-context-autoplay-muted-001-claude-449ddc42 | passed | valid |  |  |  | 2 | 35 | 15 | 4119 | 563527 | 15440 | unknown | 0.952541 | 187085 |
| todomvc-toggle-all-checkbox-001 | regression | 20260604-115522-todomvc-toggle-all-checkbox-001-claude-7613ddbd | passed | valid | success_clean |  |  | 4 | 8 | 10 | 3417 | 426337 | 9926 | unknown | 0.6560580000000001 | 123307 |
| todomvc-toggle-all-checkbox-001 | regression | 20260606-073255-todomvc-toggle-all-checkbox-001-claude-bc2594cd | passed | valid |  |  |  | 4 | 6 | 8 | 3713 | 543391 | 10947 | unknown | 0.7109649999999998 | 141435 |
| todomvc-toggle-all-checkbox-001 | regression | 20260606-073255-todomvc-toggle-all-checkbox-001-claude-fce47d77 | passed | valid |  |  |  | 4 | 6 | 8 | 3856 | 909370 | 18448 | unknown | 1.1413819999999997 | 263285 |
| todomvc-toggle-all-checkbox-001 | regression | 20260606-073521-todomvc-toggle-all-checkbox-001-claude-87d8152b | passed | valid |  |  |  | 4 | 6 | 8 | 3564 | 371236 | 10449 | unknown | 0.6233925 | 128907 |
| todomvc-toggle-all-checkbox-001 | regression | 20260606-073722-todomvc-toggle-all-checkbox-001-claude-ee9f0f00 | passed | valid |  |  |  | 4 | 6 | 8 | 3556 | 269248 | 10194 | unknown | 0.5644585 | 122540 |
| vite-deno-workspace-root-001 | regression | 20260604-115750-vite-deno-workspace-root-001-claude-0c83c058 | passed | valid | success_clean |  |  | 6 | 58 | 0 | 3437 | 604593 | 12464 | unknown | 0.7889065000000001 | 165940 |
| vite-deno-workspace-root-001 | regression | 20260606-121430-vite-deno-workspace-root-001-claude-000ac1fa | passed | valid |  |  |  | 6 | 59 | 0 | 3723 | 816229 | 16646 | unknown | 1.03207325 | 219793 |
| vite-deno-workspace-root-001 | regression | 20260606-121430-vite-deno-workspace-root-001-claude-9c267b91 | passed | valid |  |  |  | 6 | 59 | 0 | 3568 | 366774 | 8187 | unknown | 0.53570825 | 119813 |
| vite-deno-workspace-root-001 | regression | 20260606-121635-vite-deno-workspace-root-001-claude-9d3f20b8 | passed | valid |  |  |  | 6 | 50 | 0 | 3584 | 684196 | 13863 | unknown | 0.8880429999999999 | 197502 |
| vite-deno-workspace-root-001 | regression | 20260606-121815-vite-deno-workspace-root-001-claude-bd26b36f | passed | valid |  |  |  | 6 | 63 | 0 | 3584 | 624899 | 13379 | unknown | 0.8300007500000001 | 172172 |
