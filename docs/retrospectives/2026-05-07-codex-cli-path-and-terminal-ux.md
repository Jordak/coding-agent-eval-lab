# Codex CLI Path and Terminal UX Retrospective

Date: 2026-05-07

## Context

The first Codex trial for `click-help-shadowed-option-001` failed before the
agent started because the evaluation harness could not find `codex`. The error
was written to the trial transcript but was not visible enough in the terminal.
A later run also showed that long-running Codex trials needed better liveness
feedback.

## What Happened

- The initial workaround hard-coded the macOS Codex app bundle path in the
  adapter. That made the local run work but was not portable.
- The real issue was environmental: `codex` existed, but no normal `PATH`
  directory exposed it.
- The environment was fixed by putting a `codex` symlink in `/opt/homebrew/bin`,
  a directory already present on the user's clean shell `PATH`.
- Terminal error display was first considered near the Codex adapter, but the
  reusable behavior belonged in the shared run summary path because any adapter
  can fail before producing a useful patch.

## Operating Lessons

- Prefer root-cause fixes over local workarounds. If the problem is the
  environment, make the environment correct.
- Do not hard-code machine-specific paths into reusable project code.
- Put generalizable behavior in shared modules rather than adapter-specific
  child classes.
- A transcript is not enough for launch failures. Serious run errors should be
  visible in the terminal at the time they happen.

## Outcome

- The repo expects `codex` to resolve from `PATH`; `--codex-command` remains an
  explicit escape hatch for unusual installs.
- Agent errors now print through the shared CLI summary path.
- Codex subprocess runs show terminal liveness while waiting for the agent.

## Follow-Ups

- Keep future runtime setup issues classified separately from model or
  agent-harness capability failures.
- Consider adding structured setup-failure labels or environment diagnostics if
  similar issues repeat across agent harnesses.
