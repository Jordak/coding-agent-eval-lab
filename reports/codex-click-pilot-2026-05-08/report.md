# Codex Click Pilot Capability Report

Date: 2026-05-08

## Scope

This report covers Codex CLI as the local `codex` agent harness on two real
Click regression tasks in the `starter-coding` suite:

- `click-help-shadowed-option-001`
- `click-default-map-nargs-001`

These are evidence-scoped observations about this local harness configuration,
not claims about Codex or any underlying model globally. No explicit
`--codex-model` was supplied for these trials, so model identity and dollar cost
remain unknown. Token counts are recorded when the Codex event stream exposes
them.

## Runtime Conditions

Both tasks create a task-local Python 3.13 virtual environment during setup,
install Click in editable mode with `pytest<9`, prepend `.agentlab/venv/bin` to
`PATH`, and set `PYTHONPATH={workspace}/src`.

The explicit `PYTHONPATH` is important for this repository path because
`Agent Eval Lab` contains a space. Before the task environment was corrected,
post-agent graders could fail to import the local Click checkout even when the
agent patch itself was plausible.

Before new Codex batches, run:

```bash
python3 -m agentlab doctor --agent codex
```

During this report update, the preflight found `/opt/homebrew/bin/codex`,
reported `codex-cli 0.129.0-alpha.15`, and accepted the current non-interactive
`exec` command shape.

## Aggregate Evidence

Generated from local trial artifacts with:

```bash
python3 -m agentlab trials summarize
python3 -m agentlab report capability-evidence-digest --output reports/codex-click-pilot-2026-05-08/evidence-digest.md
python3 -m agentlab run --agent codex --task tasks/starter/click-default-map-nargs-001 --trials 3 --jobs 3
```

| Task | Total Trials | Fair Trials | Excluded Trials | Fair Passes | Fair Pass Rate | pass@k | pass^k | Human Review | Exclusions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `click-help-shadowed-option-001` | 7 | 6 | 1 | 6 | 1.00 | 1.00 | 1.00 | `success_clean:6` | `eval_harness_error:1` |
| `click-default-map-nargs-001` | 9 | 4 | 5 | 4 | 1.00 | 1.00 | 1.00 | `success_clean:4` | `setup_error:5` |

The help-option task has enough fair repeated trials to support a narrow
consistency observation under these conditions: all six fair Codex trials
passed the deterministic graders and were reviewed as `success_clean`.

The default-map task now has four fair trials after the corrected task
environment and bounded follow-up batch. All four fair trials passed and were
reviewed as `success_clean`. The five excluded setup-error trials remain useful
diagnostic evidence about the earlier environment, but they do not count in fair
capability metrics.

Under the current token-normalized outcome semantics, the ten fair passing
trials in this pilot are both verified and accepted results because each has a
primary `success_clean` review label. Those fair trials used 12,788,931 reported
input-plus-output tokens, or about 1,278,893 tokens per verified/accepted
result. This pilot predates the later model-attribution cleanup, so the newer
12-task report should be preferred for broader Codex resource interpretation.

## What Codex Did Well

On these Click tasks, Codex consistently found the relevant production area and
added regression tests in the passing trials.

For `click-help-shadowed-option-001`, the fair trials edited three files with a
median of 62.5 added lines and 12 deleted lines. All fair trials passed. The
patches generally changed Click option parsing/error formatting behavior and
added coverage around the shadowed help-option case.

For `click-default-map-nargs-001`, the fair trials edited two files with a
median of 88 added lines and 2.5 deleted lines. All fair trials passed. The
patches generally changed default-map value handling and added regression tests
for multi-value string defaults.

## What Was Brittle

The strongest brittleness was not Codex's code generation. It was the
evaluation harness/runtime path and task environment.

- One early help-option run is excluded as `eval_harness_error` because the
  evaluation harness could not discover or invoke the local Codex CLI, so Codex
  did not attempt the task.
