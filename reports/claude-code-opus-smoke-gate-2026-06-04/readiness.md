# Claude Code Opus Smoke Gate Readiness

Date: 2026-06-04

Scope: GitHub issue #62, the Claude Code Opus smoke-gate prerequisite for the later #50 starter-suite comparison.

Readiness verdict: Ready for the approved 12-task smoke gate, using outside-sandbox Claude Code execution. The sandbox cannot see the macOS Keychain-backed Claude.ai login, but the same executable outside the sandbox reports a first-party Claude.ai Pro subscription login with no API-key or cloud-provider routing variables present.

## Decision

Run the Opus smoke suite only through outside-sandbox Claude Code execution, where the local auth state is visible. The resolved Claude Code executable is available and recent. Inside the sandbox, the non-secret auth check reports that this process is not logged in:

```text
loggedIn=false authMethod=none apiProvider=firstParty
```

Outside the sandbox, the same auth check reports:

```text
loggedIn=true authMethod=claude.ai apiProvider=firstParty subscriptionType=pro
```

The task explicitly forbids continuing if the run could fall onto API billing or if the no-extra-cost path cannot be trusted. Current official Claude Code docs say `ANTHROPIC_API_KEY` is always used in non-interactive `-p` mode when present, subscription OAuth from `/login` is the default for Claude Pro, Max, Team, and Enterprise users, and `/status` should be checked when falling back from an API key to a subscription. They also say the `/usage` Session dollar figure is intended for API users and is not the relevant billing figure for Pro and Max subscription users, who should see plan usage information instead. This local environment has no API-key, token, cloud-provider, custom-base-URL, or Opus override routing variables present by name.

## Sources Checked

- GitHub issue #62, read with `gh issue view 62 --repo Jordak/coding-agent-eval-lab --comments --json number,title,state,labels,body,comments,url`.
- Claude Code CLI reference: https://code.claude.com/docs/en/cli-usage
- Claude Code model configuration: https://code.claude.com/docs/en/model-config
- Claude Code authentication: https://code.claude.com/docs/en/iam
- Claude Code costs: https://code.claude.com/docs/en/costs
- Local project context: `CONTEXT.md`, ADR 0002, ADR 0004, ADR 0005, ADR 0007, and `docs/design/issue-86-portable-report-digests.md`.
- Project report workflow: `.agents/skills/report-evidence/SKILL.md`.

## Local Safety Gate

Non-secret routing checks:

```text
ANTHROPIC_API_KEY: absent
ANTHROPIC_AUTH_TOKEN: absent
CLAUDE_CODE_OAUTH_TOKEN: absent
CLAUDE_CODE_USE_BEDROCK: absent
CLAUDE_CODE_USE_VERTEX: absent
CLAUDE_CODE_USE_FOUNDRY: absent
CLAUDE_CODE_USE_AWS_BEDROCK: absent
ANTHROPIC_BASE_URL: absent
ANTHROPIC_BEDROCK_BASE_URL: absent
ANTHROPIC_AWS_BASE_URL: absent
ANTHROPIC_VERTEX_BASE_URL: absent
ANTHROPIC_MODEL: absent
ANTHROPIC_DEFAULT_OPUS_MODEL: absent
CLAUDE_CODE_API_KEY_HELPER_TTL_MS: absent
CLAUDE_CONFIG_DIR: absent
```

Local command facts:

| Check | Result |
| --- | --- |
| `git status --short --branch` | `## codex/issue-62-claude-opus-smoke...origin/main` |
| `claude --version` | `2.1.162 (Claude Code)` |
| `claude auth status` inside sandbox | exit 1, `loggedIn=false authMethod=none apiProvider=firstParty` |
| `claude auth status` outside sandbox | exit 0, `loggedIn=true authMethod=claude.ai apiProvider=firstParty subscriptionType=pro` |
| `python3 -B -m agentlab doctor --agent claude --claude-model opus --claude-timeout-seconds 20` inside sandbox | failed on Claude Code auth, before inference |
| `python3 -B -m agentlab doctor --agent claude --claude-model opus --claude-timeout-seconds 20` outside sandbox | passed |

One preflight caveat: `python3 -m agentlab doctor ...` without `-B` initially produced a false passing auth line from an external stale Python bytecode cache. Use `python3 -B -m agentlab ...` for this branch until that local cache is cleared.

