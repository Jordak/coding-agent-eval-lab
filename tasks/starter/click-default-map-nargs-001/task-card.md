# Click should split default_map strings for multi-value options

- Task ID: `click-default-map-nargs-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `python`
- Repository: `https://github.com/pallets/click.git`
- Commit: `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`
- Source: `task.yaml`

## Prompt

Fix Click's handling of string values supplied through default_map for multi-value parameters. When default_map provides a string for an option with nargs greater than 1, or for a tuple option type, Click should split the string the same way it splits environment variable values. Already-structured list or tuple values should still pass through unchanged, single-value string defaults should not be split, and explicit CLI arguments should still override default_map.

## Reference

In Option.consume_value, when a value comes from default_map and is a string for a multi-value parameter, split it with the parameter type's existing environment-variable splitting behavior before type conversion.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

- PATH prepends: `.agentlab/venv/bin`
- PYTEST_ADDOPTS=-p no:cacheprovider
- PYTHONDONTWRITEBYTECODE=1
- PYTHONPATH={workspace}/src
- VIRTUAL_ENV={workspace}/.agentlab/venv

## Hidden Verifier

- Patch: `verifier.patch`
- Commands: `1 command configured`

## Graders

### Setup

- `PYENV_VERSION=3.13.5 python3.13 -m venv .agentlab/venv`
- `python -m pip install -e . "pytest<9"`

### Baseline

- `python -c 'import click; from click.testing import CliRunner; cli = click.command()(click.option("--point", nargs=2, type=int)(lambda point: click.echo(repr(point)))); result = CliRunner().invoke(cli, [], default_map={"point":"3 4"}); assert result.exit_code != 0, result.output; assert "Value must be an iterable" in result.output, result.output'`

### Target

None configured.

## Success Criteria

- Tests must pass: `true`
- Max files changed: `2`

## Tags

- `bugfix`
- `python`
- `cli`
- `default-map`
- `real-issue`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `resource_inefficient`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
