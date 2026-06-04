# Capability Evidence Digest

This digest is generated from stored agent-trial results. It reports evidence only; hand-authored agent capability reports should interpret these observations within the evaluated conditions.

Portable Markdown policy: checked-in digests intentionally omit per-trial artifact links because local `runs/` artifacts are ignored and can disappear after temporary worktree cleanup. HTML reports generated from durable snapshot-backed evidence may be checked in when they pass the same no-local-artifact-link portability check.

- Agent trials: `60`
- Evidence set: `Claude Code starter suite baseline, 12 tasks, 5 fair trials per task, 2026-05-14`
- Evidence set source: `evidence-sets/claude-code-starter-suite-baseline-2026-05-14.json`
- Outcome evidence snapshot: `evidence-sets/claude-code-starter-suite-baseline-2026-05-14.outcome-evidence.json`
- Evidence set description: Evidence set for GitHub issue #53. Contains 60 valid Claude Code fair trials across the 12 starter-suite tasks. Quota-hit/operator-error runs are preserved under runs/ but excluded from this manifest. Baseline config: --agent claude --claude-model claude-haiku-4-5-20251001 --claude-permission-mode acceptEdits --claude-output-format stream-json --claude-timeout-seconds 1800, no max turns.
- Selected entries: `60`
- Selected result files: `60`
- Selected snapshot records: `60`

## Run Context: starter-coding / claude / claude-haiku-4-5-20251001 / unknown

- Suite: `starter-coding`
- Agent Harness: `claude`
- Model: `claude-haiku-4-5-20251001`
- Effort: `unknown`

### Run Surface

| Execution Surface | Runtime Version | Model Source | Sandbox | Approval | Memory | Network | Timeout Seconds | Stop Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local_cli | unknown | recovered_from_checked_in_digest | unknown | acceptEdits | unknown | unknown | 1800 | mixed: success; unknown |

### Agent Harness Operability

| Operability Dimension | Evidence |
| --- | --- |
| Agent harness configuration | agent_harness: `claude`<br>model: `claude-haiku-4-5-20251001`<br>reasoning_effort: `unknown`<br>trials: `60` |
| Budget controls | timeout_seconds: `1800`<br>turn_or_step_budget: `unknown`<br>observed_input_output_tokens: `60/60`<br>observed_cost_usd: `60/60`<br>configured_token_cost_quota_limits: `unknown` |
| Approval boundaries | sandbox_mode: `unknown`<br>approval_policy: `acceptEdits`<br>tool_policy: `unknown`<br>memory_scope: `unknown`<br>network_policy: `unknown` |
| Verifier state | final_grader_status: `failed; passed`<br>checks_array: `60/60`<br>graders_array: `60/60`<br>intermediate_verifier_movement: `unknown` |
| Halt reasons | normalized_or_derived_stop_reason: `success; unknown in 7/60`<br>first_class_halt_reason_taxonomy: `unknown`<br>error_field: `unknown`<br>budget_operator_interruption_taxonomy: `unknown` |
| Interrupted-run receipt | interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`<br>admission_decision_evidence: `12/60` |
| Tool/patch context | changed_files: `60/60`<br>commands_run: `60/60`<br>human_review_overlay: `12/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |
| Receipt basics | run_dir: `60/60`<br>report_md: `60/60`<br>result_json: `60/60`<br>transcript: `60/60`<br>diff_patch: `60/60` |

### Outcome Summary

| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 5 | 5 | 0 | 5 | 0 | 1.00 | 1.00 | 1.00 |
| click-help-option-refactor-001 | capability | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| click-default-map-nargs-001 | regression | 5 | 5 | 0 | 5 | 2 | 1.00 | 1.00 | 1.00 |
| click-help-shadowed-option-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| click-should-strip-ansi-tests-001 | regression | 5 | 5 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 |
| datawrapper-mcp-docker-requirements-001 | regression | 5 | 5 | 0 | 5 | 0 | 1.00 | 1.00 | 1.00 |
| httpx-verify-false-client-cert-001 | regression | 5 | 5 | 0 | 5 | 0 | 1.00 | 1.00 | 1.00 |
| prettier-duplicate-dangling-comments-001 | regression | 5 | 5 | 0 | 5 | 1 | 1.00 | 1.00 | 1.00 |
| react-tabs-selected-focus-overlay-001 | regression | 5 | 5 | 0 | 5 | 0 | 1.00 | 1.00 | 1.00 |
| remotion-audio-context-autoplay-muted-001 | regression | 5 | 5 | 0 | 3 | 0 | 0.60 | 1.00 | 0.00 |
| todomvc-toggle-all-checkbox-001 | regression | 5 | 5 | 0 | 5 | 0 | 1.00 | 1.00 | 1.00 |
| vite-deno-workspace-root-001 | regression | 5 | 5 | 0 | 5 | 0 | 1.00 | 1.00 | 1.00 |

