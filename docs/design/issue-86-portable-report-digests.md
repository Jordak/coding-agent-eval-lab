# Issue 86 Portable Report Digests

Source: GitHub issue #86, "Make generated report digests portable after worktree cleanup".

Design readiness: ready to implement

Readiness verdict: Ready to Implement

## Chosen Policy

Checked-in selected evidence manifests that need to outlive local `runs/` cleanup should carry a durable `OutcomeEvidence` snapshot. The snapshot is the runs-to-reports interface object: normalized trial result and human-review facts plus artifact-presence receipts. It strips local artifact paths and does not bundle task workspaces, transcripts, or diffs.

Checked-in Markdown capability evidence digests and report-support packets remain portable evidence summaries. They must not include per-trial artifact links to local `runs/` outputs, absolute workstation paths, or temporary worktree paths. Markdown keeps the trial identifiers and aggregate evidence needed for later hand-authored capability reports, but omits the `Report`, `Transcript`, `Diff`, and `Result` artifact-link columns.

Static HTML reports may be checked in when they are regenerated from durable snapshot-backed evidence and pass the no-local-artifact-link portability scan. HTML generated from raw local `runs/` remains useful as a local artifact-navigation preview while raw trial artifacts are present, but it should not be committed if it links to disposable report, transcript, diff, or result files.

## Alternatives Considered

- Bundle raw selected artifacts: rejected for this slice because transcripts, diffs, and task workspaces expand size and privacy surface beyond what digest regeneration needs.
- Link to a stable external artifact store: deferred because this repository does not currently define one.
- Hand-edit only the low-effort baseline digest: rejected because the generator should stop creating non-portable checked-in Markdown.
- Remove links only: rejected after the issue comment clarified that selected evidence manifests must remain resolvable even when raw worktree-local `runs/` directories are deleted.

## Implementation Boundary

This slice updates the Markdown digest generator, source-path display, durable snapshot support, evidence-set loading, documentation, focused tests, existing checked-in generated digests, and older checked-in report-support files that exposed local artifact indexes. It adds a snapshot for the low-effort Codex starter-suite baseline so its evidence-set manifest can regenerate Markdown and HTML digests without the original temporary `runs/` tree. It does not bundle raw trial artifacts, introduce an external artifact store, or draft the issue #50 final comparison interpretation.

Agent workflow policy lives in `.agents/skills/report-evidence`: report/evidence branches that create or update selected evidence manifests must generate the digest and snapshot together, prove regeneration with a missing runs directory, and run the portability check before push.

## Validation Plan

- Focused unit tests for Markdown digest portability, evidence-set source display, snapshot round-tripping, and CLI regeneration from a snapshot with a missing runs directory.
- HTML generation tests cover both local previews and snapshot-backed durable reports.
- `agentlab report check-evidence-portability --evidence-set ...` for every evidence-set manifest created or updated by a report/evidence branch.
- Deterministic `rg` checks over checked-in reports and the committed snapshot for disposable `runs/`, `/Users/...`, `/private/...`, and worktree artifact links.

## Report Size Impact

Removing four artifact-link columns from Markdown digests intentionally shrinks checked-in digest files. The low-effort Codex baseline adds one durable snapshot file for selected evidence. Its size is intentional because it preserves normalized report-generation evidence while avoiding raw transcripts, diffs, task workspaces, and local artifact paths. Snapshot-backed HTML can be checked in as a durable rendered view; local HTML previews with raw artifact links should remain uncommitted.

The low-effort snapshot was recovered from the checked-in digest because the original temporary worktree runs were already unavailable. It is sufficient to regenerate the checked-in digest metrics and trial rows, but it is not a substitute for raw run artifacts when a later reviewer needs full transcripts or diffs.
