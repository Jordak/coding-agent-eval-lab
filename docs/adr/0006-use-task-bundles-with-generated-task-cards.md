# ADR 0006: Use Task Bundles With Generated Task Cards

Status: Accepted

Date: 2026-05-07

## Context

Tasks are no longer just standalone YAML files. Publishable tasks need metadata,
human-readable summaries, reference artifacts, and sometimes screenshots or
notes. Keeping those files in separate directories would make task review and
agent navigation harder.

## Decision

Store each task as a task bundle:

```text
tasks/<suite>/<task-id>/
  task.yaml
  task-card.md
  reference.patch
```

`task.yaml` remains the source of truth. `task-card.md` is generated Markdown
for humans and AI assistants, committed next to the task YAML. Suite directories
may include generated `README.md` indexes that link to task cards.

## Consequences

- Task metadata, reference artifacts, and readable summaries stay together.
- `docs/` remains focused on project-level explanation rather than per-task
  material.
- The task loader should accept both task YAML paths and task bundle directories.
- Generated task cards and suite indexes must be refreshed from task metadata,
  not edited by hand.
