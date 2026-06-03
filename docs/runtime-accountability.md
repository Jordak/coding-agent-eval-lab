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

Before running Codex trials, use the local preflight check:

```bash
python3 -m agentlab doctor --agent codex
```

The preflight verifies that `codex` resolves from `PATH`, records the installed
CLI version, and asks the installed CLI to parse the same non-interactive
`exec` command shape that trials use. This catches eval-harness/runtime launch
problems before a real task trial is created.

Codex trials show terminal liveness while the subprocess is running, including a
`waiting for agent response` progress message. Agent adapter errors are reported
through the shared trial summary path and printed to stderr, so launch failures
do not require opening `transcript.md`.

When `codex-events.jsonl` includes `turn.completed` usage metadata, Agent Lab
captures input tokens, cached input tokens, output tokens, and reasoning output
tokens as outcome evidence. When Codex events expose the actual model used,
Agent Lab records that model as `model_name` with `model_source: events`; an
explicit `--codex-model` value is retained as `requested_model_name`. When
events expose a Codex `thread_id` but not the runtime model, future Codex runs
also try a failure-tolerant lookup in the local Codex state database and record
recovered model metadata with `model_source: local_codex_state`. Current local
Codex traces do not expose dollar cost, so cost remains `unknown` unless a
future event stream includes a reliable cost field.

Codex trial `result.json` artifacts also store an `agent_harness_config` object
with event-derived model identity when available, requested model and profile
when supplied, sandbox mode, approval policy, timeout, configured command,
resolved command identity when available, and CLI version when Agent Lab can
read it. New trial results also include a sibling `run_surface` object that
normalizes these facts into vendor-neutral fields for comparison. Runtime
accountability fields that the evaluation harness cannot currently provide,
such as account and billing context, remain explicitly unknown in artifact
metadata and report output.

## Run Surface Metadata

Run surface metadata is the neutral comparison layer for facts that affect how a
trial should be interpreted without treating one vendor's option names as the
project vocabulary.

New `result.json` artifacts include `run_surface` with these fields:

- `execution_surface`
- `runtime_version`
- `model_identity_source`
- `sandbox_mode`
- `approval_policy`
- `tool_policy`
- `memory_scope`
- `network_policy`
- `timeout_seconds`
- `turn_or_step_budget`
- `stop_reason`
- `human_intervention_events`

Codex CLI and Claude Code CLI results map existing adapter configuration and
runtime facts into this structure when available. Manual and reference results
use the same structure but leave unsupported facts as `unknown`, except for
explicitly recorded manual intervention events. Historical results that do not
store `run_surface` are normalized at load time from `agent_harness_config`, so
existing artifacts remain readable without migration.

`agent_harness_config` remains the adapter-specific compatibility surface.
`run_surface` is the vendor-neutral surface for trial reports and capability
evidence digests. A missing or unsupported fact should be represented as
`unknown`, not silently omitted.

This means each Codex trial currently measures **Codex CLI as configured on this
machine**. Authentication, default model selection, account limits, and token
budget are handled by the local Codex app/CLI configuration, not by Agent Lab.

That is fine for early eval-harness development, but it is not yet a complete
model-quality measurement.

## Historical Codex Metadata Recovery

Historical Codex runs can be updated explicitly from a selected evidence set and
a supplied local Codex state database:

```bash
python3 -m agentlab recover codex-runtime-metadata \
  --evidence-set evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json \
  --runs-dir /path/to/runs \
  --codex-state-db ~/.codex/state_5.sqlite \
  --dry-run
```

The command defaults to a dry run. Re-run with `--no-dry-run` to write
recovered fields such as `model_name`, `model_source`, `reasoning_effort`,
`model_provider`, and `codex_thread_id` into selected `result.json` artifacts.
If the run artifacts are in another checkout, pass that checkout's `runs`
directory with `--runs-dir`.
This is intentionally separate from normal result loading so reports do not
silently depend on a mutable machine-local database.

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

- Which exact model was used if neither the Codex event stream nor explicit
  recovered local thread metadata identifies runtime model identity.
- Which account or billing context paid for the trial.
- What the trial cost.
- Whether an apparently correct patch was unusually expensive in cost or runtime.
- Whether a later Codex CLI config change affected comparability.

## TODO

- Preserve any additional preflight-derived runtime facts in trial metadata when
  future checks expose them.
- Prefer requiring `--codex-model` for publishable comparisons.
- Parse `codex-events.jsonl` for cost if the event stream exposes it.
- Add a report warning when model or cost is unknown.
- Document that early results are local-machine/runtime measurements, not pure
  model-vs-model comparisons.
