# Coding Agent Eval Lab

A reproducible evaluation harness for running coding-agent trials on realistic
software engineering tasks, grading their outcomes, classifying failure modes,
and producing model-quality reports.

This project is intentionally about evaluation infrastructure, not another chat
wrapper. It keeps the key evaluation concerns separate:

- **Task**: a single test case with repository, commit, prompt, environment, and
  success criteria.
- **Trial**: one attempt at a task by an agent harness.
- **Agent harness / scaffold**: Cursor Agent, Claude Code, Codex CLI, Aider,
  manual, etc.
- **Underlying model**: Claude, GPT, Gemini, or another model.
- **Grader**: tests, static checks, human review, LLM judge, and taxonomy.
- **Outcome**: the final environment state, including patch and grader results.

## Current Status

The first scaffold supports:

- Human-editable task bundles with YAML source and generated Markdown cards.
- `agentlab task validate` for shared task-bundle integrity checks.
- Publishable starter task bundles under `tasks/starter/`.
- Draft or illustrative task bundles under `tasks/drafts/`; these are not part
  of the publishable baseline until they have real pinned repositories and
  verified reference artifacts.
- Task-local environment setup for exposing per-task tools such as `pytest`.
- `agentlab run --agent manual --task ...` for one manual trial.
- Git checkout preparation, configured command execution, diff capture, and
  Markdown/JSON trial artifacts.
- Outcome evidence including changed files and line additions/deletions.
- Codex token usage capture when `codex-events.jsonl` exposes usage metadata.
- Codex CLI, Claude Code, and manual agent adapters.
- Multi-trial execution, concurrent trial jobs, and pass@k/pass^k summaries.
- Human review labels, trial-validity metadata, and excluded-trial summaries.
- Standard-library unit tests.

## Quick Start

Install the package and runtime dependencies:

```bash
python3 -m pip install -e .
```

Validate the starter task:

```bash
python3 -m agentlab task validate tasks/starter
```

Verify a task's reference artifact:

```bash
python3 -m agentlab task verify-reference tasks/starter/2048-advanced-snake-params-001
```

Use `--no-write-artifacts` for a transient check that does not update
`reference-report.md`, `reference-result.json`, or `reference.diff`.

Smoke-test a task before repeated trials:

```bash
python3 -m agentlab task smoke-test \
  --task tasks/starter/2048-advanced-snake-params-001 \
  --agent codex
```

The smoke-test workflow verifies the reference artifact first, then runs exactly
one trial with one job. Inspect the emitted report and diff before scaling to
repeated or parallel trials.

Run the self-tests:

```bash
python3 -m unittest discover
```

Run a real task through the manual adapter once its `repo` and `commit` point to
an accessible Git repository:

```bash
python3 -m agentlab run --agent manual --task path/to/task-bundle
```

The manual adapter pauses after workspace setup so a human can edit the cloned
repo. Press Enter in the terminal when edits are complete; the evaluation
harness will then capture the diff and run the task graders. Use `--no-pause`
for a negative-control trial where the manual adapter intentionally changes
nothing.

Run a task through Codex CLI:

```bash
python3 -m agentlab run --agent codex --task tasks/starter/2048-advanced-snake-params-001
```

Run multiple independent trials:

```bash
python3 -m agentlab run \
  --agent codex \
  --trials 5 \
  --jobs 3 \
  --task tasks/starter/2048-advanced-snake-params-001
```

`--jobs` controls how many trials run at the same time. During parallel runs,
the terminal shows one aggregate trial progress bar plus trial-level
start information instead of per-agent progress bars. Passing batches print only
the aggregate summary; failed batches also print the failed trial IDs and report
paths.

Useful Codex options:

```bash
python3 -m agentlab run \
  --agent codex \
  --codex-model gpt-5.2 \
  --codex-reasoning-effort low \
  --codex-timeout-seconds 1800 \
  --task tasks/starter/2048-advanced-snake-params-001
```

The Codex adapter stores `codex-events.jsonl`, `codex-last-message.md`,
`transcript.md`, `diff.patch`, `report.md`, and `result.json` in the run
directory. Reports and result metadata include changed-file counts plus line
additions/deletions from the captured patch. When JSON events expose the actual
model used, `result.json` and reports derive `model_name` and `model_source`
from those events; an explicit CLI `--model` is retained as the requested model
rather than treated as authoritative runtime identity. `--codex-reasoning-effort`
requests a Codex reasoning level through `codex exec --config
model_reasoning_effort="<value>"`; the requested value is recorded separately
from recovered runtime `reasoning_effort` so ignored overrides remain visible.
By default it resolves `codex` from `PATH`. If the CLI is installed outside
`PATH`, fix the shell environment or use `--codex-command /path/to/codex` for
that run. While the agent process is running, the terminal shows a small
progress bar such as `waiting for agent response`; agent launch errors are also
printed to stderr instead of only appearing in the transcript.

Run a task through Claude Code:

```bash
python3 -m agentlab doctor --agent claude
python3 -m agentlab run \
  --agent claude \
  --task tasks/starter/2048-advanced-snake-params-001 \
  --trials 1 \
  --jobs 1
```