### Token Summary

| Task | Type | IO Tokens | Cached Tokens | Reason Tokens | IO Tok / Verified | IO Tok / Accepted | Cached Tok / Verified | Reason Tok / Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 36701 | unknown | unknown | 7340.20 | unknown | unknown | unknown |
| click-help-option-refactor-001 | capability | 100443 | unknown | unknown | 20088.60 | 100443 | unknown | unknown |
| click-default-map-nargs-001 | regression | 103530 | unknown | unknown | 20706 | 51765 | unknown | unknown |
| click-help-shadowed-option-001 | regression | 100762 | unknown | unknown | 20152.40 | 100762 | unknown | unknown |
| click-should-strip-ansi-tests-001 | regression | 76893 | unknown | unknown | unknown | unknown | unknown | unknown |
| datawrapper-mcp-docker-requirements-001 | regression | 21736 | unknown | unknown | 4347.20 | unknown | unknown | unknown |
| httpx-verify-false-client-cert-001 | regression | 43647 | unknown | unknown | 8729.40 | unknown | unknown | unknown |
| prettier-duplicate-dangling-comments-001 | regression | 85087 | unknown | unknown | 17017.40 | 85087 | unknown | unknown |
| react-tabs-selected-focus-overlay-001 | regression | 22504 | unknown | unknown | 4500.80 | unknown | unknown | unknown |
| remotion-audio-context-autoplay-muted-001 | regression | 64933 | unknown | unknown | 21644.33 | unknown | unknown | unknown |
| todomvc-toggle-all-checkbox-001 | regression | 52808 | unknown | unknown | 10561.60 | unknown | unknown | unknown |
| vite-deno-workspace-root-001 | regression | 76126 | unknown | unknown | 15225.20 | unknown | unknown | unknown |

### Review and Patch Summary

| Task | Type | Median ms | Median Files | Median +Lines | Median -Lines | Primary Review Labels | Secondary Review Labels | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 64279 | 2 | 6 | 6 |  |  |  |
| click-help-option-refactor-001 | capability | 194851 | 3 | 38 | 28 | success_clean:1 | resource_inefficient:1 |  |
| click-default-map-nargs-001 | regression | 216856 | 1 | 14 | 0 | success_clean:2 | resource_inefficient:2 |  |
| click-help-shadowed-option-001 | regression | 211586 | 1 | 7 | 8 | success_clean:1 | resource_inefficient:1 |  |
| click-should-strip-ansi-tests-001 | regression | 99401 | 1 | 54 | 1 | bad_local_fix:5 | test_gap:5 |  |
| datawrapper-mcp-docker-requirements-001 | regression | 45710 | 1 | 5 | 2 |  |  |  |
| httpx-verify-false-client-cert-001 | regression | 78012 | 1 | 6 | 6 |  |  |  |
| prettier-duplicate-dangling-comments-001 | regression | 182434 | 1 | 6 | 0 | success_clean:1 | resource_inefficient:1 |  |
| react-tabs-selected-focus-overlay-001 | regression | 40027 | 3 | 0 | 30 |  |  |  |
| remotion-audio-context-autoplay-muted-001 | regression | 108248 | 2 | 29 | 16 | bad_local_fix:2 | test_gap:2 |  |
| todomvc-toggle-all-checkbox-001 | regression | 100744 | 4 | 8 | 10 |  |  |  |
| vite-deno-workspace-root-001 | regression | 126710 | 6 | 54 | 0 |  |  |  |

### Trial Evidence

