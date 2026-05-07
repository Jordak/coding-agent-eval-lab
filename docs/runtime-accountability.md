# Runtime Accountability

## Current Codex CLI Behavior

The Codex adapter shells out to the locally installed Codex CLI:

```bash
codex --ask-for-approval never exec --json --cd <workspace> --sandbox workspace-write ...
```

This means each Codex trial currently measures **Codex CLI as configured on this
machine**. Authentication, default model selection, account limits, and token
budget are handled by the local Codex app/CLI configuration, not by Agent Lab.

That is fine for early harness development, but it is not yet a complete
model-quality measurement.

## Risk

Trial reports can currently answer:

- Which agent harness adapter ran.
- Whether the patch passed deterministic code-based graders.
- What files changed.
- What assertions ran.
- How long the adapter call took for the trial.

Reports cannot yet reliably answer:

- Which exact model was used if `--codex-model` was omitted.
- Which account or billing context paid for the trial.
- How many input/output tokens were consumed.
- What the trial cost.
- Whether an apparently correct patch was unusually expensive in tokens, cost,
  or runtime.
- Whether a later Codex CLI config change affected comparability.

## TODO

- Record Codex CLI version for every Codex trial.
- Record the explicit model whenever supplied.
- Prefer requiring `--codex-model` for publishable comparisons.
- Parse `codex-events.jsonl` for token usage and cost if the event stream exposes
  it.
- Store resource usage metrics as outcome evidence for human review and
  capability reports.
- Store runtime configuration in `result.json`, including sandbox mode, approval
  policy, command path, model, profile, and CLI version.
- Add a report warning when model, token usage, or cost is unknown.
- Document that early results are local-machine/runtime measurements, not pure
  model-vs-model comparisons.
