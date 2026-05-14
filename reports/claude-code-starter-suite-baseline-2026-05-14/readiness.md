# Claude Code Starter Suite Baseline Readiness

Date: 2026-05-14

Scope: GitHub issue #51, the readiness/configuration slice for the Claude Code
baseline in #49. This note records the Claude Code configuration to use before
Phase 1 collects one fair trial for each Solo Dev Starter Suite task.

## Decision

Use Claude Code with the pinned Claude Haiku 4.5 model ID:

```text
claude-haiku-4-5-20251001
```

Why this model:

- Anthropic's current model comparison lists Claude Haiku 4.5 as the cheapest
  and lowest-latency current first-party Claude model in the
  Opus/Sonnet/Haiku lineup: `$1 / input MTok`, `$5 / output MTok`, and
  `Fastest` comparative latency.
- Anthropic's pricing page lists Claude Haiku 3.5 at a lower token price, but
  marks it as retired except on Bedrock and Vertex AI. That makes it a poor
  fit for a Claude Code baseline.
- Anthropic's Haiku page says Haiku 4.5 is the fastest, most cost-efficient
  model, matches Sonnet 4 performance on coding, computer-use, and agent tasks,
  and is available in Claude Code.
- The local Claude Code CLI accepted the pinned model ID in print mode and
  emitted assistant/result events with `claude-haiku-4-5-20251001`.

This is intentionally a cheap proof-of-concept baseline. It should not be read
as the strongest possible Claude Code configuration.

## Sources Checked

- Anthropic model overview:
  https://platform.claude.com/docs/en/about-claude/models/overview
- Anthropic Claude Haiku 4.5 page:
  https://www.anthropic.com/claude/haiku
- Anthropic pricing:
  https://platform.claude.com/docs/en/about-claude/pricing
- Claude Code model configuration:
  https://code.claude.com/docs/en/model-config
- Local Claude Code CLI help:
  `claude --help`

## Local Preflight

Command:

```bash
python3 -m agentlab doctor --agent claude \
  --claude-model claude-haiku-4-5-20251001 \
  --claude-timeout-seconds 20
```

Result:

- Claude Code executable: found at `/Users/jordanharry/.local/bin/claude`
- Claude Code version: `2.1.139 (Claude Code)`
- Claude Code auth: `loggedIn=true authMethod=claude.ai apiProvider=firstParty`
- Claude Code print command shape: accepted
- Overall preflight: passed

The same doctor command also passed with the convenience alias
`claude-haiku-4-5`, but the baseline should request the pinned ID above for
reproducibility.

## Model Availability Probe

Command:

```bash
claude -p 'Reply with exactly: ready' \
  --model claude-haiku-4-5-20251001 \
  --output-format stream-json \
  --permission-mode acceptEdits \
  --verbose \
  --no-session-persistence \
  --max-turns 1 \
  --max-budget-usd 0.02 \
  --tools ''
```

Result:

- Exit code: `0`
- Result text: `ready`
- Event model: `claude-haiku-4-5-20251001`
- Total reported cost: `0.00831675` USD
- Usage reported by Claude Code: `input_tokens=10`,
  `cache_creation_input_tokens=6167`, `cache_read_input_tokens=0`,
  `output_tokens=42`
- `modelUsage` listed `claude-haiku-4-5-20251001` with a 200k context window and
  32k max output tokens.

This probe was deliberately tiny and disabled tools. It verifies model/account
availability, not coding capability. Coding capability comes from the official
model documentation above.

## Baseline Harness Config

Use these settings for Phase 1:

| Setting | Value |
| --- | --- |
| Agent harness | `claude` |
| CLI command | `claude` |
| Model request | `claude-haiku-4-5-20251001` |
| Permission mode | `acceptEdits` |
| Output format | `stream-json` |
| Verbose stream | yes, added by the adapter for `stream-json` |
| Max turns | unset |
| Timeout | `1800` seconds |
| Session persistence | disabled, adapter passes `--no-session-persistence` |
| Allowed tools | none configured |
| Disallowed tools | none configured |
| Effort flag | unset |

Max turns should remain unset for the baseline. The 2026-05-11 Claude Code
harness pilot observed a fair trial that reached `max_turns` while debugging,
which made the configured turn cap part of the result. Leaving max turns unset
keeps the Phase 1 baseline closer to the existing Codex one-invocation trial
shape and lets the 1800-second wall-clock timeout be the bounding limit.

## Phase 1 Command Shape

For each task bundle under `tasks/starter/`, run exactly one smoke trial:

```bash
python3 -m agentlab task smoke-test \
  --task tasks/starter/<task-id> \
  --agent claude \
  --claude-model claude-haiku-4-5-20251001 \
  --claude-permission-mode acceptEdits \
  --claude-output-format stream-json \
  --claude-timeout-seconds 1800
```

Do not pass `--claude-max-turns` for Phase 1. The smoke-test command verifies
the reference artifact first, then runs exactly one agent trial with one job.
If a failure is caused by setup, task definition, dependency, operator, or eval
harness problems, preserve the artifacts and mark the trial excluded rather than
counting it as Claude Code capability evidence.
