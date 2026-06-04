# Design Overview

Accepted architectural decisions live in [adr/](adr/). This file summarizes the
current system shape; new durable decisions should be added as ADRs instead of
only being recorded here.

## Core Entities

The lab separates task design, agent harness, underlying model, and evaluation.
This keeps reports honest when, for example, Cursor uses Claude as a model but
still runs inside Cursor's agent harness.

The project follows the vocabulary in
[anthropic-eval-principles.md](anthropic-eval-principles.md): tasks, trials,
graders/assertions, transcripts/traces, outcomes, evaluation harness, agent
harness/scaffold, and evaluation suites.

## MVP Architecture

- `agentlab.tasks` loads task YAML into domain objects.
- `agentlab.tasks.integrity` is the shared task-bundle integrity boundary
  for source YAML validation, generated task-card drift checks, reference
  artifact readiness, and smoke-test readiness.
- `agentlab.execution.workspace` prepares base-only git workspaces for each trial.
- `agentlab.agents` defines agent harness adapters.
- `agentlab.execution.runner` coordinates workspace setup, agent execution, code-based
  graders, outcome capture, and artifact writing.
- `agentlab.reports.trial_markdown` renders Markdown trial reports and later static HTML.

## Package Layout

The `agentlab` package is organized by domain module:

- `agentlab.agents` contains agent harness adapters plus shared adapter infrastructure.
- `agentlab.tasks` contains task bundle loading, task-card generation, task environment helpers, reference verification, and integrity checks.
- `agentlab.execution` contains command execution, workspace preparation, trial phases, scoring, and run orchestration.
- `agentlab.evidence` contains result artifacts, human review outcomes, validity metadata, evidence sets, summaries, backfills, and archival helpers.
- `agentlab.reports` contains human-facing report renderers.
- `agentlab.runtime` contains runtime metadata normalization such as model identity, token usage, harness configuration, and patch metrics.
- `agentlab.cli` contains command-line parsing and command handlers.

## Task Bundles

Tasks live as bundles under `tasks/<suite>/<task-id>/`. Each bundle contains a
source `task.yaml`, a generated `task-card.md`, and any reference artifacts such
as `reference.patch`.

The task loader accepts either a direct task YAML path or a task bundle
directory. Suite directories can be passed to validation commands to discover
all bundled `task.yaml` files below them.

`agentlab.tasks.integrity` owns the source-to-validation contract for a
single task bundle. CLI task commands, generated task-card checks, reference
artifact workflows, smoke-test preflight, and the repo-local pre-commit hook
should call this shared interface instead of each rebuilding its own
bundle-integrity path.

Publishable tasks should distinguish a prose `reference_solution` from a
verified `reference_artifact`. The prose field orients readers. The artifact
points to a reviewed reference patch or commit that proves the task is solvable
and that graders can accept a known-good outcome. Reference artifacts may be
AI-authored, but they must be human-reviewed and validated before the task is
treated as publishable.

Use `agentlab task verify-reference <task-bundle>` to materialize the pinned
base tree in a base-only git workspace, apply the reference artifact, run
setup/baseline/target graders, and enforce success criteria such as max files
changed. Patch artifacts are applied directly; commit artifacts are converted to
patches in a private prep clone before being applied to the base-only workspace.
Reference verification writes `reference-report.md`, `reference-result.json`,
and `reference.diff` next to the task bundle by default; use
`--no-write-artifacts` for a transient check. These artifacts use the same
report/result shape as agent trials, but are marked with
`trial_kind: reference_verification` and excluded from normal trial summaries.

Use `agentlab task smoke-test` before repeated trials. The smoke-test workflow
verifies the reference artifact, then runs exactly one agent trial with one job
and prints the report, result, and diff paths a maintainer should inspect before
scaling.

Generated task cards are source-adjacent review artifacts, not the source of
truth. The repo-local pre-commit hook runs task-bundle integrity validation with
task-card drift checks enabled so drift is caught before commits. Task
candidates and suite-curation backlog live in GitHub Issues; do not maintain
local task-candidate backlog documents or generated suite task-card indexes.

## Scope Oracle Metadata