The Claude Code adapter invokes `claude -p` in print mode, writes
`claude-events.jsonl`, `claude-final-message.md`, `transcript.md`,
`diff.patch`, `report.md`, and `result.json`, and records the CLI version,
auth preflight status, selected model, permission mode, output format, max
turns, and allowed/disallowed tool rules when configured. By default it uses
`--permission-mode acceptEdits`, `--output-format stream-json`, `--verbose`, and
`--no-session-persistence` for isolated trials. Like Codex, actual model
identity is derived from Claude Code events when present. Use `--claude-command`
when the executable is outside `PATH`, `--claude-model` to request a model, and
repeated `--claude-allowed-tool` / `--claude-disallowed-tool` flags to tune the
tool surface for a smoke-tested task.

Reference verification uses the same report/result shape, marked with
`trial_kind: reference_verification`, and writes `reference-report.md`,
`reference-result.json`, and `reference.diff` by default.

List trials that have machine-readable metadata:

```bash
python3 -m agentlab trials list
```

Summarize trials by suite, task, agent harness, and model:

```bash
python3 -m agentlab trials summarize
```

`pass@k` means at least one fair trial in the group passed. `pass^k` means every
fair trial in the group passed. Trials marked `excluded` by human review remain
stored but do not count in those fair capability metrics. Summary tables show
primary review-label counts separately from secondary review-label caveats.
Summary tables also report accepted-result counts and token-normalized outcome
metrics. A verified result is a valid grader-passing trial; an accepted result is
a valid grader-passing trial with a primary `success_clean` review label. Token
spend includes failed valid trials in the numerator, so wasted attempts remain
visible. Input-plus-output tokens are the primary portable bucket, with cached
input and reasoning-output token buckets kept separate.

Generate a Markdown capability evidence digest for capability reports:

```bash
python3 -m agentlab report capability-evidence-digest --output reports/evidence-digest.md
```

The digest is generated evidence, not final interpretation. Use it as the data
backbone for hand-authored capability reports. Per-trial rows link to the
report, transcript, diff, and result artifacts so surprising pass rates can be
investigated without hunting through `runs/`. Aggregate and per-trial review
columns distinguish primary labels from secondary labels, and aggregate resource
columns show token spend per verified or accepted result when the selected trial
artifacts have complete token data.

For report prep, make the evidence set explicit instead of relying on every
local trial artifact:

```json
{
  "name": "codex-click-pilot",
  "description": "Selected Codex CLI trials for the Click pilot.",
  "trials": [
    "20260507-171508-click-help-shadowed-option-001-codex",
    "20260507-190123-click-default-map-nargs-001-codex-18672b25/result.json"
  ]
}
```

```bash
python3 -m agentlab report capability-evidence-digest \
  --evidence-set reports/codex-click-pilot.json \
  --output reports/evidence-digest.md
```

Attach a human review label to a trial:

```bash
python3 -m agentlab review --trial latest --label success_clean --note "Focused one-line fix; graders pass."
```

Exclude an invalid trial from fair summaries while preserving its artifacts:

```bash
python3 -m agentlab review \
  --trial latest \
  --label dependency_issue \
  --note "Task setup failed before the agent acted." \
  --exclude \
  --exclusion-reason setup_error
```

Archive reviewed excluded trials out of the active runs directory without
deleting evidence:

```bash
python3 -m agentlab trials archive-excluded --exclusion-reason setup_error
python3 -m agentlab trials archive-excluded --exclusion-reason setup_error --apply
```

The archive command is a dry run unless `--apply` is supplied. It moves matched
reviewed excluded trials under `runs/_archive/excluded/<reason>/` and appends a
machine-readable `archive-manifest.jsonl`.

The first real project task is:

```bash
python3 -m agentlab task validate tasks/starter/2048-advanced-snake-params-001
```

Regenerate task cards after changing task metadata or reference artifacts:

```bash
python3 .agents/skills/task-card/scripts/render_task_cards.py tasks
```

Enable the repo-local pre-commit hook:

```bash
git config core.hooksPath .githooks
```

The hook fails commits when generated task cards drift from `task.yaml`, and it
validates all task bundles through `agentlab.tasks.integrity`. Task
candidates and curation backlog live in GitHub Issues rather than in local
aggregate Markdown files.

## MVP Path

1. Validate task bundles, including suite/type/reference-artifact metadata.
2. Create isolated workspaces from task repos and commits.
3. Add a manual adapter that lets a human edit the checkout for positive-control trials.
4. Capture diffs and command results.
5. Generate a Markdown report.
6. Add Cursor SDK and additional agent adapters.

See [CONTEXT.md](CONTEXT.md) for project vocabulary,
[docs/design.md](docs/design.md) for architecture notes,
[docs/adr/](docs/adr/) for accepted architectural decisions,
[docs/anthropic-eval-principles.md](docs/anthropic-eval-principles.md) for the
terminology and practices this project follows,
[docs/failure-taxonomy.md](docs/failure-taxonomy.md) for the initial review
taxonomy, and [docs/runtime-accountability.md](docs/runtime-accountability.md)
for open work around model identity, account context, token usage, and cost. See
[reports/codex-starter-suite-12-task-baseline-2026-05-11/report.md](reports/codex-starter-suite-12-task-baseline-2026-05-11/report.md)
for the current Codex starter-suite baseline and
[docs/retrospectives/2026-05-08-first-eval-2048-advanced-snake.md](docs/retrospectives/2026-05-08-first-eval-2048-advanced-snake.md)
for the first completed positive/negative control evaluation.
