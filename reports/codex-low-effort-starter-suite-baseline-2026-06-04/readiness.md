# Codex Low-Effort Starter Suite Baseline Readiness

Date: 2026-06-04

Scope: GitHub issue #63. This note records the portable low-effort Codex
configuration, the required readiness/preflight proof, and the follow-on full
baseline collection approved after that proof.

Design readiness: ready to implement

Readiness verdict: Ready to Implement. The preflight/smoke slice proved the
configuration before the approved full baseline collection.

## Decision

Use Codex CLI with an explicit model request and an explicit per-invocation
reasoning-effort override:

| Setting | Value |
| --- | --- |
| Agent harness | `codex` |
| CLI command | `codex` |
| Model request | `gpt-5.5` |
| Requested reasoning effort | `low` |
| Sandbox | `workspace-write` |
| Approval policy | `never` |
| Timeout | `1800` seconds |
| Trials/jobs for smoke | exactly one trial and one job |

Portable request mechanism:

```text
codex exec --config model_reasoning_effort="low" --model gpt-5.5 ...
```

Agent Eval Lab exposes this through:

```text
--codex-model gpt-5.5 --codex-reasoning-effort low
```

`requested_reasoning_effort` records the requested configuration. Runtime
`reasoning_effort` remains a recovered/proven metadata field, so a silently
ignored override can still be detected by comparing the requested and recovered
values.

## Sources Checked

- GitHub issue #63, read with `gh issue view 63 --comments --json ...`.
- OpenAI Codex CLI command-line options:
  https://developers.openai.com/codex/cli/reference
- OpenAI Codex config basics:
  https://developers.openai.com/codex/config-basic
- OpenAI Codex configuration reference:
  https://developers.openai.com/codex/config-reference
- OpenAI GPT-5.3-Codex model page for supported effort values:
  https://developers.openai.com/api/docs/models/gpt-5.3-codex
- Local Codex CLI help: `codex --help` and `codex exec --help`.
- Local project context: `CONTEXT.md`, ADR 0002, ADR 0004, ADR 0005, and ADR
  0007.

## Local Preflight Commands

Run the cheap adapter/config preflight:

```bash
python3 -m agentlab doctor \
  --agent codex \
  --codex-model gpt-5.5 \
  --codex-reasoning-effort low \
  --codex-sandbox workspace-write \
  --codex-approval never \
  --codex-timeout-seconds 20
```

Then run one task with exactly one agent trial and one job before any scaling:

```bash
python3 -m agentlab task smoke-test \
  --task tasks/starter/click-should-strip-ansi-tests-001 \
  --agent codex \
  --runs-dir runs/issue-63-low-effort-preflight \
  --codex-model gpt-5.5 \
  --codex-reasoning-effort low \
  --codex-sandbox workspace-write \
  --codex-approval never \
  --codex-timeout-seconds 1800
```

The smoke run is only valid as readiness evidence if its stored or recovered
metadata records both:

- `model_name = gpt-5.5`
- `agent_harness_config.reasoning_effort = low`

## Local Preflight Results

Command:

```bash
python3 -m agentlab doctor \
  --agent codex \
  --codex-model gpt-5.5 \
  --codex-reasoning-effort low \
  --codex-sandbox workspace-write \
  --codex-approval never \
  --codex-timeout-seconds 20
```

Result:

- Codex executable: found at `/opt/homebrew/bin/codex`
- Codex version: `codex-cli 0.136.0-alpha.2`
- Codex exec command shape: accepted
- Overall preflight: passed

## Smoke Trial Evidence

Command:

```bash
python3 -m agentlab task smoke-test \
  --task tasks/starter/click-should-strip-ansi-tests-001 \
  --agent codex \
  --runs-dir runs/issue-63-low-effort-preflight \
  --codex-model gpt-5.5 \
  --codex-reasoning-effort low \
  --codex-sandbox workspace-write \
  --codex-approval never \
  --codex-timeout-seconds 1800
```

Result:

- Trial:
  `20260603-191424-click-should-strip-ansi-tests-001-codex-964f53c1`