## Intended Opus Configuration After Auth Is Fixed

The first safe model probe requested the Opus alias and trusted only the event-derived runtime model identity:

| Setting | Intended value |
| --- | --- |
| Agent harness | `claude` |
| CLI command | `claude` |
| Model request | `opus` |
| Runtime model identity | `claude-opus-4-8` from stream-json `system`, `assistant`, and `modelUsage` events |
| Permission mode | `acceptEdits` |
| Output format | `stream-json` with verbose stream |
| Session persistence | disabled through `--no-session-persistence` |
| Max turns | unset |
| Timeout | `1800` seconds |
| Effort | unset in Agent Eval Lab; current Claude Code docs say Opus effort defaults depend on the resolved Opus version |
| Allowed tools | none configured |
| Disallowed tools | none configured |

Current Claude Code docs say `--model` accepts aliases such as `opus` or a full model name, and that `--model` applies only to the launched session. They also say eligible Max, Team Premium, Enterprise pay-as-you-go, and Anthropic API defaults currently resolve to Opus 4.8, while Pro, Team Standard, and subscription Enterprise seats default to Sonnet 4.6. In this account, an explicit `--model opus` probe resolved to `claude-opus-4-8`.

## Model Availability Probe

Command:

```bash
claude -p 'Reply with exactly: ready' \
  --model opus \
  --output-format stream-json \
  --permission-mode acceptEdits \
  --verbose \
  --no-session-persistence \
  --max-turns 1 \
  --max-budget-usd 0.02 \
  --tools ''
```

Result:

- Exit code: `1`
- Result text: `ready`
- Error subtype: `error_max_budget_usd`
- Reason: local probe cap was intentionally tiny and the estimated total was `0.02145` USD
- Event model: `claude-opus-4-8`
- `apiKeySource`: `none`
- Tools: `[]`
- Usage reported by Claude Code: `inputTokens=25`, `cacheCreationInputTokens=3396`, `outputTokens=4`
- `modelUsage` listed `claude-opus-4-8` with a 1,000,000-token context window and 64,000 max output tokens

This probe verifies model/account availability and subscription routing. It is not a task-capability trial.

## Smoke Command Shape After Manual Approval

After Jordan confirms `/status` and `/usage` show subscription-quota routing rather than API billing, run exactly one sequential smoke trial per starter-suite task. Use `--trials 1 --jobs 1` semantics by calling `task smoke-test`, and stop after the 12 trials:

```bash
python3 -B -m agentlab task smoke-test \
  --task tasks/starter/<task-id> \
  --agent claude \
  --runs-dir runs/claude-code-opus-smoke-gate-2026-06-04 \
  --claude-model opus \
  --claude-permission-mode acceptEdits \
  --claude-output-format stream-json \
  --claude-timeout-seconds 1800
```

Do not top up to five trials per task without Jordan's explicit follow-up approval. If a trial is fair but fails, retain it and mark it valid. If a failure is caused by task, grader, setup, dependency, operator, or eval-harness unfairness, stop and surface the blocker rather than rerunning it away.

## Evidence Status

The model availability probe above is not included in a selected evidence manifest because it is not a task trial.

The 12-task smoke evidence is recorded in:

- `reports/claude-code-opus-smoke-gate-2026-06-04/report.md`
- `reports/claude-code-opus-smoke-gate-2026-06-04/digest.md`
- `reports/claude-code-opus-smoke-gate-2026-06-04/digest.html`
- `evidence-sets/claude-code-opus-smoke-gate-2026-06-04.json`
- `evidence-sets/claude-code-opus-smoke-gate-2026-06-04.outcome-evidence.json`

The post-#86 report-evidence workflow generated a durable `OutcomeEvidence` snapshot, proved digest/HTML regeneration with a missing runs directory, and passed the evidence-portability check.

## Manual Verification Needed

Jordan verified Claude Code auth locally before Opus smoke collection:

1. Claude Code auth reports first-party `claude.ai` credentials with `subscriptionType=pro`.
2. The outside-sandbox environment has no API-key, token, cloud-provider, custom-base-URL, or Opus override routing variables present by name.
3. The local preflight with bytecode disabled passes outside the sandbox: `python3 -B -m agentlab doctor --agent claude --claude-model opus --claude-timeout-seconds 20`.
4. The tiny Opus model probe records event-derived runtime model identity before the 12-task smoke run.
