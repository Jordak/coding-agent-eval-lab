# Advanced-snake simulations should persist custom weights

- Task ID: `2048-advanced-snake-params-001`
- Suite: `starter-coding`
- Evaluation type: `capability`
- Language: `python`
- Repository: `https://github.com/Jordak/2048-game.git`
- Commit: `aec81a17d78a60f1f69d64aade4c108423d1f97e`
- Source: `task.yaml`

## Prompt

Fix the simulation metadata bug where trials using the advanced-snake heuristic do not persist their custom heuristic weights in the result payload. The CLI exposes this heuristic as advanced-snake, so a simulation with custom weights should return those weights in the params field and preserve the trial tag. Keep the patch focused and run the relevant tests.

## Reference

In simulation.py, persist params when args.heuristic is advanced-snake instead of the obsolete advanced name; a focused solution changes only that condition and may optionally update stale tests to match the renamed heuristic.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

- PYTEST_ADDOPTS=-p no:cacheprovider
- PYTHONDONTWRITEBYTECODE=1

## Graders

### Setup

- `python3 -c "import numpy"`

### Baseline

- `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`

### Target

- `python3 -c "from types import SimpleNamespace; from simulation import run_single_simulation; from ai.heuristics import get_advanced_heuristic_with_weights; weights = {'empty': 1.0, 'smooth': 2.0, 'mono': 3.0, 'snake': 4.0}; heuristic = get_advanced_heuristic_with_weights(weights); args = SimpleNamespace(ai='expectimax', heuristic='advanced-snake', depth=1, tag='eval-smoke'); result = run_single_simulation((args, weights, heuristic, {'name': heuristic.name, 'version': heuristic.version, 'description': heuristic.description})); assert result['params'] == weights, result; assert result['tag'] == 'eval-smoke', result"`
- `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`

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
