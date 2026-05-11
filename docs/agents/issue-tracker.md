# Issue Tracker: GitHub

Issues and PRDs for this repo live as GitHub issues in `Jordak/coding-agent-eval-lab`. Use the `gh` CLI for issue operations.

## Conventions

- Create an issue: `gh issue create --title "..." --body "..."`
- Read an issue: `gh issue view <number> --comments`
- List issues: `gh issue list --state open --json number,title,body,labels,comments`
- Comment on an issue: `gh issue comment <number> --body "..."`
- Apply or remove labels: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- Close an issue: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v`; `gh` does this automatically when run inside the clone.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Task Candidates And Curation

Task candidates, task-curation backlog items, and proposed additions to an
evaluation suite live in GitHub Issues. Do not create or maintain a local task
candidate backlog document.

Use labels to represent the candidate's workflow state:

- `needs-triage`: a candidate needs curator judgment, more exact commits,
  feasibility checks, or a grading strategy before an AFK agent can implement it.
- `ready-for-human`: the next step requires human curation, design judgment, or
  visual/product review.
- `ready-for-agent`: the issue is fully specified for an AFK agent, including
  repository, pinned starting commit, expected behavior, reference artifact
  expectations, deterministic grader strategy, acceptance criteria, and any
  stop conditions for suspicious or resource-heavy setup.

When adding a task from an issue, keep the implementation branch scoped to the
task bundle, generated task card, reference artifacts, task-specific tests when
needed, and issue comments that record smoke-trial evidence. Do not add
suite-level task-card indexes.
