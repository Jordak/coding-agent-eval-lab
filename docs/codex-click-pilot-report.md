# Codex Click Pilot Report

Date: 2026-05-07

## Scope

This pilot looked at Codex CLI on two real Click regression tasks in the
`starter-coding` suite:

- `click-default-map-nargs-001`
- `click-help-shadowed-option-001`

These results are local-runtime observations. They describe Codex CLI as
configured on this machine, with no explicit `--codex-model` supplied.

## Trial Environment

Both tasks now create a task-local Python 3.13 virtual environment during setup,
install Click in editable mode with `pytest<9`, prepend `.agentlab/venv/bin` to
`PATH`, and set `PYTHONPATH={workspace}/src`.

The `PYTHONPATH` setting matters because Click's editable install writes a
`.pth` file whose path contains a space from `Agent Eval Lab`; without an
explicit `PYTHONPATH`, post-agent graders could fail to import the local
checkout even when the agent's own validation commands passed.

## Fair Confirmation Trials

| Task | Trial | Status | Duration | Files Changed | Report |
| --- | --- | --- | ---: | ---: | --- |
| `click-default-map-nargs-001` | `20260507-191800-click-default-map-nargs-001-codex-f8be8394` | passed | 241s | 2 | `runs/20260507-191800-click-default-map-nargs-001-codex-f8be8394/report.md` |
| `click-help-shadowed-option-001` | `20260507-192403-click-help-shadowed-option-001-codex-c0a854fe` | passed | 257s | 3 | `runs/20260507-192403-click-help-shadowed-option-001-codex-c0a854fe/report.md` |

Under these conditions, Codex CLI produced grader-passing patches for both Click
tasks in one trial each.

## Excluded Trials

An earlier `5`-trial batch for `click-default-map-nargs-001` failed `0/5`, but
those trials are excluded from capability interpretation. The failures were due
to task-environment configuration, not the candidate patches: post-agent
graders failed with `ModuleNotFoundError: No module named 'click'` because the
task environment did not yet set `PYTHONPATH={workspace}/src`.

Those five runs should be reviewed as `dependency_issue` with trial validity
`excluded` and exclusion reason `setup_error`, so summaries show the reason for
exclusion without counting them in fair capability metrics.

## Observations

- Codex added regression tests in both passing trials.
- The default-map task patch changed `src/click/core.py` and
  `tests/test_defaults.py`.
- The help-option task patch changed `src/click/core.py`,
  `src/click/exceptions.py`, and `tests/test_formatting.py`.
- The results are encouraging, but they are not yet reliability measurements.
  Repeated fair trials are still needed before reporting consistency claims such
  as pass@k or pass^k for these tasks.

## Next Steps

- Use explicit trial-validity review metadata for dependency-issue runs so they
  do not distort pass-rate summaries.
- After a single-trial smoke test passes for any new task or environment change,
  run bounded repeated trials and report pass@k/pass^k.
- Add human review labels for the two passing Click trials after inspecting
  patch quality beyond deterministic grader success.
