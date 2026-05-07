# Reference Verification Report: 2048-advanced-snake-params-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `capability`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`

## Code-Based Graders

1. Assertion `python3 -c "import numpy"`: passed (0)
2. Assertion `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `python3 -c "from types import SimpleNamespace; from simulation import run_single_simulation; from ai.heuristics import get_advanced_heuristic_with_weights; weights = {'empty': 1.0, 'smooth': 2.0, 'mono': 3.0, 'snake': 4.0}; heuristic = get_advanced_heuristic_with_weights(weights); args = SimpleNamespace(ai='expectimax', heuristic='advanced-snake', depth=1, tag='eval-smoke'); result = run_single_simulation((args, weights, heuristic, {'name': heuristic.name, 'version': heuristic.version, 'description': heuristic.description})); assert result['params'] == weights, result; assert result['tag'] == 'eval-smoke', result"`: passed (0)
5. Assertion `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`: passed (0)

## Changed Files

- `simulation.py`
