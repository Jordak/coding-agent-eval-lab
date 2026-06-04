# Capability Evidence Digest

This digest is generated from stored agent-trial results. It reports evidence only; hand-authored agent capability reports should interpret these observations within the evaluated conditions.

Portable Markdown policy: checked-in digests intentionally omit per-trial artifact links because local `runs/` artifacts are ignored and can disappear after temporary worktree cleanup. HTML reports generated from durable snapshot-backed evidence may be checked in when they pass the same no-local-artifact-link portability check.

- Agent trials: `60`
- Evidence set: `codex-starter-suite-12-task-baseline-2026-05-11`
- Evidence set source: `evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json`
- Outcome evidence snapshot: `evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.outcome-evidence.json`
- Evidence set description: Five fair Codex CLI trials for each of the twelve starter-suite tasks under Issue #10. Extends the 2026-05-09 nine-task baseline with Prettier, Vite, and Remotion trials collected on 2026-05-11.
- Selected entries: `60`
- Selected result files: `60`
- Selected snapshot records: `60`

## Run Context: starter-coding / codex / gpt-5.5 / xhigh

- Suite: `starter-coding`
- Agent Harness: `codex`
- Model: `gpt-5.5`
- Effort: `xhigh`

### Run Surface

| Execution Surface | Runtime Version | Model Source | Sandbox | Approval | Memory | Network | Timeout Seconds | Stop Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local_cli | unknown | recovered_from_checked_in_digest | unknown | unknown | unknown | unknown | unknown | success |

### Agent Harness Operability

