# Capability Evidence Digest

This digest is generated from stored agent-trial results. It reports evidence only; hand-authored agent capability reports should interpret these observations within the evaluated conditions.

Portable Markdown policy: checked-in digests intentionally omit per-trial artifact links because local `runs/` artifacts are ignored and can disappear after temporary worktree cleanup. HTML reports generated from durable snapshot-backed evidence may be checked in when they pass the same no-local-artifact-link portability check.

- Agent trials: `5`
- Evidence set: `codex-2048-advanced-snake-2026-05-08`
- Evidence set source: `evidence-sets/codex-2048-advanced-snake-2026-05-08.json`
- Outcome evidence snapshot: `evidence-sets/codex-2048-advanced-snake-2026-05-08.outcome-evidence.json`
- Evidence set description: Five fair Codex CLI trials for the starter 2048 advanced-snake params capability task.
- Selected entries: `5`
- Selected result files: `5`
- Selected snapshot records: `5`

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
| Agent harness configuration | agent_harness: `codex`<br>model: `gpt-5.5`<br>reasoning_effort: `xhigh`<br>trials: `5` |
| Budget controls | timeout_seconds: `unknown`<br>turn_or_step_budget: `unknown`<br>observed_input_output_tokens: `5/5`<br>observed_cost_usd: `unknown`<br>configured_token_cost_quota_limits: `unknown` |
| Approval boundaries | sandbox_mode: `unknown`<br>approval_policy: `unknown`<br>tool_policy: `unknown`<br>memory_scope: `unknown`<br>network_policy: `unknown` |
| Verifier state | final_grader_status: `passed`<br>checks_array: `5/5`<br>graders_array: `5/5`<br>intermediate_verifier_movement: `unknown` |
| Halt reasons | normalized_or_derived_stop_reason: `success`<br>first_class_halt_reason_taxonomy: `unknown`<br>error_field: `unknown`<br>budget_operator_interruption_taxonomy: `unknown` |
| Interrupted-run receipt | interrupted_or_error_receipt: `unknown: selected evidence has no interrupted/error receipts`<br>admission_decision_evidence: `5/5` |
| Tool/patch context | changed_files: `5/5`<br>commands_run: `5/5`<br>human_review_overlay: `5/5`<br>transcript: `5/5`<br>diff_patch: `5/5` |
| Receipt basics | run_dir: `5/5`<br>report_md: `5/5`<br>result_json: `5/5`<br>transcript: `5/5`<br>diff_patch: `5/5` |

### Outcome Summary

| Task | Type | Total | Fair | Excluded | Passes | Accepted | Pass Rate | pass@k | pass^k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 5 | 5 | 0 | 5 | 5 | 1.00 | 1.00 | 1.00 |

### Token Summary

| Task | Type | IO Tokens | Cached Tokens | Reason Tokens | IO Tok / Verified | IO Tok / Accepted | Cached Tok / Verified | Reason Tok / Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 1831753 | unknown | 8504 | 366350.60 | 366350.60 | unknown | 1700.80 |

### Review and Patch Summary

| Task | Type | Median ms | Median Files | Median +Lines | Median -Lines | Primary Review Labels | Secondary Review Labels | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 122522 | 2 | 11 | 7 | success_clean:5 |  |  |

### Trial Evidence

| Task | Type | Trial | Grader Outcome | Validity | Primary Review Label | Secondary Review Labels | Exclusion | Files | +Lines | -Lines | Input Tokens | Cached Input Tokens | Output Tokens | Reasoning Tokens | Cost USD | Duration ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2048-advanced-snake-params-001 | capability | 20260508-192558-2048-advanced-snake-params-001-codex-a24c0d88 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 369730 | unknown | 5878 | 1770 | unknown | 123947 |
| 2048-advanced-snake-params-001 | capability | 20260508-192836-2048-advanced-snake-params-001-codex-852468e7 | passed | valid | success_clean |  |  | 2 | 12 | 7 | 405265 | unknown | 5973 | 2179 | unknown | 127637 |
| 2048-advanced-snake-params-001 | capability | 20260508-192836-2048-advanced-snake-params-001-codex-c28086a4 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 263850 | unknown | 4390 | 1366 | unknown | 96705 |
| 2048-advanced-snake-params-001 | capability | 20260508-192836-2048-advanced-snake-params-001-codex-f9940a53 | passed | valid | success_clean |  |  | 2 | 9 | 7 | 390176 | unknown | 5396 | 1602 | unknown | 122522 |
| 2048-advanced-snake-params-001 | capability | 20260508-193138-2048-advanced-snake-params-001-codex-036d2392 | passed | valid | success_clean |  |  | 2 | 11 | 7 | 375823 | unknown | 5272 | 1587 | unknown | 114274 |
