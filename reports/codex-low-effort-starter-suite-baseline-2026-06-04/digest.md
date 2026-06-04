# Capability Evidence Digest

This digest is generated from stored agent-trial results. It reports evidence only; hand-authored agent capability reports should interpret these observations within the evaluated conditions.

Portable Markdown policy: checked-in digests intentionally omit per-trial artifact links because local `runs/` artifacts are ignored and can disappear after temporary worktree cleanup. HTML reports generated from durable snapshot-backed evidence may be checked in when they pass the same no-local-artifact-link portability check.

- Agent trials: `60`
- Evidence set: `codex-low-effort-starter-suite-baseline-2026-06-04`
- Evidence set source: `evidence-sets/codex-low-effort-starter-suite-baseline-2026-06-04.json`
- Outcome evidence snapshot: `evidence-sets/codex-low-effort-starter-suite-baseline-2026-06-04.outcome-evidence.json`
- Evidence set description: Five fair Codex CLI trials for each of the twelve starter-suite tasks under Issue #63, using gpt-5.5 with requested and recovered reasoning_effort=low. The first click-should-strip-ansi-tests trial was the preflight smoke run; the remaining selected trials were collected sequentially with --trials 5 --jobs 1, except that task's four top-up trials.
- Selected entries: `60`
- Selected result files: `60`
- Selected snapshot records: `60`

## Run Context: starter-coding / codex / gpt-5.5 / low

- Suite: `starter-coding`
- Agent Harness: `codex`
- Model: `gpt-5.5`
- Effort: `low`

### Run Surface

| Execution Surface | Runtime Version | Model Source | Sandbox | Approval | Memory | Network | Timeout Seconds | Stop Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local_cli | codex-cli 0.136.0-alpha.2 | local_codex_state | workspace-write | never | unknown | unknown | 1800 | success |

### Agent Harness Operability

