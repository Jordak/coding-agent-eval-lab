# Reference Verification Report: click-default-map-nargs-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Task repository: `https://github.com/pallets/click.git`
- Task commit: `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `5`
- Lines deleted: `0`

Setup-created untracked coverage caveat: 1802 setup-created untracked paths existed outside exact boundary-pattern matching. Changed-file counts/lists and boundary metrics include detected changes, but detection remains best-effort for worktree-only content-preserving edits to those paths.

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
- Workspace base ref: `9de2b9c9cba0c82374206783bb4b3853373e575c`

## Public Graders

1. Assertion `PYENV_VERSION=3.13.5 python3.13 -m venv .agentlab/venv`: passed (0)
2. Assertion `python -m pip install -e . "pytest<9"`: passed (0)

```text
[notice] A new release of pip is available: 25.1.1 -> 26.1.2
[notice] To update, run: pip install --upgrade pip
```

3. Assertion `python -c 'import click; from click.testing import CliRunner; cli = click.command()(click.option("--point", nargs=2, type=int)(lambda point: click.echo(repr(point)))); result = CliRunner().invoke(cli, [], default_map={"point":"3 4"}); assert result.exit_code != 0, result.output; assert "Value must be an iterable" in result.output, result.output'`: passed (0)
4. Assertion `git apply reference.patch`: passed (0)

## Hidden Verifier

- Patch: `verifier.patch`

1. Assertion `git apply hidden verifier patch: verifier.patch`: passed (0)
2. Assertion `python .agentlab_hidden/check_behavior.py`: passed (0)

```text
$ python -c 'import ast, click; from click.testing import CliRunner; cli = click.command()(click.option("--point", nargs=2, type=int)(lambda point: click.echo(repr(point)))); runner = CliRunner(); result = runner.invoke(cli, [], default_map={"point":"3 4"}); assert result.exit_code == 0, result.output; assert ast.literal_eval(result.output.strip()) == (3, 4), result.output; override = runner.invoke(cli, ["--point", "10", "20"], default_map={"point":"3 4"}); assert override.exit_code == 0, override.output; assert ast.literal_eval(override.output.strip()) == (10, 20), override.output'
$ python -c 'import ast, click; from click.testing import CliRunner; cli = click.command()(click.option("--word-pair", type=(str, str))(lambda word_pair: click.echo(repr(word_pair)))); result = CliRunner().invoke(cli, [], default_map={"word_pair":"hello world"}); assert result.exit_code == 0, result.output; assert ast.literal_eval(result.output.strip()) == ("hello", "world"), result.output'
$ python -c 'import click; from click.testing import CliRunner; cli = click.command()(click.option("--name")(lambda name: click.echo(name))); result = CliRunner().invoke(cli, [], default_map={"name":"hello world"}); assert result.exit_code == 0, result.output; assert result.output.strip() == "hello world", result.output'
```


## Changed Files

- `src/click/core.py`
