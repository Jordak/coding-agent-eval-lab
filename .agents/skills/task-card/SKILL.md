---
name: task-card
description: Generate Markdown task cards and suite indexes from Agent Eval Lab task bundles. Use when adding, moving, reviewing, or refreshing task YAML files under tasks/.
---

# Task Card

Generate human-readable and AI-readable Markdown cards from task bundles.

## Quick Start

From the repository root:

```bash
python3 .agents/skills/task-card/scripts/render_task_cards.py tasks
```

Check for drift without writing:

```bash
python3 .agents/skills/task-card/scripts/render_task_cards.py tasks --check
```

Enable the repo-local pre-commit hook:

```bash
git config core.hooksPath .githooks
```

## Task Bundle Convention

Each task lives in its own directory:

```text
tasks/<suite>/<task-id>/
  task.yaml
  task-card.md
  reference.patch
```

`task.yaml` is the source of truth. `task-card.md` is generated and committed
next to it. Suite `README.md` files are generated indexes.

When adding tasks in parallel, keep each task branch scoped to the task bundle
and its generated `task-card.md`. Do not update suite `README.md` indexes in
the per-task branch; those aggregate indexes should be refreshed once after the
parallel task branches are merged.

When a task needs local tools such as `pytest`, record workspace-relative PATH
entries and variables in `task.yaml`:

```yaml
environment_path:
  - .agentlab/venv/bin
environment:
  VIRTUAL_ENV: "{workspace}/.agentlab/venv"
```

When a task has a verified reference patch or commit, record it in `task.yaml`:

```yaml
reference_artifact:
  type: patch
  path: reference.patch
```

## Workflow

1. Edit or create `task.yaml` in a task bundle.
2. Add or update any verified reference artifact, such as `reference.patch`.
3. Run the generator for the task bundle or all tasks. In parallel task-add
   branches, include `--no-index` so the branch does not rewrite aggregate suite
   indexes.
4. Review `task-card.md` for readability.
5. Run `python3 -m agentlab task validate tasks`.
6. For tasks with reference artifacts, run `python3 -m agentlab task verify-reference <task-bundle>`.
7. Ensure `python3 .agents/skills/task-card/scripts/render_task_cards.py tasks --check --no-index` passes before committing.

Do not hand-edit generated task cards or suite indexes. Update the YAML,
reference artifact, or generator instead.