| Operability Dimension | Evidence |
| --- | --- |
| Agent harness configuration | agent_harness: `codex`<br>model: `gpt-5.5`<br>reasoning_effort: `low`<br>trials: `60` |
| Budget controls | timeout_seconds: `1800`<br>turn_or_step_budget: `unknown`<br>observed_input_output_tokens: `60/60`<br>observed_cost_usd: `unknown`<br>configured_token_cost_quota_limits: `unknown` |
| Approval boundaries | sandbox_mode: `workspace-write`<br>approval_policy: `never`<br>tool_policy: `unknown`<br>memory_scope: `unknown`<br>network_policy: `unknown` |
| Verifier state | final_grader_status: `passed`<br>checks_array: `60/60`<br>graders_array: `60/60`<br>intermediate_verifier_movement: `unknown` |
| Halt reasons | normalized_or_derived_stop_reason: `success`<br>first_class_halt_reason_taxonomy: `unknown`<br>error_field: `unknown`<br>budget_operator_interruption_taxonomy: `unknown` |
| Interrupted-run receipt | interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`<br>admission_decision_evidence: `60/60` |
| Tool/patch context | changed_files: `60/60`<br>commands_run: `60/60`<br>human_review_overlay: `60/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |
| Receipt basics | run_dir: `60/60`<br>report_md: `60/60`<br>result_json: `60/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |

### Outcome Summary

| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-help-option-refactor-001 | capability | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-default-map-nargs-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-help-shadowed-option-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-should-strip-ansi-tests-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| datawrapper-mcp-docker-requirements-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| httpx-verify-false-client-cert-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| prettier-duplicate-dangling-comments-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| react-tabs-selected-focus-overlay-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| remotion-audio-context-autoplay-muted-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| todomvc-toggle-all-checkbox-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| vite-deno-workspace-root-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |

### Token Summary

| Task | Type | IO Tokens | Cached Tokens | Reason Tokens | IO Tok / Verified | IO Tok / Accepted | Cached Tok / Verified | Reason Tok / Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 1103228 | 768256 | 1163 | 220645.60 | 220645.60 | 153651.20 | 232.60 |
| click-help-option-refactor-001 | capability | 3000572 | 2623744 | 4399 | 600114.40 | 600114.40 | 524748.80 | 879.80 |
| click-default-map-nargs-001 | regression | 2407792 | 1976192 | 3033 | 481558.40 | 481558.40 | 395238.40 | 606.60 |
| click-help-shadowed-option-001 | regression | 1607985 | 1365888 | 1613 | 321597 | 321597 | 273177.60 | 322.60 |
| click-should-strip-ansi-tests-001 | regression | 779675 | 498816 | 1183 | 155935 | 155935 | 99763.20 | 236.60 |
| datawrapper-mcp-docker-requirements-001 | regression | 464263 | 324480 | 105 | 92852.60 | 92852.60 | 64896 | 21 |
| httpx-verify-false-client-cert-001 | regression | 1148169 | 883456 | 895 | 229633.80 | 229633.80 | 176691.20 | 179 |
| prettier-duplicate-dangling-comments-001 | regression | 3473843 | 3074816 | 2690 | 694768.60 | 694768.60 | 614963.20 | 538 |
| react-tabs-selected-focus-overlay-001 | regression | 599102 | 404352 | 103 | 119820.40 | 119820.40 | 80870.40 | 20.60 |
| remotion-audio-context-autoplay-muted-001 | regression | 1571098 | 1334528 | 1664 | 314219.60 | 314219.60 | 266905.60 | 332.80 |
| todomvc-toggle-all-checkbox-001 | regression | 1295384 | 1071488 | 1132 | 259076.80 | 259076.80 | 214297.60 | 226.40 |
| vite-deno-workspace-root-001 | regression | 1209020 | 928640 | 1430 | 241804 | 241804 | 185728 | 286 |

### Review and Patch Summary

| Task | Type | Median ms | Median Files | Median +Lines | Median -Lines | Primary Review Labels | Secondary Review Labels | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 74896 | 2 | 9 | 7 | success_clean:5 |  |  |
| click-help-option-refactor-001 | capability | 174247 | 3 | 31 | 26 | success_clean:5 | resource_inefficient:2 |  |
| click-default-map-nargs-001 | regression | 110853 | 2 | 76 | 1 | success_clean:5 | resource_inefficient:1 |  |
| click-help-shadowed-option-001 | regression | 97795 | 3 | 52 | 4 | success_clean:5 | resource_inefficient:1 |  |
| click-should-strip-ansi-tests-001 | regression | 62668 | 1 | 28 | 7 | success_clean:5 |  |  |
| datawrapper-mcp-docker-requirements-001 | regression | 36464 | 1 | 5 | 2 | success_clean:5 |  |  |
| httpx-verify-false-client-cert-001 | regression | 77391 | 2 | 25 | 4 | success_clean:5 |  |  |
| prettier-duplicate-dangling-comments-001 | regression | 165417 | 3 | 119 | 0 | success_clean:5 |  |  |
| react-tabs-selected-focus-overlay-001 | regression | 49788 | 3 | 0 | 30 | success_clean:5 |  |  |
| remotion-audio-context-autoplay-muted-001 | regression | 98225 | 2 | 30 | 15 | success_clean:5 |  |  |
| todomvc-toggle-all-checkbox-001 | regression | 65467 | 4 | 6 | 8 | success_clean:5 | resource_inefficient:1 |  |
| vite-deno-workspace-root-001 | regression | 103036 | 6 | 49 | 0 | success_clean:5 |  |  |

### Trial Evidence

| Task | Type | Trial | Grader Outcome | Validity | Primary Review Label | Secondary Review Labels | Exclusion | Files | +Lines | -Lines | Input Tokens | Cached Input Tokens | Output Tokens | Reasoning Tokens | Cost USD | Duration ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| click-should-strip-ansi-tests-001 | regression | 20260603-191424-click-should-strip-ansi-tests-001-codex-964f53c1 | passed | valid | success_clean |  |  | 1 | 70 | 7 | 147890 | 101632 | 2206 | 0 | unknown | 49692 |
| click-should-strip-ansi-tests-001 | regression | 20260603-191935-click-should-strip-ansi-tests-001-codex-7bab70d6 | passed | valid | success_clean |  |  | 1 | 33 | 7 | 174279 | 125056 | 2876 | 301 | unknown | 65403 |
| click-should-strip-ansi-tests-001 | regression | 20260603-192044-click-should-strip-ansi-tests-001-codex-0a97c13c | passed | valid | success_clean |  |  | 1 | 25 | 7 | 152773 | 78592 | 2705 | 287 | unknown | 62668 |
| click-should-strip-ansi-tests-001 | regression | 20260603-192151-click-should-strip-ansi-tests-001-codex-51886a8d | passed | valid | success_clean |  |  | 1 | 27 | 7 | 102300 | 63360 | 2011 | 302 | unknown | 48231 |
| click-should-strip-ansi-tests-001 | regression | 20260603-192243-click-should-strip-ansi-tests-001-codex-3e29db43 | passed | valid | success_clean |  |  | 1 | 28 | 2 | 189641 | 130176 | 2994 | 293 | unknown | 68246 |
| 2048-advanced-snake-params-001 | capability | 20260603-192415-2048-advanced-snake-params-001-codex-5e129991 | passed | valid | success_clean |  |  | 2 | 9 | 7 | 169726 | 137472 | 3369 | 230 | unknown | 74826 |
| 2048-advanced-snake-params-001 | capability | 20260603-192532-2048-advanced-snake-params-001-codex-45b527b8 | passed | valid | success_clean |  |  | 2 | 8 | 6 | 267032 | 172416 | 3433 | 258 | unknown | 87028 |
| 2048-advanced-snake-params-001 | capability | 20260603-192700-2048-advanced-snake-params-001-codex-23549aa9 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 233969 | 174080 | 3620 | 295 | unknown | 81259 |
| 2048-advanced-snake-params-001 | capability | 20260603-192822-2048-advanced-snake-params-001-codex-76e4185d | passed | valid | success_clean |  |  | 2 | 9 | 7 | 232215 | 176128 | 3361 | 235 | unknown | 74896 |
| 2048-advanced-snake-params-001 | capability | 20260603-192938-2048-advanced-snake-params-001-codex-7575f050 | passed | valid | success_clean |  |  | 2 | 8 | 6 | 183502 | 108160 | 3001 | 145 | unknown | 70784 |
| click-default-map-nargs-001 | regression | 20260603-193104-click-default-map-nargs-001-codex-107d9ab0 | passed | valid | success_clean |  |  | 2 | 60 | 0 | 379943 | 315008 | 5085 | 838 | unknown | 123014 |
| click-default-map-nargs-001 | regression | 20260603-193311-click-default-map-nargs-001-codex-f4e64fcc | passed | valid | success_clean | resource_inefficient |  | 2 | 77 | 1 | 827439 | 736000 | 7560 | 895 | unknown | 179367 |
| click-default-map-nargs-001 | regression | 20260603-193614-click-default-map-nargs-001-codex-4a85428e | passed | valid | success_clean |  |  | 2 | 79 | 1 | 456408 | 382336 | 4556 | 516 | unknown | 110853 |
| click-default-map-nargs-001 | regression | 20260603-193809-click-default-map-nargs-001-codex-cc9e2c6f | passed | valid | success_clean |  |  | 2 | 76 | 1 | 353489 | 272640 | 4434 | 454 | unknown | 106667 |
| click-default-map-nargs-001 | regression | 20260603-193959-click-default-map-nargs-001-codex-a7c2ebe1 | passed | valid | success_clean |  |  | 2 | 67 | 0 | 364343 | 270208 | 4535 | 330 | unknown | 103949 |
| click-help-option-refactor-001 | capability | 20260603-194205-click-help-option-refactor-001-codex-f3f25bd7 | passed | valid | success_clean |  |  | 3 | 36 | 27 | 468447 | 414080 | 7396 | 877 | unknown | 174247 |
| click-help-option-refactor-001 | capability | 20260603-194503-click-help-option-refactor-001-codex-efbdc416 | passed | valid | success_clean | resource_inefficient |  | 3 | 43 | 26 | 778946 | 694528 | 8536 | 1180 | unknown | 214715 |
| click-help-option-refactor-001 | capability | 20260603-194842-click-help-option-refactor-001-codex-2fb9de9e | passed | valid | success_clean | resource_inefficient |  | 3 | 30 | 26 | 811846 | 714240 | 8311 | 852 | unknown | 195852 |
| click-help-option-refactor-001 | capability | 20260603-195201-click-help-option-refactor-001-codex-eae57dbd | passed | valid | success_clean |  |  | 3 | 23 | 26 | 435216 | 402432 | 6005 | 1057 | unknown | 142248 |
| click-help-option-refactor-001 | capability | 20260603-195427-click-help-option-refactor-001-codex-47f95ec5 | passed | valid | success_clean |  |  | 3 | 31 | 29 | 470180 | 398464 | 5689 | 433 | unknown | 128780 |
| click-help-shadowed-option-001 | regression | 20260603-195702-click-help-shadowed-option-001-codex-edb0e1e1 | passed | valid | success_clean |  |  | 2 | 52 | 2 | 328618 | 296192 | 4461 | 155 | unknown | 97795 |
| click-help-shadowed-option-001 | regression | 20260603-195843-click-help-shadowed-option-001-codex-95944239 | passed | valid | success_clean |  |  | 3 | 50 | 4 | 209194 | 160640 | 3432 | 345 | unknown | 76023 |
| click-help-shadowed-option-001 | regression | 20260603-200003-click-help-shadowed-option-001-codex-b0f0a32c | passed | valid | success_clean | resource_inefficient |  | 3 | 60 | 9 | 481114 | 432640 | 4783 | 445 | unknown | 112938 |
| click-help-shadowed-option-001 | regression | 20260603-200200-click-help-shadowed-option-001-codex-2e0b2693 | passed | valid | success_clean |  |  | 3 | 56 | 5 | 241608 | 186752 | 3522 | 361 | unknown | 81444 |
| click-help-shadowed-option-001 | regression | 20260603-200325-click-help-shadowed-option-001-codex-1c6cc4db | passed | valid | success_clean |  |  | 3 | 50 | 4 | 326172 | 289664 | 5081 | 307 | unknown | 122719 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260603-200543-datawrapper-mcp-docker-requirements-001-codex-acd8ea8e | passed | valid | success_clean |  |  | 1 | 5 | 2 | 108093 | 86912 | 1706 | 62 | unknown | 38236 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260603-200622-datawrapper-mcp-docker-requirements-001-codex-3d6d9072 | passed | valid | success_clean |  |  | 1 | 5 | 2 | 85902 | 65024 | 1570 | 12 | unknown | 36464 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260603-200700-datawrapper-mcp-docker-requirements-001-codex-c53d8e56 | passed | valid | success_clean |  |  | 1 | 5 | 2 | 85919 | 53248 | 1626 | 7 | unknown | 40657 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260603-200741-datawrapper-mcp-docker-requirements-001-codex-3bc00cc4 | passed | valid | success_clean |  |  | 1 | 5 | 2 | 86249 | 72192 | 1569 | 0 | unknown | 34674 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260603-200817-datawrapper-mcp-docker-requirements-001-codex-8a8429ad | passed | valid | success_clean |  |  | 1 | 5 | 2 | 90032 | 47104 | 1597 | 24 | unknown | 36043 |
| httpx-verify-false-client-cert-001 | regression | 20260603-200907-httpx-verify-false-client-cert-001-codex-8022d66e | passed | valid | success_clean |  |  | 2 | 22 | 4 | 206543 | 154624 | 3028 | 187 | unknown | 70053 |
| httpx-verify-false-client-cert-001 | regression | 20260603-201023-httpx-verify-false-client-cert-001-codex-6fc6c9b4 | passed | valid | success_clean |  |  | 2 | 31 | 4 | 212139 | 156160 | 3603 | 243 | unknown | 77391 |
| httpx-verify-false-client-cert-001 | regression | 20260603-201146-httpx-verify-false-client-cert-001-codex-b8ee812d | passed | valid | success_clean |  |  | 2 | 25 | 4 | 269230 | 218368 | 3828 | 93 | unknown | 99780 |
| httpx-verify-false-client-cert-001 | regression | 20260603-201331-httpx-verify-false-client-cert-001-codex-daf4411c | passed | valid | success_clean |  |  | 2 | 25 | 4 | 163152 | 132864 | 3180 | 92 | unknown | 75227 |
| httpx-verify-false-client-cert-001 | regression | 20260603-201453-httpx-verify-false-client-cert-001-codex-6eef6b70 | passed | valid | success_clean |  |  | 2 | 37 | 4 | 279263 | 221440 | 4203 | 280 | unknown | 95374 |
| prettier-duplicate-dangling-comments-001 | regression | 20260603-201648-prettier-duplicate-dangling-comments-001-codex-25abf60c | passed | valid | success_clean |  |  | 3 | 119 | 0 | 824478 | 762240 | 7130 | 557 | unknown | 165417 |
| prettier-duplicate-dangling-comments-001 | regression | 20260603-201944-prettier-duplicate-dangling-comments-001-codex-78ef41a6 | passed | valid | success_clean |  |  | 3 | 149 | 0 | 611163 | 542336 | 5847 | 347 | unknown | 145538 |
| prettier-duplicate-dangling-comments-001 | regression | 20260603-202219-prettier-duplicate-dangling-comments-001-codex-339f55f5 | passed | valid | success_clean |  |  | 3 | 117 | 0 | 631384 | 547840 | 5980 | 637 | unknown | 143271 |
| prettier-duplicate-dangling-comments-001 | regression | 20260603-202453-prettier-duplicate-dangling-comments-001-codex-6c28e677 | passed | valid | success_clean |  |  | 3 | 119 | 0 | 742301 | 688896 | 7111 | 615 | unknown | 176328 |
| prettier-duplicate-dangling-comments-001 | regression | 20260603-202801-prettier-duplicate-dangling-comments-001-codex-81faebf8 | passed | valid | success_clean |  |  | 3 | 119 | 0 | 631109 | 533504 | 7340 | 534 | unknown | 171344 |
| react-tabs-selected-focus-overlay-001 | regression | 20260603-203114-react-tabs-selected-focus-overlay-001-codex-de6cf8c4 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 111258 | 66944 | 2251 | 8 | unknown | 48562 |
| react-tabs-selected-focus-overlay-001 | regression | 20260603-203204-react-tabs-selected-focus-overlay-001-codex-b9d5496b | passed | valid | success_clean |  |  | 3 | 0 | 30 | 119105 | 94080 | 2483 | 37 | unknown | 55002 |
| react-tabs-selected-focus-overlay-001 | regression | 20260603-203301-react-tabs-selected-focus-overlay-001-codex-7cc6dfd6 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 118232 | 70016 | 2146 | 29 | unknown | 49063 |
| react-tabs-selected-focus-overlay-001 | regression | 20260603-203351-react-tabs-selected-focus-overlay-001-codex-904df909 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 116684 | 70016 | 2104 | 8 | unknown | 49788 |
| react-tabs-selected-focus-overlay-001 | regression | 20260603-203443-react-tabs-selected-focus-overlay-001-codex-4e1c6299 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 122547 | 103296 | 2292 | 21 | unknown | 52049 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260603-203551-remotion-audio-context-autoplay-muted-001-codex-d72792a0 | passed | valid | success_clean |  |  | 2 | 29 | 15 | 279382 | 211840 | 4367 | 340 | unknown | 98225 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260603-203847-remotion-audio-context-autoplay-muted-001-codex-d2ac1422 | passed | valid | success_clean |  |  | 2 | 30 | 14 | 416355 | 376704 | 5275 | 229 | unknown | 126807 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260603-204211-remotion-audio-context-autoplay-muted-001-codex-5e1e35f3 | passed | valid | success_clean |  |  | 2 | 27 | 15 | 279768 | 243072 | 4169 | 254 | unknown | 97854 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260603-204503-remotion-audio-context-autoplay-muted-001-codex-aa6afefc | passed | valid | success_clean |  |  | 2 | 36 | 15 | 178312 | 145152 | 3187 | 178 | unknown | 74815 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260603-204747-remotion-audio-context-autoplay-muted-001-codex-88d1c094 | passed | valid | success_clean |  |  | 2 | 33 | 15 | 393186 | 357760 | 7097 | 663 | unknown | 156103 |
| todomvc-toggle-all-checkbox-001 | regression | 20260603-205231-todomvc-toggle-all-checkbox-001-codex-f53ce739 | passed | valid | success_clean |  |  | 4 | 6 | 8 | 159936 | 131328 | 2798 | 27 | unknown | 61960 |
| todomvc-toggle-all-checkbox-001 | regression | 20260603-205336-todomvc-toggle-all-checkbox-001-codex-1a544425 | passed | valid | success_clean |  |  | 4 | 18 | 20 | 367596 | 300032 | 6087 | 413 | unknown | 131582 |
| todomvc-toggle-all-checkbox-001 | regression | 20260603-205552-todomvc-toggle-all-checkbox-001-codex-3536e1ec | passed | valid | success_clean |  |  | 4 | 8 | 10 | 163316 | 122112 | 2833 | 38 | unknown | 65467 |
| todomvc-toggle-all-checkbox-001 | regression | 20260603-205701-todomvc-toggle-all-checkbox-001-codex-3e5ccc45 | passed | valid | success_clean | resource_inefficient |  | 4 | 6 | 8 | 424431 | 388736 | 8137 | 629 | unknown | 184822 |
| todomvc-toggle-all-checkbox-001 | regression | 20260603-210009-todomvc-toggle-all-checkbox-001-codex-d7f5350a | passed | valid | success_clean |  |  | 4 | 6 | 8 | 157616 | 129280 | 2634 | 25 | unknown | 60362 |
| vite-deno-workspace-root-001 | regression | 20260603-210128-vite-deno-workspace-root-001-codex-81cfb9db | passed | valid | success_clean |  |  | 6 | 48 | 0 | 236429 | 182656 | 4139 | 121 | unknown | 96183 |
| vite-deno-workspace-root-001 | regression | 20260603-210308-vite-deno-workspace-root-001-codex-457a5b61 | passed | valid | success_clean |  |  | 6 | 49 | 0 | 202777 | 177536 | 4294 | 173 | unknown | 96679 |
| vite-deno-workspace-root-001 | regression | 20260603-210450-vite-deno-workspace-root-001-codex-b92b8e99 | passed | valid | success_clean |  |  | 6 | 53 | 0 | 257228 | 194944 | 6415 | 346 | unknown | 136116 |
| vite-deno-workspace-root-001 | regression | 20260603-210710-vite-deno-workspace-root-001-codex-13624836 | passed | valid | success_clean |  |  | 6 | 49 | 0 | 246274 | 186240 | 5318 | 578 | unknown | 123320 |
| vite-deno-workspace-root-001 | regression | 20260603-210917-vite-deno-workspace-root-001-codex-52a10bca | passed | valid | success_clean |  |  | 6 | 48 | 0 | 241474 | 187264 | 4672 | 212 | unknown | 103036 |
