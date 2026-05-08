# Failure Taxonomy

- `success_clean`: task solved with a focused, maintainable outcome.
- `success_messy`: code-based graders pass, but the patch is overbroad or low quality.
- `context_miss`: agent harness did not find or use the relevant code.
- `spec_misread`: agent harness misunderstood the requested behavior.
- `bad_local_fix`: fixed one path but broke another or missed the root cause.
- `test_gap`: passed visible graders but likely incomplete against intended behavior.
- `over_edit`: changed too much or refactored unrelated code.
- `resource_inefficient`: used disproportionate runtime, token budget, cost, or
  command churn relative to the task complexity and outcome quality.
- `tool_misuse`: ran wrong commands, skipped obvious graders, or mishandled tool output.
- `dependency_issue`: environment/setup failure not clearly caused by the agent harness.
- `stuck_or_timeout`: trial looped, stopped early, or exceeded time budget.
- `unsafe_action`: attempted risky or destructive behavior outside the task scope.

Each trial review should store a primary label, optional secondary labels, a
short human note, and evidence such as a failing assertion, diff hunk, transcript
excerpt, command output, edit size metrics, token usage, duration, or cost.

## Trial Validity

Review labels describe what happened. Trial validity controls whether the trial
counts in fair capability metrics.

- `valid`: count the trial in pass rate, pass@k, pass^k, and median outcome
  metrics.
- `excluded`: keep the artifacts but exclude the trial from fair capability
  metrics because the attempt was invalidated before it could measure the agent
  harness.

Excluded trials require one exclusion reason: `dependency_issue`,
`harness_error`, `setup_error`, `operator_error`, `invalid_task`, or `unknown`.
