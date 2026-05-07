# Agent Eval Lab Instructions

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `Jordak/coding-agent-eval-lab`. See `docs/agents/issue-tracker.md`.

### Triage labels

This repo uses the default five-label triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses a single-context domain docs layout. See `docs/agents/domain.md`.

### Project-local skills

Use `.agents/skills/task-card` when creating, moving, or refreshing task bundles
under `tasks/`.

This checkout uses `.githooks/pre-commit` to check generated task cards and task
bundle validation before commits.
