# First Eval: 2048 Advanced-Snake Params

## Task

The first real task targets `Jordak/2048-game` at commit
`aec81a17d78a60f1f69d64aade4c108423d1f97e`.

The bug is intentionally small and realistic: the CLI exposes the parameterized
heuristic as `advanced-snake`, but `simulation.py` only persisted custom weights
when the old name `advanced` was present. As a result, simulation result payloads
preserved the run tag but returned `params: None`.

## Success Signal

The task uses deterministic Python checks:

- Import the core dependency.
- Confirm basic `Game` construction still works.
- Run a single `advanced-snake` simulation with custom weights.
- Assert that the result payload preserves both `params` and `tag`.

## Negative Control

Running the manual adapter with `--no-pause` makes no edits. The harness should
clone the repo, run checks, capture an empty diff, and fail the target assertion.

Observed result:

- Status: failed.
- Files changed: 0.
- Failure: `params` was `None` for an `advanced-snake` simulation.

## Positive Control

Running the manual adapter with its human-edit pause allows a focused patch:

```diff
- 'params': weights if args.heuristic == 'advanced' else None,
+ 'params': weights if args.heuristic == 'advanced-snake' else None,
```

Observed result:

- Status: passed.
- Files changed: 1.
- Changed file: `simulation.py`.
- All setup, baseline, target, and post-check commands passed.

## What This Proves

This first eval proves the core loop:

- A task can pin an external repo and commit.
- The harness can isolate a workspace.
- The manual adapter can produce both negative and positive control runs.
- The report captures checks, changed files, transcript, and patch.
- Result metadata can be listed and human-reviewed.

## Next Step

The next meaningful milestone is an automated agent adapter that attempts this
same task without a human edit pause, so its behavior can be compared against
the manual positive and negative controls.