- Five default-map runs are excluded as `setup_error` because the task-local
  environment did not yet expose the local Click checkout to post-agent graders.
- Those invalid runs still matter as lab evidence: they led to explicit trial
  validity, exclusion reasons, task-local environment fixes, and the Codex
  preflight.

## Recommendations

For technical evaluators:

- Treat Codex Click results as local-runtime, harness-specific evidence.
- Run `agentlab doctor --agent codex` before spending a repeated trial batch.
- Keep invalid setup, eval-harness, and operator failures excluded from fair
  capability summaries, but preserve their transcripts for diagnosis.
- Repeat this same pattern before expanding to new task categories: reference
  verification, one-trial smoke test, then a bounded fair batch.

For solo developers:

- Under these evaluated conditions, Codex was strong on focused library
  regression tasks with clear target behavior and deterministic tests.
- The main caveat is environment setup. If a project's local install, import
  path, or test command is shaky, agent performance can look worse than it is.
- The useful question is not "does Codex always solve Click bugs?" It is "with a
  clean task environment and focused regression prompt, did this agent harness
  produce reviewed, grader-passing patches on these tasks?" For this pilot, yes.

## Trial Artifact Index

Raw trial artifacts were local, ignored files used during original review.
Per-trial artifact paths are omitted from this checked-in report because they can disappear after temporary worktree cleanup.

| Trial | Task | Outcome | Validity | Artifact Availability |
| --- | --- | --- | --- | --- |
| `20260507-170846-click-help-shadowed-option-001-codex` | `click-help-shadowed-option-001` | failed | excluded: `eval_harness_error` | local artifacts omitted |
| `20260507-171508-click-help-shadowed-option-001-codex` | `click-help-shadowed-option-001` | passed | valid | local artifacts omitted |
| `20260507-175243-click-help-shadowed-option-001-codex` | `click-help-shadowed-option-001` | passed | valid | local artifacts omitted |
| `20260507-183521-click-help-shadowed-option-001-codex-20f74f8c` | `click-help-shadowed-option-001` | passed | valid | local artifacts omitted |
| `20260507-183521-click-help-shadowed-option-001-codex-b0c8e35f` | `click-help-shadowed-option-001` | passed | valid | local artifacts omitted |
| `20260507-183521-click-help-shadowed-option-001-codex-d191b2b5` | `click-help-shadowed-option-001` | passed | valid | local artifacts omitted |
| `20260507-192403-click-help-shadowed-option-001-codex-c0a854fe` | `click-help-shadowed-option-001` | passed | valid | local artifacts omitted |
| `20260507-190123-click-default-map-nargs-001-codex-18672b25` | `click-default-map-nargs-001` | failed | excluded: `setup_error` | local artifacts omitted |
| `20260507-190123-click-default-map-nargs-001-codex-40da680b` | `click-default-map-nargs-001` | failed | excluded: `setup_error` | local artifacts omitted |
| `20260507-190123-click-default-map-nargs-001-codex-8990300d` | `click-default-map-nargs-001` | failed | excluded: `setup_error` | local artifacts omitted |
| `20260507-190627-click-default-map-nargs-001-codex-da315bee` | `click-default-map-nargs-001` | failed | excluded: `setup_error` | local artifacts omitted |
| `20260507-190743-click-default-map-nargs-001-codex-45ab8712` | `click-default-map-nargs-001` | failed | excluded: `setup_error` | local artifacts omitted |
| `20260507-191800-click-default-map-nargs-001-codex-f8be8394` | `click-default-map-nargs-001` | passed | valid | local artifacts omitted |
| `20260507-212911-click-default-map-nargs-001-codex-59243485` | `click-default-map-nargs-001` | passed | valid | local artifacts omitted |
| `20260507-212911-click-default-map-nargs-001-codex-953cf220` | `click-default-map-nargs-001` | passed | valid | local artifacts omitted |
| `20260507-212911-click-default-map-nargs-001-codex-a2253130` | `click-default-map-nargs-001` | passed | valid | local artifacts omitted |
