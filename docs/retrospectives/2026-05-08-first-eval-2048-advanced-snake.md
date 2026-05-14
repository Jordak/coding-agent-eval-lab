# First Eval: 2048 Advanced-Snake Params

Date: 2026-05-08

## Task

The first real task targets `Jordak/2048-game` at commit
`aec81a17d78a60f1f69d64aade4c108423d1f97e`.

The bug is intentionally small and realistic: the CLI exposes the parameterized
heuristic as `advanced-snake`, but `simulation.py` only persisted custom weights
when the old name `advanced` was present. As a result, simulation result payloads
preserved the trial tag but returned `params: None`.

## Code-Based Graders

The task uses deterministic Python assertions:

- Import the core dependency.
- Confirm basic `Game` construction still works.
- Run a single `advanced-snake` simulation with custom weights.
- Assert that the result payload preserves both `params` and `tag`.

## Negative-Control Trial

Running the manual adapter with `--no-pause` makes no edits. The evaluation
harness should clone the repo, run code-based graders, capture an empty diff,
and fail the target assertion.

Observed result:

- Status: failed.
- Files changed: 0.
- Failure: `params` was `None` for an `advanced-snake` simulation.

## Positive-Control Trial

Running the manual adapter with its human-edit pause allows a focused patch:

```diff
- 'params': weights if args.heuristic == 'advanced' else None,
+ 'params': weights if args.heuristic == 'advanced-snake' else None,
```

Observed result:

- Status: passed.
- Files changed: 1.
- Changed file: `simulation.py`.
- All setup, baseline, target, and post-change assertions passed.

## First Codex CLI Trials

After adding the Codex CLI adapter, the same task was run with:

```bash
python3 -m agentlab run --agent codex --task tasks/starter/2048-advanced-snake-params-001
```

The first trial exposed an adapter bug: `--ask-for-approval` was passed after
`exec`, but this Codex CLI expects that option before the subcommand. The harness
captured the runtime error in `transcript.md` and `result.json`. Under the
current trial-validity vocabulary, this run is reviewed as `tool_misuse` by the
evaluation harness with trial validity `excluded` and exclusion reason
`eval_harness_error`, because Codex exited before it could attempt the task.

Run `python3 -m agentlab doctor --agent codex` before new Codex trial batches to
catch this class of adapter/runtime launch problem before creating task trials.

After fixing the adapter command shape, Codex completed the task successfully:

- Status: passed.
- Duration: about 69 seconds.
- Files changed: 2.
- Changed files: `simulation.py`, `test_ai.py`.
- Review label: `success_clean`.

Codex made the same production fix as the manual positive control and also
updated the stale local unit test fixture to use `advanced-snake`, include `tag`,
and assert the current heuristic metadata.

## What This Proves

This first eval proves the core loop:

- A task can pin an external repo and commit.
- The evaluation harness can isolate a workspace.
- The manual adapter can produce both negative and positive control trials.
- The Codex CLI adapter can run a trial non-interactively and produce a passing
  patch.
- The report captures grader assertions, changed files, transcript, and patch.
- Result metadata can be listed and human-reviewed.

## Next Step

The next meaningful milestone was adding an automated agent adapter that
attempts this same task without a human edit pause, so its behavior can be
compared against the manual positive and negative controls. That milestone is
now complete for Codex CLI.

## Repeated Codex CLI Batch

On 2026-05-08, a bounded Codex CLI batch was run against the publishable
`starter-coding` task after the starter suite was cleaned up.

Preflight and reference checks:

```bash
python3 -m agentlab doctor --agent codex
python3 -m agentlab task verify-reference tasks/starter/2048-advanced-snake-params-001 --no-write-artifacts
python3 -m agentlab task smoke-test --task tasks/starter/2048-advanced-snake-params-001 --agent codex
```

Repeated trials:

```bash
python3 -m agentlab run --agent codex --task tasks/starter/2048-advanced-snake-params-001 --trials 3 --jobs 3
python3 -m agentlab run --agent codex --task tasks/starter/2048-advanced-snake-params-001 --trials 1 --jobs 1
```

The selected evidence set is tracked at
`evidence-sets/codex-2048-advanced-snake-2026-05-08.json` and can be rendered
with:

```bash
python3 -m agentlab report capability-evidence-digest \
  --evidence-set evidence-sets/codex-2048-advanced-snake-2026-05-08.json \
  --runs-dir runs \
  --output reports/evidence-digest.md
```

Selected trial IDs:

- `20260508-192558-2048-advanced-snake-params-001-codex-a24c0d88`
- `20260508-192836-2048-advanced-snake-params-001-codex-852468e7`
- `20260508-192836-2048-advanced-snake-params-001-codex-c28086a4`
- `20260508-192836-2048-advanced-snake-params-001-codex-f9940a53`
- `20260508-193138-2048-advanced-snake-params-001-codex-036d2392`

Current aggregate for this evidence set:

- Total trials: 5.
- Fair trials: 5.
- Excluded trials: 0.
- Passes: 5.
- Pass rate: 1.00.
- pass@k: 1.00.
- pass^k: 1.00.
- Human reviews: `success_clean:5`.
- Median duration: 122522 ms.
- Median changed files: 2.
- Median lines added/deleted: 11/7.

This turns the one-off Codex success into a consistency measurement under the
local Codex CLI runtime captured by the trial artifacts.
