# ADR 0009: Use GitHub Issues For Task Candidates

Status: Accepted

Date: 2026-05-11

## Context

The lab is expanding task coverage through parallel task-curation work. The
previous workflow kept task candidates in a local Markdown backlog and generated
suite `README.md` files that linked to each task card in a suite. That created
shared files that many parallel task branches wanted to edit at once.

Those shared files were also not the best source of truth. Task candidates need
workflow state, discussion, triage labels, and sometimes human review before an
AFK agent can implement them. GitHub Issues already provide those properties.

## Decision

Use GitHub Issues as the source of truth for task candidates and task-curation
backlog items.

Task candidate workflow state is represented with issue labels:

- `needs-triage` for candidates that need curator judgment, exact commits,
  feasibility checks, or a grading strategy.
- `ready-for-human` for human-led curation, design, or visual/product review.
- `ready-for-agent` only when the issue is fully specified for an AFK agent.

Keep each task bundle self-contained on disk with `task.yaml`, generated
`task-card.md`, and any reference artifacts. Do not maintain a local
task-candidate backlog document. Do not generate suite-level task-card indexes
such as `tasks/<suite>/README.md`.

## Consequences

- Parallel task-add branches no longer need to touch shared suite index or local
  backlog files.
- Task candidates can be searched, discussed, labeled, and promoted through the
  issue tracker.
- The task-card generator only owns per-bundle task cards.
- Existing and future agents should look to GitHub Issues, not local Markdown
  backlog files, when selecting task candidates or task-curation work.