Tasks may carry optional scope-oracle metadata that is used by graders and
reports but is not injected into trial prompts automatically. The generic fields
are `consent_style`, `success.allowed_paths`, and
`success.forbidden_paths`.

`consent_style` records the consent cue style a task author intended. Valid
values are `silent`, `implicit_deny`, `explicit_deny`, `implicit_allow`, and
`explicit_allow`.

Boundary path patterns are repo-root-relative globs matched against normalized
final changed paths that use `/` separators. Patterns must not be absolute, must
not contain `..`, must not be empty, and must not start with `!`; v1 has no
negation. A pattern is matched against the whole changed path. `*` and `?` match
within one path segment, and `**` matches zero or more path segments. A trailing
slash means a recursive directory match: `src/` matches changed paths below
`src/`, including nested descendants.

Missing `success.allowed_paths` means there is no allow-list constraint. An
explicit empty `success.allowed_paths: []` is invalid task metadata. Missing or
empty `success.forbidden_paths` means there is no forbidden-path constraint.
When a changed path matches both lists, `success.forbidden_paths` wins.

Boundary checks run against the final changed paths recorded by the harness,
including staged and unstaged tracked changes, untracked files, additions,
modifications, deletes, and renames. Boundary violations fail the deterministic
grader outcome with clear notes, but they do not automatically create human
review labels.

## Interaction Model

V1 tasks are non-interactive by default: the agent harness receives a fixed
prompt and should proceed without a clarification loop. Future task bundles may
opt into bounded follow-up questions with explicit interaction metadata, but
interactive tasks must be summarized separately from non-interactive tasks. See
[ADR 0008](adr/0008-reserve-interactive-task-contracts.md).

## Task Environments

Task setup should provision the dependencies needed by the deterministic graders
and by the obvious self-checks an agent is likely to run. For example, a Python
task that reasonably invites `pytest` should either make the relevant pytest
entrypoint available or document that the intended validation scope is the
listed grader commands.

Tasks can declare `environment_path` entries to prepend workspace-relative
directories to `PATH`, and an `environment` mapping for environment variables.
The runner applies that task-local environment to setup, baseline, agent, and
target grader commands. This lets a task create `.agentlab/venv` in setup and
then expose `python`, `pip`, and `pytest` consistently to both the agent and the
graders.

The current lightweight evaluation harness still leaves interpreter/package-manager
selection inside task setup commands. Candidate curation should record setup
cost, language runtime requirements, and whether full upstream tests are
available inside the trial workspace.

## Agent Adapters

Agent-facing trial and reference-verification workspaces expose only one
synthetic base commit for the pinned task tree. Full repository history may
exist temporarily in private prep state to fetch and materialize the base tree,
but it is not present in the workspace handed to the agent harness. Result JSON and
reports record both the original task repository/commit and the synthetic
workspace base ref. See [ADR 0010](adr/0010-use-base-only-agent-workspaces.md).

The manual adapter is the positive/negative-control baseline. It can pause for a
human edit or run with `--no-pause` to intentionally make no changes.

The Codex CLI adapter uses `codex exec` non-interactively against the isolated
workspace. It captures JSONL events, the final agent message, the resulting
patch, and the same code-based graders as every other adapter.

Command-based adapters share the **agent process executor** in
`agentlab.agents.process_execution`. The executor owns executable resolution,
process launch, timeout and progress polling, stdout/stderr capture, working
directory and environment wiring, and stdout event-artifact persistence.
Adapters own command construction, agent-specific event parsing, resource usage
normalization, model identity extraction, final-message rendering, and harness
configuration metadata.

## Graders And Outcomes

The current evaluation harness uses deterministic code-based graders: setup
commands, baseline assertions, target assertions, and post-change assertions.
These are fast, cheap, reproducible, and appropriate for early coding-agent
evals.

Reports emphasize the outcome: the final patch, changed files, command results,
and grader pass/fail status. Tool-call and transcript graders should be added
only when they evaluate behavior that outcome graders cannot capture.

The project keeps the deterministic **grader outcome** separate from the
**human review outcome**. A trial can pass code-based graders and still receive a
human review label such as `success_messy`, `over_edit`, or `test_gap`.
A valid trial with passing graders is a **verified result**. A valid
grader-passing trial with a primary `success_clean` review label is an
**accepted result**; `success_messy` remains verified but not accepted.

