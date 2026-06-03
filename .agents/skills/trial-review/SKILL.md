---
name: trial-review
description: Interactively review Agent Eval Lab trial results with the user. Use when approving, revising, or proposing human review labels for one run directory, all trials in an explicit evidence set, or pending review.proposed.json drafts.
---

# Trial Review

Run an interactive, trial-by-trial review loop for Agent Eval Lab evidence. The goal is to help the user approve canonical human review outcomes without making proposal artifacts count as applied review.

## Sources

Before reviewing, read the narrowest relevant canonical sources:

- `CONTEXT.md` for project vocabulary.
- `docs/failure-taxonomy.md` for review labels, trial validity, and exclusion reasons.
- `agentlab/evidence/taxonomy.py` and `agentlab/evidence/validity.py` when exact accepted values matter.
- `agentlab/evidence/review_proposals.py` and `agentlab/evidence/review_artifacts.py` when writing artifacts.

Do not duplicate the taxonomy in this skill. Let the code validate labels, validity, and exclusion reasons before artifact writes.

## Review Scope

- In one-run mode, review only that run unless the user asks for broader context.
- In evidence-set mode, review only selected trials from the explicit evidence set.
- Compare resources and patch size only against selected peer trials with the same `task_id`; do not compare against other tasks.
- Skip trials that already have canonical `review.json` by default. Offer re-review only if the user explicitly asks.
- If `review.proposed.json` exists without `review.json`, treat it as draft context, inspect the artifacts yourself, and then keep, revise, or replace the draft.

## Artifact Inspection

For each selected trial, inspect enough evidence to make a defensible proposal:

- `result.json`
- `report.md`
- `diff.patch`
- transcript or trace file when present
- task metadata such as `task.yaml` when discoverable
- same-task selected peers when judging resource or patch-size outliers

Use resource facts when present: duration, input/output/cached/reasoning tokens, cost, command count, files changed, and lines added/deleted. Propose `resource_inefficient` only as an evidence-backed human-review judgment, not from universal hard-coded thresholds.

## Loop

For each trial:

1. Build a compact review card:
   - trial id and task id/title
   - grader outcome
   - patch size
   - resource usage
   - same-task peer context when available
   - proposed primary label
   - proposed secondary labels
   - proposed validity and exclusion reason when excluded
   - confidence
   - evidence bullets
   - proposed note
2. Persist the draft proposal with `python3 -m agentlab review-proposals write`.
3. Ask the user to approve, revise, skip, or ask for more inspection. Do not present a command grammar; accept natural prose.
4. If the user revises in prose, translate the revision into structured review fields, update the draft proposal, and show the exact fields again.
5. Write canonical `review.json` only after explicit user approval of the final fields.
6. After canonical review write succeeds, clear the draft with `python3 -m agentlab review-proposals clear`.
7. Continue to the next selected trial unless the user stops.

## Backend Commands

Persist an agentic draft proposal:

```bash
python3 -m agentlab review-proposals write \
  --run <run-dir> \
  --label <primary-label> \
  --note "<note>" \
  --evidence "<evidence>" \
  --confidence <0-to-1> \
  --reviewer trial-review-skill
```

Add `--secondary <label>` for secondary labels. Add `--exclude --exclusion-reason <reason>` or `--validity excluded --exclusion-reason <reason>` for excluded trials.

Apply a canonical review after explicit approval:

```bash
python3 -m agentlab review \
  --run <run-dir> \
  --label <primary-label> \
  --note "<note>" \
  --evidence "<evidence>"
```

Use the same secondary-label and exclusion options as needed.

Clear a draft after the canonical review write succeeds:

```bash
python3 -m agentlab review-proposals clear --run <run-dir>
```

`python3 -m agentlab review-proposals run` and `evidence-set` generate heuristic drafts. Do not use them as the normal interactive reviewer; they are fallback/smoke paths.

## Safety

- Never auto-apply a proposal.
- Never overwrite an existing `review.json` without explicit user approval for re-review.
- Never count `review.proposed.json` as accepted evidence; summaries and digests read canonical `review.json`.
- If approval, label choice, validity, or exclusion reason is ambiguous, ask one focused question before writing.
