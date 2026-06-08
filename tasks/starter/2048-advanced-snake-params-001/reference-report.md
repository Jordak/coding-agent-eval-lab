# Reference Verification Report: 2048-advanced-snake-params-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `capability`
- Task repository: `https://github.com/Jordak/2048-game.git`
- Task commit: `aec81a17d78a60f1f69d64aade4c108423d1f97e`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `2`
- Lines deleted: `2`

## Run Surface

- Execution surface: `unknown`
- Runtime version: `unknown`
- Model identity source: `unknown`
- Sandbox mode: `unknown`
- Approval policy: `unknown`
- Tool policy: `unknown`
- Memory scope: `unknown`
- Network policy: `unknown`
- Timeout seconds: `unknown`
- Turn or step budget: `unknown`
- Stop reason: `success`
- Human intervention events: `none`
- Workspace history policy: `base_only`
- Workspace base ref: `f07a425c106ce205170bc3eb23e722ce1fa0233d`

## Code-Based Graders

1. Assertion `python3 -c "import numpy"`: passed (0)
2. Assertion `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `python3 -c "from types import SimpleNamespace; from simulation import run_single_simulation; from ai.heuristics import get_advanced_heuristic_with_weights; weights = {'empty': 1.0, 'smooth': 2.0, 'mono': 3.0, 'snake': 4.0}; heuristic = get_advanced_heuristic_with_weights(weights); args = SimpleNamespace(ai='expectimax', heuristic='advanced-snake', depth=1, tag='eval-smoke'); result = run_single_simulation((args, weights, heuristic, {'name': heuristic.name, 'version': heuristic.version, 'description': heuristic.description})); assert result['params'] == weights, result; assert result['tag'] == 'eval-smoke', result"`: passed (0)
5. Assertion `python3 -c "from game import Game; game = Game(); assert game.board.shape == (4, 4); assert not game.game_over()"`: passed (0)

## Changed Files

- `simulation.py`
