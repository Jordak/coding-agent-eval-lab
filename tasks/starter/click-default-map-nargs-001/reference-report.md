# Reference Verification Report: click-default-map-nargs-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`

## Code-Based Graders

1. Assertion `PYENV_VERSION=3.13.5 python3.13 -m venv .agentlab/venv`: passed (0)
2. Assertion `python -m pip install -e . "pytest<9"`: passed (0)

```text
[notice] A new release of pip is available: 25.1.1 -> 26.1.1
[notice] To update, run: pip install --upgrade pip
```

3. Assertion `python -c 'import click; from click.testing import CliRunner; cli = click.command()(click.option("--point", nargs=2, type=int)(lambda point: click.echo(repr(point)))); result = CliRunner().invoke(cli, [], default_map={"point":"3 4"}); assert result.exit_code != 0, result.output; assert "Value must be an iterable" in result.output, result.output'`: passed (0)
4. Assertion `git apply reference.patch`: passed (0)
5. Assertion `python -c 'import ast, click; from click.testing import CliRunner; cli = click.command()(click.option("--point", nargs=2, type=int)(lambda point: click.echo(repr(point)))); runner = CliRunner(); result = runner.invoke(cli, [], default_map={"point":"3 4"}); assert result.exit_code == 0, result.output; assert ast.literal_eval(result.output.strip()) == (3, 4), result.output; override = runner.invoke(cli, ["--point", "10", "20"], default_map={"point":"3 4"}); assert override.exit_code == 0, override.output; assert ast.literal_eval(override.output.strip()) == (10, 20), override.output'`: passed (0)
6. Assertion `python -c 'import ast, click; from click.testing import CliRunner; cli = click.command()(click.option("--word-pair", type=(str, str))(lambda word_pair: click.echo(repr(word_pair)))); result = CliRunner().invoke(cli, [], default_map={"word_pair":"hello world"}); assert result.exit_code == 0, result.output; assert ast.literal_eval(result.output.strip()) == ("hello", "world"), result.output'`: passed (0)
7. Assertion `python -c 'import click; from click.testing import CliRunner; cli = click.command()(click.option("--name")(lambda name: click.echo(name))); result = CliRunner().invoke(cli, [], default_map={"name":"hello world"}); assert result.exit_code == 0, result.output; assert result.output.strip() == "hello world", result.output'`: passed (0)

## Changed Files

- `src/click/core.py`