| Operability Dimension | Evidence |
| --- | --- |
| Agent harness configuration | agent_harness: `codex`<br>model: `gpt-5.5`<br>reasoning_effort: `xhigh`<br>trials: `60` |
| Budget controls | timeout_seconds: `unknown`<br>turn_or_step_budget: `unknown`<br>observed_input_output_tokens: `60/60`<br>observed_cost_usd: `unknown`<br>configured_token_cost_quota_limits: `unknown` |
| Approval boundaries | sandbox_mode: `unknown`<br>approval_policy: `unknown`<br>tool_policy: `unknown`<br>memory_scope: `unknown`<br>network_policy: `unknown` |
| Verifier state | final_grader_status: `passed`<br>checks_array: `60/60`<br>graders_array: `60/60`<br>intermediate_verifier_movement: `unknown` |
| Halt reasons | normalized_or_derived_stop_reason: `success`<br>first_class_halt_reason_taxonomy: `unknown`<br>error_field: `unknown`<br>budget_operator_interruption_taxonomy: `unknown` |
| Interrupted-run receipt | interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`<br>admission_decision_evidence: `60/60` |
| Tool/patch context | changed_files: `60/60`<br>commands_run: `60/60`<br>human_review_overlay: `60/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |
| Receipt basics | run_dir: `60/60`<br>report_md: `60/60`<br>result_json: `60/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |

### Outcome Summary

| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-help-option-refactor-001 | capability | 5 | 5 | 0 | 5 | 4 | 1.00 | 1.00 | 1.00 |
| click-default-map-nargs-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-help-shadowed-option-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| click-should-strip-ansi-tests-001 | regression | 5 | 5 | 0 | 5 | 4 | 1.00 | 1.00 | 1.00 |
| datawrapper-mcp-docker-requirements-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| httpx-verify-false-client-cert-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| prettier-duplicate-dangling-comments-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| react-tabs-selected-focus-overlay-001 | regression | 5 | 5 | 0 | 5 | 3 | 1.00 | 1.00 | 1.00 |
| remotion-audio-context-autoplay-muted-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| todomvc-toggle-all-checkbox-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |
| vite-deno-workspace-root-001 | regression | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |

### Token Summary

| Task | Type | IO Tokens | Cached Tokens | Reason Tokens | IO Tok / Verified | IO Tok / Accepted | Cached Tok / Verified | Reason Tok / Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 1831753 | unknown | 8504 | 366350.60 | 366350.60 | unknown | 1700.80 |
| click-help-option-refactor-001 | capability | 6357302 | unknown | 36115 | 1271460.40 | 1589325.50 | unknown | 7223 |
| click-default-map-nargs-001 | regression | 7198021 | unknown | 31492 | 1439604.20 | 1439604.20 | unknown | 6298.40 |
| click-help-shadowed-option-001 | regression | 5699991 | unknown | 20826 | 1139998.20 | 1139998.20 | unknown | 4165.20 |
| click-should-strip-ansi-tests-001 | regression | 1072584 | unknown | 6502 | 214516.80 | 268146 | unknown | 1300.40 |
| datawrapper-mcp-docker-requirements-001 | regression | 576588 | unknown | 2371 | 115317.60 | 115317.60 | unknown | 474.20 |
| httpx-verify-false-client-cert-001 | regression | 2114903 | unknown | 10204 | 422980.60 | 422980.60 | unknown | 2040.80 |
| prettier-duplicate-dangling-comments-001 | regression | 9398657 | unknown | 24786 | 1879731.40 | 1879731.40 | unknown | 4957.20 |
| react-tabs-selected-focus-overlay-001 | regression | 524466 | unknown | 663 | 104893.20 | 174822 | unknown | 132.60 |
| remotion-audio-context-autoplay-muted-001 | regression | 3990120 | unknown | 23370 | 798024 | 798024 | unknown | 4674 |
| todomvc-toggle-all-checkbox-001 | regression | 1106108 | unknown | 4644 | 221221.60 | 221221.60 | unknown | 928.80 |
| vite-deno-workspace-root-001 | regression | 1956082 | unknown | 17108 | 391216.40 | 391216.40 | unknown | 3421.60 |

### Review and Patch Summary

| Task | Type | Median ms | Median Files | Median +Lines | Median -Lines | Primary Review Labels | Secondary Review Labels | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 122522 | 2 | 11 | 7 | success_clean:5 |  |  |
| click-help-option-refactor-001 | capability | 348321 | 3 | 39 | 27 | resource_inefficient:1, success_clean:4 | resource_inefficient:4 |  |
| click-default-map-nargs-001 | regression | 273731 | 2 | 80 | 1 | success_clean:5 |  |  |
| click-help-shadowed-option-001 | regression | 274698 | 3 | 61 | 12 | success_clean:5 |  |  |
| click-should-strip-ansi-tests-001 | regression | 99158 | 1 | 34 | 2 | success_clean:4, success_messy:1 |  |  |
| datawrapper-mcp-docker-requirements-001 | regression | 46696 | 1 | 5 | 2 | success_clean:5 |  |  |
| httpx-verify-false-client-cert-001 | regression | 139464 | 2 | 26 | 4 | success_clean:5 |  |  |
| prettier-duplicate-dangling-comments-001 | regression | 298903 | 1 | 11 | 0 | success_clean:5 | resource_inefficient:5 |  |
| react-tabs-selected-focus-overlay-001 | regression | 46198 | 3 | 0 | 30 | resource_inefficient:2, success_clean:3 |  |  |
| remotion-audio-context-autoplay-muted-001 | regression | 243349 | 2 | 27 | 15 | success_clean:5 | resource_inefficient:5 |  |
| todomvc-toggle-all-checkbox-001 | regression | 92557 | 4 | 6 | 8 | success_clean:5 |  |  |
| vite-deno-workspace-root-001 | regression | 202990 | 6 | 61 | 0 | success_clean:5 |  |  |

### Trial Evidence

| Task | Type | Trial | Grader Outcome | Validity | Primary Review Label | Secondary Review Labels | Exclusion | Files | +Lines | -Lines | Input Tokens | Cached Input Tokens | Output Tokens | Reasoning Tokens | Cost USD | Duration ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 20260508-192558-2048-advanced-snake-params-001-codex-a24c0d88 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 369730 | unknown | 5878 | 1770 | unknown | 123947 |
| 2048-advanced-snake-params-001 | capability | 20260508-192836-2048-advanced-snake-params-001-codex-852468e7 | passed | valid | success_clean |  |  | 2 | 12 | 7 | 405265 | unknown | 5973 | 2179 | unknown | 127637 |
| 2048-advanced-snake-params-001 | capability | 20260508-192836-2048-advanced-snake-params-001-codex-c28086a4 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 263850 | unknown | 4390 | 1366 | unknown | 96705 |
| 2048-advanced-snake-params-001 | capability | 20260508-192836-2048-advanced-snake-params-001-codex-f9940a53 | passed | valid | success_clean |  |  | 2 | 9 | 7 | 390176 | unknown | 5396 | 1602 | unknown | 122522 |
| 2048-advanced-snake-params-001 | capability | 20260508-193138-2048-advanced-snake-params-001-codex-036d2392 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 375823 | unknown | 5272 | 1587 | unknown | 114274 |
| click-help-option-refactor-001 | capability | 20260508-231553-click-help-option-refactor-001-codex-595ac36a | passed | valid | resource_inefficient |  |  | 3 | 39 | 27 | 1330105 | unknown | 16870 | 9809 | unknown | 348321 |
| click-help-option-refactor-001 | capability | 20260509-003039-click-help-option-refactor-001-codex-06c9c997 | passed | valid | success_clean | resource_inefficient |  | 3 | 49 | 27 | 1441571 | unknown | 16383 | 5276 | unknown | 403027 |
| click-help-option-refactor-001 | capability | 20260509-003039-click-help-option-refactor-001-codex-d7135962 | passed | valid | success_clean | resource_inefficient |  | 3 | 39 | 26 | 1400170 | unknown | 15950 | 7071 | unknown | 372053 |
| click-help-option-refactor-001 | capability | 20260509-003657-click-help-option-refactor-001-codex-50edac8f | passed | valid | success_clean | resource_inefficient |  | 3 | 39 | 29 | 1178622 | unknown | 14544 | 6089 | unknown | 337320 |
| click-help-option-refactor-001 | capability | 20260509-003728-click-help-option-refactor-001-codex-14783133 | passed | valid | success_clean | resource_inefficient |  | 3 | 52 | 28 | 928411 | unknown | 14676 | 7870 | unknown | 307697 |
| click-default-map-nargs-001 | regression | 20260507-191800-click-default-map-nargs-001-codex-f8be8394 | passed | valid | success_clean |  |  | 2 | 63 | 5 | 1135797 | unknown | 10862 | 4590 | unknown | 241069 |
| click-default-map-nargs-001 | regression | 20260507-212911-click-default-map-nargs-001-codex-59243485 | passed | valid | success_clean |  |  | 2 | 79 | 4 | 1022767 | unknown | 10964 | 5787 | unknown | 249893 |
| click-default-map-nargs-001 | regression | 20260507-212911-click-default-map-nargs-001-codex-953cf220 | passed | valid | success_clean |  |  | 2 | 97 | 1 | 2614558 | unknown | 18716 | 9239 | unknown | 425133 |
| click-default-map-nargs-001 | regression | 20260507-212911-click-default-map-nargs-001-codex-a2253130 | passed | valid | success_clean |  |  | 2 | 105 | 1 | 1198406 | unknown | 12987 | 5967 | unknown | 280520 |
| click-default-map-nargs-001 | regression | 20260508-233845-click-default-map-nargs-001-codex-e436b67c | passed | valid | success_clean |  |  | 2 | 80 | 0 | 1160085 | unknown | 12879 | 5909 | unknown | 273731 |
| click-help-shadowed-option-001 | regression | 20260507-175243-click-help-shadowed-option-001-codex | passed | valid | success_clean |  |  | 3 | 64 | 12 | 887475 | unknown | 13544 | 4843 | unknown | 284582 |
| click-help-shadowed-option-001 | regression | 20260507-183521-click-help-shadowed-option-001-codex-20f74f8c | passed | valid | success_clean |  |  | 3 | 55 | 12 | 1273526 | unknown | 14889 | 4294 | unknown | 313434 |
| click-help-shadowed-option-001 | regression | 20260507-183521-click-help-shadowed-option-001-codex-b0c8e35f | passed | valid | success_clean |  |  | 3 | 59 | 9 | 861011 | unknown | 10128 | 3359 | unknown | 234537 |
| click-help-shadowed-option-001 | regression | 20260507-183521-click-help-shadowed-option-001-codex-d191b2b5 | passed | valid | success_clean |  |  | 3 | 68 | 12 | 1376977 | unknown | 11285 | 3945 | unknown | 274698 |
| click-help-shadowed-option-001 | regression | 20260507-192403-click-help-shadowed-option-001-codex-c0a854fe | passed | valid | success_clean |  |  | 3 | 61 | 12 | 1239279 | unknown | 11877 | 4385 | unknown | 257231 |
| click-should-strip-ansi-tests-001 | regression | 20260508-233623-click-should-strip-ansi-tests-001-codex-0ea41a6d | passed | valid | success_clean |  |  | 1 | 34 | 2 | 221487 | unknown | 4189 | 1175 | unknown | 99158 |
| click-should-strip-ansi-tests-001 | regression | 20260509-002547-click-should-strip-ansi-tests-001-codex-4902f3ad | passed | valid | success_clean |  |  | 1 | 35 | 2 | 170118 | unknown | 3715 | 1328 | unknown | 78897 |
| click-should-strip-ansi-tests-001 | regression | 20260509-002547-click-should-strip-ansi-tests-001-codex-6cf5bb2a | passed | valid | success_clean |  |  | 1 | 65 | 0 | 259419 | unknown | 3740 | 335 | unknown | 132639 |
| click-should-strip-ansi-tests-001 | regression | 20260509-002711-click-should-strip-ansi-tests-001-codex-3842bbe6 | passed | valid | success_clean |  |  | 1 | 30 | 2 | 213055 | unknown | 5126 | 1954 | unknown | 103015 |
| click-should-strip-ansi-tests-001 | regression | 20260509-002805-click-should-strip-ansi-tests-001-codex-4bb77432 | passed | valid | success_messy |  |  | 1 | 28 | 7 | 187775 | unknown | 3960 | 1710 | unknown | 82525 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260508-233002-datawrapper-mcp-docker-requirements-001-codex-15c694da | passed | valid | success_clean |  |  | 1 | 5 | 2 | 96997 | unknown | 2053 | 496 | unknown | 46696 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260509-001658-datawrapper-mcp-docker-requirements-001-codex-848ab9d3 | passed | valid | success_clean |  |  | 1 | 8 | 3 | 119124 | unknown | 2518 | 552 | unknown | 55542 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260509-001658-datawrapper-mcp-docker-requirements-001-codex-b7a852cd | passed | valid | success_clean |  |  | 1 | 5 | 2 | 97067 | unknown | 1655 | 234 | unknown | 37809 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260509-001737-datawrapper-mcp-docker-requirements-001-codex-fb93677c | passed | valid | success_clean |  |  | 1 | 5 | 2 | 94965 | unknown | 1785 | 201 | unknown | 38142 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260509-001754-datawrapper-mcp-docker-requirements-001-codex-8c000cc0 | passed | valid | success_clean |  |  | 1 | 9 | 4 | 157442 | unknown | 2982 | 888 | unknown | 66821 |
| httpx-verify-false-client-cert-001 | regression | 20260508-233323-httpx-verify-false-client-cert-001-codex-48157a76 | passed | valid | success_clean |  |  | 2 | 26 | 4 | 362140 | unknown | 6049 | 1884 | unknown | 139464 |
| httpx-verify-false-client-cert-001 | regression | 20260509-001950-httpx-verify-false-client-cert-001-codex-30f0598a | passed | valid | success_clean |  |  | 2 | 26 | 4 | 331716 | unknown | 5618 | 1750 | unknown | 122320 |
| httpx-verify-false-client-cert-001 | regression | 20260509-001950-httpx-verify-false-client-cert-001-codex-9340e11f | passed | valid | success_clean |  |  | 2 | 47 | 4 | 454235 | unknown | 7768 | 2830 | unknown | 167652 |
| httpx-verify-false-client-cert-001 | regression | 20260509-002205-httpx-verify-false-client-cert-001-codex-00fabb3b | passed | valid | success_clean |  |  | 2 | 26 | 4 | 485440 | unknown | 7450 | 1936 | unknown | 162229 |
| httpx-verify-false-client-cert-001 | regression | 20260509-002250-httpx-verify-false-client-cert-001-codex-de36837b | passed | valid | success_clean |  |  | 2 | 26 | 4 | 448399 | unknown | 6088 | 1804 | unknown | 129760 |
| react-tabs-selected-focus-overlay-001 | regression | 20260508-232845-react-tabs-selected-focus-overlay-001-codex-3aff2262 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 84591 | unknown | 1727 | 205 | unknown | 46198 |
| react-tabs-selected-focus-overlay-001 | regression | 20260508-234737-react-tabs-selected-focus-overlay-001-codex-0b27f904 | passed | valid | success_clean |  |  | 3 | 0 | 30 | 86417 | unknown | 1543 | 153 | unknown | 40061 |
| react-tabs-selected-focus-overlay-001 | regression | 20260508-234737-react-tabs-selected-focus-overlay-001-codex-5fb1524e | passed | valid | success_clean |  |  | 3 | 0 | 30 | 106666 | unknown | 1788 | 133 | unknown | 40183 |
| react-tabs-selected-focus-overlay-001 | regression | 20260508-234819-react-tabs-selected-focus-overlay-001-codex-9deb6294 | passed | valid | resource_inefficient |  |  | 3 | 0 | 30 | 131976 | unknown | 1746 | 75 | unknown | 353860 |
| react-tabs-selected-focus-overlay-001 | regression | 20260508-234819-react-tabs-selected-focus-overlay-001-codex-de0c8846 | passed | valid | resource_inefficient |  |  | 3 | 0 | 30 | 106201 | unknown | 1811 | 97 | unknown | 348556 |
| todomvc-toggle-all-checkbox-001 | regression | 20260508-212455-todomvc-toggle-all-checkbox-001-codex-6370c97d | passed | valid | success_clean |  |  | 4 | 8 | 10 | 368614 | unknown | 5896 | 1563 | unknown | 124925 |
| todomvc-toggle-all-checkbox-001 | regression | 20260508-234354-todomvc-toggle-all-checkbox-001-codex-60445af9 | passed | valid | success_clean |  |  | 4 | 6 | 8 | 195351 | unknown | 4587 | 1361 | unknown | 92557 |
| todomvc-toggle-all-checkbox-001 | regression | 20260508-234354-todomvc-toggle-all-checkbox-001-codex-f253bfc3 | passed | valid | success_clean |  |  | 4 | 6 | 8 | 137636 | unknown | 2465 | 283 | unknown | 57581 |
| todomvc-toggle-all-checkbox-001 | regression | 20260508-234457-todomvc-toggle-all-checkbox-001-codex-f96b370e | passed | valid | success_clean |  |  | 4 | 8 | 10 | 235188 | unknown | 4380 | 958 | unknown | 93170 |
| todomvc-toggle-all-checkbox-001 | regression | 20260508-234532-todomvc-toggle-all-checkbox-001-codex-a0ea494a | passed | valid | success_clean |  |  | 4 | 6 | 8 | 149132 | unknown | 2859 | 479 | unknown | 65031 |
| prettier-duplicate-dangling-comments-001 | regression | 20260511-120602-prettier-duplicate-dangling-comments-001-codex-bf3fb709 | passed | valid | success_clean | resource_inefficient |  | 1 | 36 | 4 | 2154851 | unknown | 12572 | 4320 | unknown | 298903 |
| prettier-duplicate-dangling-comments-001 | regression | 20260511-170522-prettier-duplicate-dangling-comments-001-codex-63f77d20 | passed | valid | success_clean | resource_inefficient |  | 3 | 149 | 0 | 1256412 | unknown | 10441 | 3358 | unknown | 225825 |
| prettier-duplicate-dangling-comments-001 | regression | 20260511-170522-prettier-duplicate-dangling-comments-001-codex-c9fa6a68 | passed | valid | success_clean | resource_inefficient |  | 1 | 9 | 0 | 2022503 | unknown | 18375 | 6647 | unknown | 380910 |
| prettier-duplicate-dangling-comments-001 | regression | 20260511-170924-prettier-duplicate-dangling-comments-001-codex-21c6e88c | passed | valid | success_clean | resource_inefficient |  | 1 | 9 | 0 | 2242758 | unknown | 12923 | 4944 | unknown | 309556 |
| prettier-duplicate-dangling-comments-001 | regression | 20260511-171200-prettier-duplicate-dangling-comments-001-codex-5e66b137 | passed | valid | success_clean | resource_inefficient |  | 1 | 11 | 0 | 1654662 | unknown | 13160 | 5517 | unknown | 292824 |
| vite-deno-workspace-root-001 | regression | 20260511-135357-vite-deno-workspace-root-001-codex-4979b435 | passed | valid | success_clean |  |  | 6 | 57 | 0 | 385298 | unknown | 11592 | 4357 | unknown | 243183 |
| vite-deno-workspace-root-001 | regression | 20260511-171727-vite-deno-workspace-root-001-codex-1f24f54e | passed | valid | success_clean |  |  | 6 | 62 | 0 | 443478 | unknown | 10183 | 3926 | unknown | 215109 |
| vite-deno-workspace-root-001 | regression | 20260511-171727-vite-deno-workspace-root-001-codex-900dde55 | passed | valid | success_clean |  |  | 6 | 65 | 0 | 296487 | unknown | 7378 | 2617 | unknown | 146945 |
| vite-deno-workspace-root-001 | regression | 20260511-171959-vite-deno-workspace-root-001-codex-11755fe8 | passed | valid | success_clean |  |  | 6 | 61 | 0 | 431838 | unknown | 8293 | 3007 | unknown | 176534 |
| vite-deno-workspace-root-001 | regression | 20260511-172107-vite-deno-workspace-root-001-codex-68b63134 | passed | valid | success_clean |  |  | 6 | 59 | 0 | 351303 | unknown | 10232 | 3201 | unknown | 202990 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260511-121728-remotion-audio-context-autoplay-muted-001-codex-1e523620 | passed | valid | success_clean | resource_inefficient |  | 2 | 30 | 15 | 1053617 | unknown | 13347 | 6314 | unknown | 298649 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260511-172451-remotion-audio-context-autoplay-muted-001-codex-ad200495 | passed | valid | success_clean | resource_inefficient |  | 2 | 25 | 15 | 865930 | unknown | 10616 | 4475 | unknown | 243349 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260511-172451-remotion-audio-context-autoplay-muted-001-codex-8f9ec1e4 | passed | valid | success_clean | resource_inefficient |  | 2 | 31 | 15 | 879535 | unknown | 11650 | 6010 | unknown | 247901 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260511-173056-remotion-audio-context-autoplay-muted-001-codex-4610ab91 | passed | valid | success_clean | resource_inefficient |  | 2 | 27 | 15 | 601668 | unknown | 8807 | 3770 | unknown | 186714 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260511-173100-remotion-audio-context-autoplay-muted-001-codex-00c2dd9b | passed | valid | success_clean | resource_inefficient |  | 2 | 27 | 15 | 537209 | unknown | 7741 | 2801 | unknown | 170188 |
