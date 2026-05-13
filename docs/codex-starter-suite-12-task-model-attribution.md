# Codex Starter Suite 12-Task Model Attribution

Date: 2026-05-13

## Conclusion

All 60 selected Codex CLI trials in
`evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json`
map to local Codex thread metadata with:

- Model: `gpt-5.5`
- Reasoning effort: `xhigh`
- Provider: `openai`
- Thread source: `exec`

This is recovered runtime metadata from the local Codex state database, not a
field exposed in the saved `codex-events.jsonl` streams.

## Evidence Strength

The selected run artifacts themselves still have no event-derived model
identity:

- `result.json` has `model_name: null` for the selected runs.
- `codex-events.jsonl` exposes `thread_id` and usage, but no `model` field.
- Historical `report.md` files are static and continue to show `Model:
  unknown`.

The stronger recovered evidence is the local Codex thread database at
`~/.codex/state_5.sqlite`. For each selected run, the `thread.started`
event's `thread_id` matches exactly one row in `threads`, and every matched row
records `model = 'gpt-5.5'` and `reasoning_effort = 'xhigh'`.

## Summary Counts

| Model | Reasoning effort | Provider | Source | CLI version | Runs |
| --- | --- | --- | --- | --- | --- |
| `gpt-5.5` | `xhigh` | `openai` | `exec` | `0.129.0-alpha.15` | 9 |
| `gpt-5.5` | `xhigh` | `openai` | `exec` | `0.130.0-alpha.5` | 51 |

Total selected runs checked: `60`

Missing Codex thread rows: `0`

## Config And Docs Cross-Check

The local user config currently contains:

```toml
model = "gpt-5.5"
model_reasoning_effort = "xhigh"
```

This is consistent with the recovered thread metadata. Current OpenAI Codex
docs say Codex configuration precedence is CLI flags and `--config` overrides,
then profiles, project config, user config, system config, and built-in
defaults. The Codex CLI docs also state that `--model` overrides the configured
model for a run, and the Codex models docs describe `model = "gpt-5.5"` as the
local default model configuration pattern.

Relevant docs:

- https://developers.openai.com/codex/config-basic
- https://developers.openai.com/codex/cli/reference
- https://developers.openai.com/codex/models

## Reproduction Notes

The investigation used each selected run's `thread.started` event:

```bash
jq -r '.trials[]' evidence-sets/codex-starter-suite-12-task-baseline-2026-05-11.json
```

For each selected run:

```bash
jq -r 'select(.type=="thread.started") | .thread_id' runs/<run-id>/codex-events.jsonl
```

Then the recovered model metadata came from:

```sql
select
  id,
  model,
  reasoning_effort,
  model_provider,
  source,
  cli_version,
  cwd
from threads
where id = '<thread-id>';
```

Because this depends on Jordan's local Codex state database, it should be cited
as recovered local runtime metadata. It is stronger than inferring from the
current config alone, but it is not the same as model identity emitted in the
portable run artifacts.
