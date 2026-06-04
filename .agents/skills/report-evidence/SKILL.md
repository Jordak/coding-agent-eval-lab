---
name: report-evidence
description: Prepare portable Agent Eval Lab report evidence from selected trial runs. Use when creating or updating evidence-set manifests, generated capability evidence digests, report-support packets, or report PRs that depend on local runs.
---

# Report Evidence

Prepare durable selected evidence for generated capability reports. The goal is
to keep report branches regenerable after temporary worktree `runs/` directories
are deleted.

## Required Workflow

1. Start from an explicit evidence-set manifest under `evidence-sets/`.
2. Ensure selected trials have canonical `review.json` outcomes when human
   review labels are part of the report evidence.
3. Generate the Markdown digest and durable `OutcomeEvidence` snapshot together:

   ```bash
   python3 -m agentlab report capability-evidence-digest \
     --evidence-set evidence-sets/<name>.json \
     --output reports/<report-dir>/digest.md \
     --snapshot-output evidence-sets/<name>.outcome-evidence.json
   ```

4. Add or update the manifest field:

   ```json
   "outcome_evidence_snapshot": "<name>.outcome-evidence.json"
   ```

5. Prove the report regenerates without local runs:

   ```bash
   python3 -m agentlab report capability-evidence-digest \
     --runs-dir /tmp/agentlab-missing-runs \
     --evidence-set evidence-sets/<name>.json \
     --output reports/<report-dir>/digest.md \
     --html-output reports/<report-dir>/digest.html
   ```

6. Run the portability check for every evidence-set manifest created or updated
   by the branch:

   ```bash
   python3 -m agentlab report check-evidence-portability \
     --evidence-set evidence-sets/<name>.json
   ```

7. Run the deterministic report scan before pushing:

   ```bash
   rg -n "\[[^\]]*(Report|Transcript|Diff|Result|Events)[^\]]*\]\(|runs/[^ )>]+/(report\.md|transcript\.md|diff\.patch|result\.json|events\.jsonl)|/Users/|\.codex/worktrees|/private/" reports evidence-sets
   ```

   The scan should print no matches.

## Policy

- Do not rely on raw `runs/` artifacts as the only durable source for a
  checked-in report evidence set.
- Do not commit raw workspaces, transcripts, or diffs as a substitute for a
  snapshot unless the user explicitly chooses that larger evidence bundle.
- Keep Markdown digests free of local artifact links. Check in HTML only when it
  is generated from durable snapshot-backed evidence and passes the same
  no-local-artifact-link scan.
- If a temporary worktree produced the runs, do not push the report branch until
  the snapshot and regeneration proof succeed.