- Status: `passed`
- Model: `gpt-5.5`
- Requested reasoning effort: `low`
- Runtime reasoning effort: `low`
- Model source: `local_codex_state`
- Codex thread: `019e9069-1ab7-7821-91a7-45b822c753f7`
- Codex state row:
  `gpt-5.5 | low | openai | exec | 0.136.0-alpha.2`
- Run surface fields present:
  `execution_surface=local_cli`, `runtime_version=codex-cli 0.136.0-alpha.2`,
  `model_identity_source=local_codex_state`, `sandbox_mode=workspace-write`,
  `approval_policy=never`, `network_policy=unknown`,
  `timeout_seconds=1800`, `stop_reason=success`
- Resource usage:
  `input_tokens=147890`, `cached_input_tokens=101632`,
  `output_tokens=2206`, `reasoning_output_tokens=0`, `cost_usd=unknown`,
  `duration_ms=49692`

## Full Baseline Collection

After the smoke trial proved runtime low-effort capture, the full starter-suite
collection was approved and run sequentially with `--jobs 1`.

Command shape:

```bash
python3 -m agentlab run \
  --agent codex \
  --task tasks/starter/<task-id> \
  --runs-dir runs/codex-low-effort-starter-suite-baseline-2026-06-04 \
  --trials 5 \
  --jobs 1 \
  --codex-model gpt-5.5 \
  --codex-reasoning-effort low \
  --codex-sandbox workspace-write \
  --codex-approval never \
  --codex-timeout-seconds 1800
```

Exception: `click-should-strip-ansi-tests-001` used the smoke trial above as
trial 1/5, then ran four top-up trials with the same command shape and
`--trials 4 --jobs 1`.

Result summary:

- Selected evidence: `60` trials across `12` starter-suite tasks.
- Main baseline directory: `runs/codex-low-effort-starter-suite-baseline-2026-06-04`
- Smoke trial directory: `runs/issue-63-low-effort-preflight`
- Outcome: `60/60` passed; every task has five fair trials.
- Metadata proof:
  `model_name=gpt-5.5`, `requested_reasoning_effort=low`,
  runtime `reasoning_effort=low`, and
  `run_surface.model_identity_source=local_codex_state` on all 60 selected
  trials.
- Run-surface proof: all 60 selected trials include raw run-surface fields for
  execution surface, runtime version, model source, sandbox, approval policy,
  timeout, and stop reason. The digest renders the Agent Harness Operability
  table from those raw fields plus resource and harness metadata.
- Evidence set:
  `evidence-sets/codex-low-effort-starter-suite-baseline-2026-06-04.json`
- Digest artifact:
  `reports/codex-low-effort-starter-suite-baseline-2026-06-04/digest.md`
- Local HTML preview:
  `reports/codex-low-effort-starter-suite-baseline-2026-06-04/digest.html`

Resource caveats:

- Total recorded tokens across the selected evidence set:
  `18,660,131`.
- `cost_usd` was `unknown` for all 60 selected trials, so dollar cost was not
  measured by the harness.
- Highest token trial:
  `20260603-193311-click-default-map-nargs-001-codex-f4e64fcc`,
  `834,999` total tokens, `179,367` ms.
- Longest trial:
  `20260603-194503-click-help-option-refactor-001-codex-efbdc416`,
  `214,715` ms, `787,482` total tokens.
- Highest aggregate task token bands in the generated digest are
  `prettier-duplicate-dangling-comments-001`,
  `click-help-option-refactor-001`, and
  `click-default-map-nargs-001`.

## Stop Conditions

For future low-effort collection or re-runs, stop before scaling if:

- the smoke result cannot prove runtime `reasoning_effort = low`;
- the recovered runtime effort differs from `requested_reasoning_effort = low`;
- the requested model differs from recovered `model_name = gpt-5.5`;
- preflight or focused tests fail;
- the smoke path suggests unexpected cost, quota pressure, repeated
  environment invalidity, or a broader config design change.

## Next Approval Checkpoint

The full local collection and digest generation are complete. Ask before
human-review labeling, GitHub issue comments, commits, pushes, PR creation, or
any additional baseline expansion/re-run that would create new cost or quota
pressure.

Cross-agent comparison and hand-authored interpretation should be handled under
parent issue #50 rather than expanded inside issue #63. Report-link portability
is tracked separately in issue #86.
