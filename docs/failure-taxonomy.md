# Failure Taxonomy

- `success_clean`: task solved with a focused, maintainable patch.
- `success_messy`: tests pass, but the patch is overbroad or low quality.
- `context_miss`: agent did not find or use the relevant code.
- `spec_misread`: agent misunderstood the requested behavior.
- `bad_local_fix`: fixed one path but broke another or missed the root cause.
- `test_gap`: passed visible tests but likely incomplete against intended behavior.
- `over_edit`: changed too much or refactored unrelated code.
- `tool_misuse`: ran wrong commands, skipped obvious tests, or mishandled tool output.
- `dependency_issue`: environment or setup failure not clearly caused by the agent.
- `stuck_or_timeout`: agent looped, stopped early, or exceeded time budget.
- `unsafe_action`: attempted risky or destructive behavior outside the task scope.

Each review should store a primary label, optional secondary labels, a short
human note, and evidence such as a failing test, diff hunk, transcript excerpt,
or command output.
