# Claude Code Harness Pilot

Date: 2026-05-11

This is a harness pilot note, not a Claude Code capability report. The goal was
to prove that Agent Eval Lab can run Claude Code through the same isolated trial
flow as manual and Codex harnesses, then capture comparable artifacts.

## Preflight

`python3 -m agentlab doctor --agent claude --claude-timeout-seconds 10` passed
with:

- Claude Code executable found on `PATH`.
- CLI version `2.1.139 (Claude Code)`.
- Auth status `loggedIn=true authMethod=claude.ai apiProvider=firstParty`.
- `claude -p` print-mode command shape accepted.

## Adapter Finding

The first Datawrapper smoke exposed an eval-harness issue before measuring
agent capability:

- Trial: `runs/20260511-191147-datawrapper-mcp-docker-requirements-001-claude-9db2e59a`
- Outcome: excluded as `eval_harness_error`.
- Cause: Claude Code 2.1.139 requires `--verbose` when `--print` uses
  `--output-format stream-json`.
- Fix: the adapter now adds `--verbose` for `stream-json`.

## Smoke Evidence

The next Datawrapper smoke was fair and passed:

- Trial: `runs/20260511-191233-datawrapper-mcp-docker-requirements-001-claude-bfa31cf7`
- Task: `datawrapper-mcp-docker-requirements-001`
- Model: `claude-sonnet-4-6`, derived from Claude events.
- Outcome: passed.
- Patch shape: one file, `deployment/requirements.txt`.
- Resource evidence: 24.846s, 1,271 output tokens, 0.08616835 USD reported by
  Claude Code.

The Click smoke was fair and failed:

- Trial: `runs/20260511-192822-click-should-strip-ansi-tests-001-claude-821a4273`
- Task: `click-should-strip-ansi-tests-001`
- Model: `claude-sonnet-4-6`, derived from Claude events.
- Outcome: failed, reviewed as `test_gap` with secondary
  `resource_inefficient`.
- Evidence: setup and pytest passed, but the structural AST grader rejected the
  patch because it called the imported `should_strip_ansi(...)` helper instead
  of `click._compat.should_strip_ansi(...)`; Claude then hit `max_turns` while
  debugging.

## Result

The Claude Code adapter is ready for more smoke testing, but not yet for a full
12-task repeated baseline. The next sensible step is a tiny two-task comparison
or one more fair smoke with adjusted tool permissions/turn budget, followed by
a decision about whether the adapter is stable enough for repeated trials.
