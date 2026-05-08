# Runtime Accountability

## Current Codex CLI Behavior

The Codex adapter shells out to the locally installed Codex CLI:

```bash
codex --ask-for-approval never exec --json --cd <workspace> --sandbox workspace-write ...
```

By default, the adapter resolves `codex` from `PATH`. If the CLI is installed
somewhere that is not on `PATH`, fix the shell environment or pass
`--codex-command /path/to/codex` for that run. The adapter does not guess
platform-specific install paths.

Codex trials show terminal liveness while the subprocess is running, including a
`waiting for agent response` progress message. Agent adapter errors are reported
through the shared trial summary path and printed to stderr, so launch failures
do not require opening `transcript.md`.

When `codex-events.jsonl` includes `turn.completed` usage metadata, Agent Lab
captures input tokens, cached input tokens, output tokens, and reasoning output
tokens as outcome evidence. Current local Codex traces do not expose dollar cost,
so cost remains `unknown` unless a future event stream includes a reliable cost
field.

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
- How many input/output tokens were reported by Codex CLI, when exposed in the
  event stream.

Reports cannot yet reliably answer:

- Which exact model was used if `--codex-model` was omitted.
- Which account or billing context paid for the trial.
- What the trial cost.
- Whether an apparently correct patch was unusually expensive in cost or runtime.
- Whether a later Codex CLI config change affected comparability.

## TODO

- Record Codex CLI version for every Codex trial.
- Record the explicit model whenever supplied.
- Prefer requiring `--codex-model` for publishable comparisons.
- Parse `codex-events.jsonl` for cost if the event stream exposes it.
- Store runtime configuration in `result.json`, including sandbox mode, approval
  policy, command path, model, profile, and CLI version.
- Add a report warning when model or cost is unknown.
- Document that early results are local-machine/runtime measurements, not pure
  model-vs-model comparisons.