| Task | Type | Trial | Grader Outcome | Validity | Primary Review Label | Secondary Review Labels | Exclusion | Files | +Lines | -Lines | Input Tokens | Cached Input Tokens | Output Tokens | Reasoning Tokens | Cost USD | Duration ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| datawrapper-mcp-docker-requirements-001 | regression | 20260514-120001-datawrapper-mcp-docker-requirements-001-claude-59b21ded | passed | valid |  |  |  | 1 | 5 | 2 | 106 | unknown | 4750 | unknown | 0.10134620000000003 | 47477 |
| 2048-advanced-snake-params-001 | capability | 20260514-120114-2048-advanced-snake-params-001-claude-b6c4cb95 | passed | valid |  |  |  | 2 | 6 | 6 | 178 | unknown | 8314 | unknown | 0.15655615 | 80101 |
| click-default-map-nargs-001 | regression | 20260514-120240-click-default-map-nargs-001-claude-54de5b71 | passed | valid |  |  |  | 1 | 12 | 0 | 466 | unknown | 18330 | unknown | 0.44235895000000014 | 225363 |
| click-help-option-refactor-001 | capability | 20260514-120634-click-help-option-refactor-001-claude-c4f69f39 | passed | valid |  |  |  | 3 | 33 | 28 | 426 | unknown | 16148 | unknown | 0.38072034999999993 | 158318 |
| click-help-shadowed-option-001 | regression | 20260514-120920-click-help-shadowed-option-001-claude-5566808c | passed | valid | success_clean | resource_inefficient |  | 2 | 47 | 8 | 538 | unknown | 19450 | unknown | 0.5106382 | 218288 |
| click-should-strip-ansi-tests-001 | regression | 20260514-121306-click-should-strip-ansi-tests-001-claude-a63f2827 | failed | valid | bad_local_fix | test_gap |  | 1 | 57 | 1 | 146 | unknown | 11565 | unknown | 0.17350744999999998 | 83658 |
| httpx-verify-false-client-cert-001 | regression | 20260514-121440-httpx-verify-false-client-cert-001-claude-044965c1 | passed | valid |  |  |  | 1 | 6 | 6 | 210 | unknown | 10010 | unknown | 0.19463375 | 96569 |
| prettier-duplicate-dangling-comments-001 | regression | 20260514-121636-prettier-duplicate-dangling-comments-001-claude-5694847a | passed | valid |  |  |  | 1 | 6 | 0 | 354 | unknown | 18394 | unknown | 0.35947635 | 200681 |
| react-tabs-selected-focus-overlay-001 | regression | 20260514-122010-react-tabs-selected-focus-overlay-001-claude-1c53c8cd | passed | valid |  |  |  | 3 | 0 | 30 | 90 | unknown | 4903 | unknown | 0.08207270000000001 | 40402 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260514-122258-remotion-audio-context-autoplay-muted-001-claude-1fc7a864 | passed | valid |  |  |  | 2 | 27 | 16 | 202 | unknown | 16739 | unknown | 0.2694114 | 131408 |
| todomvc-toggle-all-checkbox-001 | regression | 20260514-122653-todomvc-toggle-all-checkbox-001-claude-dfe6d568 | passed | valid |  |  |  | 4 | 8 | 10 | 322 | unknown | 12267 | unknown | 0.2780227500000001 | 119163 |
| vite-deno-workspace-root-001 | regression | 20260514-122902-vite-deno-workspace-root-001-claude-867ec512 | passed | valid |  |  |  | 6 | 53 | 0 | 362 | unknown | 11861 | unknown | 0.28635745 | 119480 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260514-124128-datawrapper-mcp-docker-requirements-001-claude-d63c61e6 | passed | valid |  |  |  | 1 | 5 | 2 | 50 | unknown | 2955 | unknown | 0.0615093 | 26786 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260514-124156-datawrapper-mcp-docker-requirements-001-claude-6c254bc6 | passed | valid |  |  |  | 1 | 7 | 4 | 130 | unknown | 5415 | unknown | 0.12030055 | 51306 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260514-124248-datawrapper-mcp-docker-requirements-001-claude-cf30258a | passed | valid |  |  |  | 1 | 3 | 9 | 106 | unknown | 4671 | unknown | 0.10231655000000002 | 45710 |
| datawrapper-mcp-docker-requirements-001 | regression | 20260514-124335-datawrapper-mcp-docker-requirements-001-claude-30c8d5a6 | passed | valid |  |  |  | 1 | 5 | 2 | 58 | unknown | 3495 | unknown | 0.06890755 | 28065 |
| 2048-advanced-snake-params-001 | capability | 20260514-124404-2048-advanced-snake-params-001-claude-40725393 | passed | valid |  |  |  | 1 | 1 | 1 | 138 | unknown | 5643 | unknown | 0.11430589999999999 | 52980 |
| 2048-advanced-snake-params-001 | capability | 20260514-124459-2048-advanced-snake-params-001-claude-57395876 | passed | valid |  |  |  | 2 | 4 | 4 | 162 | unknown | 6509 | unknown | 0.14249245 | 59504 |
| 2048-advanced-snake-params-001 | capability | 20260514-124559-2048-advanced-snake-params-001-claude-b5a42479 | passed | valid |  |  |  | 2 | 6 | 6 | 154 | unknown | 8929 | unknown | 0.15359245 | 82627 |
| 2048-advanced-snake-params-001 | capability | 20260514-124723-2048-advanced-snake-params-001-claude-a943b569 | passed | valid |  |  |  | 2 | 8 | 7 | 154 | unknown | 6520 | unknown | 0.13182095 | 64279 |
| click-default-map-nargs-001 | regression | 20260514-124829-click-default-map-nargs-001-claude-cb47fc08 | passed | valid |  |  |  | 1 | 8 | 0 | 458 | unknown | 21442 | unknown | 0.4945633499999998 | 216856 |
| click-default-map-nargs-001 | regression | 20260514-125210-click-default-map-nargs-001-claude-3c4c70bf | passed | valid |  |  |  | 1 | 16 | 1 | 418 | unknown | 15536 | unknown | 0.4176668500000001 | 170565 |
| click-default-map-nargs-001 | regression | 20260514-125505-click-default-map-nargs-001-claude-82f02f7a | passed | valid | success_clean | resource_inefficient |  | 2 | 88 | 0 | 578 | unknown | 24502 | unknown | 0.6334486499999998 | 248138 |
| click-default-map-nargs-001 | regression | 20260514-125917-click-default-map-nargs-001-claude-54d20c01 | passed | valid | success_clean | resource_inefficient |  | 1 | 14 | 0 | 514 | unknown | 21286 | unknown | 0.5142575500000001 | 215793 |
| click-help-option-refactor-001 | capability | 20260514-130257-click-help-option-refactor-001-claude-7c2ab8da | passed | valid |  |  |  | 3 | 38 | 28 | 498 | unknown | 19372 | unknown | 0.46197235000000003 | 208036 |
| click-help-option-refactor-001 | capability | 20260514-130629-click-help-option-refactor-001-claude-37b8f08e | passed | valid |  |  |  | 3 | 39 | 28 | 434 | unknown | 18908 | unknown | 0.45613955000000006 | 194851 |
| click-help-option-refactor-001 | capability | 20260514-130949-click-help-option-refactor-001-claude-010fb91c | passed | valid | success_clean | resource_inefficient |  | 3 | 30 | 28 | 730 | unknown | 25603 | unknown | 0.72578465 | 277223 |
| click-help-option-refactor-001 | capability | 20260514-131430-click-help-option-refactor-001-claude-e43ad9ae | passed | valid |  |  |  | 3 | 40 | 27 | 410 | unknown | 17914 | unknown | 0.46333999999999986 | 178540 |
| click-help-shadowed-option-001 | regression | 20260514-131733-click-help-shadowed-option-001-claude-11d301a7 | passed | valid |  |  |  | 1 | 7 | 8 | 402 | unknown | 14623 | unknown | 0.36135210000000006 | 142958 |
| click-help-shadowed-option-001 | regression | 20260514-164549-click-help-shadowed-option-001-claude-59d6c787 | passed | valid |  |  |  | 1 | 7 | 5 | 354 | unknown | 23072 | unknown | 0.3825584000000001 | 204881 |
| click-help-shadowed-option-001 | regression | 20260514-164918-click-help-shadowed-option-001-claude-16dc4eb5 | passed | valid |  |  |  | 1 | 7 | 8 | 426 | unknown | 20832 | unknown | 0.4399256 | 213403 |
| click-help-shadowed-option-001 | regression | 20260514-165256-click-help-shadowed-option-001-claude-ec2a28e8 | passed | valid |  |  |  | 1 | 7 | 8 | 450 | unknown | 20615 | unknown | 0.43125474999999985 | 211586 |
| click-should-strip-ansi-tests-001 | regression | 20260514-165650-click-should-strip-ansi-tests-001-claude-f219f43e | failed | valid | bad_local_fix | test_gap |  | 1 | 54 | 1 | 191 | unknown | 13819 | unknown | 0.17125854999999998 | 107555 |
| click-should-strip-ansi-tests-001 | regression | 20260514-165842-click-should-strip-ansi-tests-001-claude-bc75b331 | failed | valid | bad_local_fix | test_gap |  | 1 | 98 | 1 | 330 | unknown | 27080 | unknown | 0.41547824999999994 | 219407 |
| click-should-strip-ansi-tests-001 | regression | 20260514-170226-click-should-strip-ansi-tests-001-claude-a7e872e0 | failed | valid | bad_local_fix | test_gap |  | 1 | 46 | 1 | 186 | unknown | 12037 | unknown | 0.1964943 | 99401 |
| click-should-strip-ansi-tests-001 | regression | 20260514-170410-click-should-strip-ansi-tests-001-claude-7c99c96e | failed | valid | bad_local_fix | test_gap |  | 1 | 47 | 1 | 154 | unknown | 11385 | unknown | 0.17512090000000002 | 85478 |
| httpx-verify-false-client-cert-001 | regression | 20260514-170552-httpx-verify-false-client-cert-001-claude-5ab308a9 | passed | valid |  |  |  | 1 | 3 | 4 | 138 | unknown | 11016 | unknown | 0.15885154999999998 | 97412 |
| httpx-verify-false-client-cert-001 | regression | 20260514-170736-httpx-verify-false-client-cert-001-claude-a45263ee | passed | valid |  |  |  | 1 | 6 | 6 | 122 | unknown | 6535 | unknown | 0.11078425000000003 | 55676 |
| httpx-verify-false-client-cert-001 | regression | 20260514-170838-httpx-verify-false-client-cert-001-claude-1eaf63b2 | passed | valid |  |  |  | 1 | 6 | 6 | 154 | unknown | 8360 | unknown | 0.14576455 | 78012 |
| httpx-verify-false-client-cert-001 | regression | 20260514-171002-httpx-verify-false-client-cert-001-claude-c9186e35 | passed | valid |  |  |  | 1 | 3 | 4 | 154 | unknown | 6948 | unknown | 0.13278145000000002 | 66652 |
| prettier-duplicate-dangling-comments-001 | regression | 20260514-171124-prettier-duplicate-dangling-comments-001-claude-f6688fa1 | passed | valid |  |  |  | 1 | 6 | 0 | 418 | unknown | 15424 | unknown | 0.40206959999999997 | 172053 |
| prettier-duplicate-dangling-comments-001 | regression | 20260514-171429-prettier-duplicate-dangling-comments-001-claude-c647e55d | passed | valid |  |  |  | 1 | 17 | 0 | 482 | unknown | 18438 | unknown | 0.4476253 | 213677 |
| prettier-duplicate-dangling-comments-001 | regression | 20260514-171816-prettier-duplicate-dangling-comments-001-claude-3e085a4f | passed | valid | success_clean | resource_inefficient |  | 1 | 6 | 0 | 546 | unknown | 17295 | unknown | 0.52182645 | 182434 |
| prettier-duplicate-dangling-comments-001 | regression | 20260514-172132-prettier-duplicate-dangling-comments-001-claude-7b5a687b | passed | valid |  |  |  | 1 | 6 | 0 | 370 | unknown | 13366 | unknown | 0.33683434999999995 | 147762 |
| react-tabs-selected-focus-overlay-001 | regression | 20260514-172426-react-tabs-selected-focus-overlay-001-claude-71cd57f2 | passed | valid |  |  |  | 3 | 0 | 30 | 90 | unknown | 4236 | unknown | 0.07777814999999999 | 36010 |
| react-tabs-selected-focus-overlay-001 | regression | 20260514-172504-react-tabs-selected-focus-overlay-001-claude-60859801 | passed | valid |  |  |  | 3 | 0 | 30 | 114 | unknown | 4635 | unknown | 0.0877965 | 40027 |
| react-tabs-selected-focus-overlay-001 | regression | 20260514-172546-react-tabs-selected-focus-overlay-001-claude-f36c70e3 | passed | valid |  |  |  | 3 | 0 | 30 | 66 | unknown | 4244 | unknown | 0.06626270000000001 | 32724 |
| react-tabs-selected-focus-overlay-001 | regression | 20260514-172621-react-tabs-selected-focus-overlay-001-claude-dd69dfaa | passed | valid |  |  |  | 3 | 0 | 30 | 114 | unknown | 4012 | unknown | 0.0847384 | 40899 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260514-172711-remotion-audio-context-autoplay-muted-001-claude-5432a34d | passed | valid |  |  |  | 2 | 27 | 15 | 170 | unknown | 11259 | unknown | 0.2029784 | 92332 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260514-173021-remotion-audio-context-autoplay-muted-001-claude-cd1474a8 | failed | valid | bad_local_fix | test_gap |  | 2 | 35 | 16 | 226 | unknown | 11261 | unknown | 0.24297530000000006 | 108248 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260514-173352-remotion-audio-context-autoplay-muted-001-claude-ec26a24f | failed | valid | bad_local_fix | test_gap |  | 2 | 32 | 16 | 154 | unknown | 10874 | unknown | 0.1912029 | 94624 |
| remotion-audio-context-autoplay-muted-001 | regression | 20260514-173707-remotion-audio-context-autoplay-muted-001-claude-3949dbd3 | passed | valid |  |  |  | 2 | 29 | 15 | 114 | unknown | 13934 | unknown | 0.1875086 | 112824 |
| todomvc-toggle-all-checkbox-001 | regression | 20260514-174054-todomvc-toggle-all-checkbox-001-claude-5ff48184 | passed | valid |  |  |  | 4 | 8 | 10 | 162 | unknown | 8505 | unknown | 0.15805155 | 69774 |
| todomvc-toggle-all-checkbox-001 | regression | 20260514-174210-todomvc-toggle-all-checkbox-001-claude-43b411f4 | passed | valid |  |  |  | 4 | 8 | 12 | 282 | unknown | 11361 | unknown | 0.24541404999999997 | 122628 |
| todomvc-toggle-all-checkbox-001 | regression | 20260514-174417-todomvc-toggle-all-checkbox-001-claude-5139d4e0 | passed | valid |  |  |  | 4 | 8 | 10 | 218 | unknown | 9195 | unknown | 0.19207625000000006 | 100744 |
| todomvc-toggle-all-checkbox-001 | regression | 20260514-174604-todomvc-toggle-all-checkbox-001-claude-4089090f | passed | valid |  |  |  | 4 | 8 | 10 | 282 | unknown | 10214 | unknown | 0.24125755 | 100206 |
| vite-deno-workspace-root-001 | regression | 20260514-174757-vite-deno-workspace-root-001-claude-6422c447 | passed | valid |  |  |  | 6 | 83 | 0 | 322 | unknown | 14068 | unknown | 0.28343470000000004 | 119926 |
| vite-deno-workspace-root-001 | regression | 20260514-175002-vite-deno-workspace-root-001-claude-0b858ecc | passed | valid |  |  |  | 6 | 51 | 0 | 418 | unknown | 17810 | unknown | 0.36986255 | 162873 |
| vite-deno-workspace-root-001 | regression | 20260514-175250-vite-deno-workspace-root-001-claude-b45610fc | passed | valid |  |  |  | 6 | 74 | 0 | 314 | unknown | 13570 | unknown | 0.28079655 | 126710 |
| vite-deno-workspace-root-001 | regression | 20260514-214849-vite-deno-workspace-root-001-claude-a5227e4c | passed | valid |  |  |  | 6 | 54 | 0 | 346 | unknown | 17055 | unknown | 0.31272685 | 158228 |
