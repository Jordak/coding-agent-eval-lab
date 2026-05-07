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

When a task has a verified reference patch or commit, record it in `task.yaml`:

```yaml
reference_artifact:
  type: patch
  path: reference.patch
```

## Workflow

1. Edit or create `task.yaml` in a task bundle.
2. Add or update any verified reference artifact, such as `reference.patch`.
3. Run the generator for the suite or all tasks.
4. Review `task-card.md` for readability.
5. Run `python3 -m agentlab task validate tasks`.
6. For tasks with reference artifacts, run `python3 -m agentlab task verify-reference --write-artifacts <task-bundle>`.
7. Ensure `python3 .agents/skills/task-card/scripts/render_task_cards.py tasks --check` passes before committing.

Do not hand-edit generated task cards or suite indexes. Update the YAML,
reference artifact, or generator instead.
