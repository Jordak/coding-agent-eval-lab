# Advanced-snake simulations should persist custom weights

- Task ID: `2048-advanced-snake-params-001`
- Suite: `starter-coding`
- Evaluation type: `capability`
- Language: `python`
- Repository: `https://github.com/Jordak/2048-game.git`
- Commit: `aec81a17d78a60f1f69d64aade4c108423d1f97e`
- Source: `task.yaml`

## Prompt

Fix the simulation metadata bug where trials using the advanced-snake heuristic do not persist their custom heuristic weights in the result payload. The CLI exposes this heuristic as advanced-snake, so a simulation with custom weights should return those weights in the params field and preserve the trial tag.

## Reference

In simulation.py, persist params when args.heuristic is advanced-snake instead of the obsolete advanced name; a focused solution changes only that condition and may optionally update stale tests to match the renamed heuristic.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

- PYTEST_ADDOPTS=-p no:cacheprovider
- PYTHONDONTWRITEBYTECODE=1

## Hidden Verifier

- Patch: `verifier.patch`
- Commands: `1 command configured`

## Graders

### Setup

- `python3 -c "import numpy"`

### Baseline

- `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`

### Target

None configured.

## Success Criteria

- Tests must pass: `true`
- Max files changed: `3`

## Tags

- `bugfix`
- `python`
- `simulation`
- `metadata`
- `real-failure`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `tool_misuse`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
