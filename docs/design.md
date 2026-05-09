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

- `agentlab.tasks` loads and validates task YAML, including suite and eval type.
- `agentlab.workspace` prepares clean checkouts for each trial.
- `agentlab.agents` defines agent harness adapters.
- `agentlab.runner` coordinates workspace setup, agent execution, code-based
  graders, outcome capture, and artifact writing.
- `agentlab.reporting` renders Markdown trial reports and later static HTML.

## Task Bundles

Tasks live as bundles under `tasks/<suite>/<task-id>/`. Each bundle contains a
source `task.yaml`, a generated `task-card.md`, and any reference artifacts such
as `reference.patch`.

The task loader accepts either a direct task YAML path or a task bundle
directory. Suite directories can be passed to validation commands to discover
all bundled `task.yaml` files below them.

Publishable tasks should distinguish a prose `reference_solution` from a
verified `reference_artifact`. The prose field orients readers. The artifact
points to a reviewed reference patch or commit that proves the task is solvable
and that graders can accept a known-good outcome. Reference artifacts may be
AI-authored, but they must be human-reviewed and validated before the task is
treated as publishable.

Use `agentlab task verify-reference <task-bundle>` to clone the pinned repo,
apply or check out the reference artifact, run setup/baseline/target graders,
and enforce success criteria such as max files changed. Reference verification
writes `reference-report.md`, `reference-result.json`, and `reference.diff` next
to the task bundle by default; use `--no-write-artifacts` for a transient check.
These artifacts use the same report/result shape as agent trials, but are marked with
`trial_kind: reference_verification` and excluded from normal trial summaries.

Use `agentlab task smoke-test` before repeated trials. The smoke-test workflow
verifies the reference artifact, then runs exactly one agent trial with one job
and prints the report, result, and diff paths a maintainer should inspect before
scaling.

Generated task cards and suite indexes are source-adjacent review artifacts, not
the source of truth. The repo-local pre-commit hook runs the task-card generator
in `--check` mode so drift is caught before commits.

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

The manual adapter is the positive/negative-control baseline. It can pause for a
human edit or run with `--no-pause` to intentionally make no changes.

The Codex CLI adapter uses `codex exec` non-interactively against the isolated
workspace. It captures JSONL events, the final agent message, the resulting
patch, and the same code-based graders as every other adapter.

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
fair-trial pass rate, pass@k, pass^k, median duration, median changed files,
median line additions/deletions, primary review-label counts, secondary
review-label counts, and exclusion-reason counts.

`agentlab report capability-evidence-digest` renders those summaries plus
per-trial evidence into Markdown. For local inspection it can scan a whole runs
directory; for report preparation it should read an explicit evidence-set
manifest so the selected trials are deliberate and reproducible. This generated
capability evidence digest is intended as the data backbone for hand-authored,
evidence-scoped capability reports; it does not replace human interpretation.
Per-trial rows link to the report, transcript, diff, and result artifacts so
reviewers can inspect surprising pass rates without leaving the digest. Digest
review columns keep primary labels separate from secondary caveat labels.

Trial storage remains the append-only file-artifact workflow described above.
Trial listing, summaries, human review outcome overlays, and capability evidence
digests discover current evidence from `runs/*/result.json` and adjacent
artifacts such as `review.json`, transcripts, and diffs. There is no active
database-backed trial storage interface or storage migration in this slice.

Reviewed excluded trials can be archived out of the active runs directory with
`agentlab trials archive-excluded`. The archive is dry-run-first, moves artifacts
under `runs/_archive/excluded/<reason>/`, and writes an `archive-manifest.jsonl`
so invalid-trial evidence remains inspectable without cluttering default
summaries or capability evidence digests.

See [runtime-accountability.md](runtime-accountability.md) for open work around
model identity, account context, token usage, and cost tracking.

## Early Constraint

The first implementation avoids mandatory third-party dependencies so the lab is
usable immediately in a fresh local folder. If PyYAML is installed, task loading
uses it. Otherwise, a small fallback parser supports the task-schema subset used
by this project.
