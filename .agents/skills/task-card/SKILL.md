---
name: task-card
description: Generate Markdown task cards from Agent Eval Lab task bundles. Use when adding, moving, reviewing, or refreshing task YAML files under tasks/.
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
next to it. Do not create generated suite `README.md` indexes; GitHub Issues are
the source of truth for task candidates and task-curation backlog.

When a task needs local tools such as `pytest`, record workspace-relative PATH
entries and variables in `task.yaml`:

```yaml
environment_path:
  - .agentlab/venv/bin
environment:
  PYTHONDONTWRITEBYTECODE: "1"
  PYTEST_ADDOPTS: "-p no:cacheprovider"
  VIRTUAL_ENV: "{workspace}/.agentlab/venv"
```

Python task bundles must include `PYTHONDONTWRITEBYTECODE: "1"` and
`PYTEST_ADDOPTS: "-p no:cacheprovider"` unless the task explicitly evaluates
Python or pytest cache behavior. This keeps ordinary `__pycache__/` and
`.pytest_cache/` byproducts out of changed-file scoring.

When a task has a verified reference patch or commit, record it in `task.yaml`:

```yaml
reference_artifact:
  type: patch
  path: reference.patch
```

Optional scope-oracle metadata can declare consent posture and path boundaries
without injecting those details into trial prompts:

```yaml
consent_style: explicit_allow
success:
  allowed_paths:
    - src/
  forbidden_paths:
    - secrets/
```

Valid `consent_style` values are `silent`, `implicit_deny`, `explicit_deny`,
`implicit_allow`, and `explicit_allow`. Boundary globs are repo-root-relative;
v1 has no negation, trailing slash means recursive directory match, and
forbidden paths win over allowed paths. See `docs/design.md` for the global
path-glob contract.

## Workflow

1. Edit or create `task.yaml` in a task bundle.
2. Add or update any verified reference artifact, such as `reference.patch`.
3. Run the generator for the task bundle or all tasks.
4. Review `task-card.md` for readability.
5. Run `python3 -m agentlab task validate --check-task-cards tasks`.
6. For tasks with reference artifacts, run `python3 -m agentlab task verify-reference <task-bundle>`.
7. Ensure the repo-local pre-commit hook passes before committing.

Do not hand-edit generated task cards. Update the YAML, reference artifact, or
generator instead.
