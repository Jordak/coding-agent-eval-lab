# Agent Eval Lab Instructions

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `Jordak/coding-agent-eval-lab`. See `docs/agents/issue-tracker.md`.

Current planning anchor: GitHub Issue #10, "PRD: Codex deep baseline and
evidence-scoped capability reports"
(`https://github.com/Jordak/coding-agent-eval-lab/issues/10`). After context
compaction, read that PRD before choosing the next implementation slice.

### Triage labels

This repo uses the default five-label triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses a single-context domain docs layout. See `docs/agents/domain.md`.

### Project-local skills

Use `.agents/skills/task-card` when creating, moving, or refreshing task bundles
under `tasks/`.

This checkout uses `.githooks/pre-commit` to check generated task cards and task
bundle validation before commits.

Task candidates and task-curation backlog items live in GitHub Issues, not in a
local backlog document. Use `needs-triage` for candidates that need curator
judgment, `ready-for-human` for human curation/design work, and
`ready-for-agent` only when a task issue is fully specified for an AFK agent.

## Engineering operating rules

- Do not hard-code user- or machine-specific file locations when a portable
  discovery or configuration mechanism exists. Prefer repo-relative paths,
  `PATH`, explicit CLI flags, or documented setup.
- If a failure is caused by the local environment, diagnose and fix the
  environment before adding application-level workarounds.
- Put reusable behavior in shared layers. Keep child adapters focused on
  adapter-specific behavior, and move general terminal, reporting, or error
  presentation into common code.
- When testing a new task, grader, environment setup, or agent-harness behavior,
  start with one trial and one job (`--trials 1 --jobs 1`). Scale to parallel
  trial batches only after the single-trial path is known to be fair.
- When adding tasks in parallel, keep each branch scoped to the task bundle,
  generated `task-card.md`, reference artifacts, and any task-specific tests.
  Do not create or update suite-level task-card indexes or local task-candidate
  backlog documents.