Human review also records **trial validity**. A valid trial is fair to count in
capability summaries. An excluded trial keeps its raw artifacts and review
evidence, but its pass/fail result is removed from fair pass-rate, pass@k,
pass^k, and median outcome metrics. Exclusion reasons use a small vocabulary:
`dependency_issue`, `eval_harness_error`, `setup_error`, `operator_error`,
`invalid_task`, and `unknown`.

Human review should be backed by structured **outcome evidence** where possible:
edit size metrics such as files changed and lines added/deleted, resource usage
metrics such as duration, tokens, and cost, plus targeted diff, transcript, and
grader-output excerpts.

## Aggregation

Single trials are useful for debugging, but agent evals need repeated trials
because agent behavior is non-deterministic. `agentlab run --trials N` executes
multiple independent trials for the same task and agent harness; `--jobs N`
controls how many of those trials run concurrently. `agentlab trials summarize`
groups stored results and reports total trials, fair trials, excluded trials,
fair-trial pass rate, pass@k, pass^k, accepted-result counts,
token-normalized outcome metrics, median duration, median changed files, median
line additions/deletions, primary review-label counts, secondary review-label
counts, and exclusion-reason counts. Token-normalized metrics include failed
valid trials in the token numerator, divide by verified or accepted results, and
keep input-plus-output, cached-input, and reasoning-output token buckets
separate. Summary groups include the agent harness, runtime model, and reasoning
effort so materially different runtime configurations are not collapsed into one
evidence row.

`agentlab report capability-evidence-digest` renders those summaries plus
per-trial evidence into Markdown. For local inspection it can scan a whole runs
directory; for report preparation it should read an explicit evidence-set
manifest so the selected trials are deliberate and reproducible. This generated
capability evidence digest is intended as the data backbone for hand-authored,
evidence-scoped capability reports; it does not replace human interpretation.
Checked-in Markdown digests intentionally omit per-trial artifact links because
local `runs/` artifacts are ignored and can disappear after temporary worktree
cleanup. HTML reports generated from durable snapshot-backed evidence can be
checked in next to Markdown when they pass the same no-local-artifact-link
portability scan. HTML generated from raw local `runs/` is a local navigation
preview and should not be committed if it contains links to disposable
artifacts. Digest review columns keep primary labels separate from secondary
caveat labels, and digest rows show both model and effort level.

Trial storage remains the append-only file-artifact workflow described above.
Trial listing, summaries, human review outcome overlays, and capability evidence
digests discover current evidence from `runs/*/result.json` and adjacent
artifacts such as `review.json`, transcripts, and diffs. A checked-in selected
evidence manifest may also point at a durable `OutcomeEvidence` snapshot. That
snapshot is the report-generation interface object: normalized result and review
facts plus artifact-presence receipts, with local artifact paths stripped and raw
workspace, transcript, and diff contents omitted. When present, the snapshot
keeps Markdown and HTML digest regeneration independent of disposable worktree
`runs/` directories. Report/evidence agents use `.agents/skills/report-evidence`
before pushing branches that create or update selected evidence manifests, and
`agentlab report check-evidence-portability` provides the deterministic guard
that those manifests carry loadable snapshots. There is no active
database-backed trial storage interface or storage migration in this slice.

Reviewed excluded trials can be archived out of the active runs directory with
`agentlab trials archive-excluded`. The archive is dry-run-first, moves artifacts
under `runs/_archive/excluded/<reason>/`, and writes an `archive-manifest.jsonl`
so invalid-trial evidence remains inspectable without cluttering default
summaries or capability evidence digests.

See [runtime-accountability.md](runtime-accountability.md) for open work around
model identity, account context, token usage, and cost tracking.

## Dependency Policy

The first implementation avoided mandatory third-party runtime dependencies, but
task bundles are now rich YAML authoring artifacts. The lab requires PyYAML for
`task.yaml` loading so pre-commit, local CLI use, and installed-package behavior
share one parser path instead of a fragile YAML-subset fallback.
