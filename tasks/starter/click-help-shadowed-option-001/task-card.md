# Click should not suggest a shadowed help option

- Task ID: `click-help-shadowed-option-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `python`
- Repository: `https://github.com/pallets/click.git`
- Commit: `f1f191ecd2c790b161187c78e7c88440e9524e5c`
- Source: `task.yaml`

## Prompt

Fix Click's usage-error help hint when a nested command shadows one of the configured help option names. If a group configures help names such as -h and --help, but a subcommand uses -h for another option, the missing-argument error should not suggest `cli foo -h` for help because that command no longer opens help. Suggest a help option that still works, and avoid printing a misleading help hint when all configured help names are shadowed. Keep the patch focused and run the relevant checks.

## Reference

In UsageError.show, derive the available help option names from the current command context instead of blindly using the first configured help name. A focused solution reuses Click's existing help-option filtering and chooses a surviving help name for the error hint.

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

## Graders

### Setup

- `PYENV_VERSION=3.13.5 python3.13 -m venv .agentlab/venv`
- `python -m pip install -e . "pytest<9"`

### Baseline

- `python -c 'import click; from click.testing import CliRunner; cli = click.group("cli", context_settings={"help_option_names":["-h","--help"]})(lambda: None); foo = click.command("foo")(click.option("--host","-h")(click.argument("required_arg")(lambda required_arg, host: None))); cli.add_command(foo); result = CliRunner().invoke(cli, ["foo"]); expected = "Try " + chr(39) + "cli foo -h" + chr(39) + " for help."; assert result.exit_code == 2, result.output; assert expected in result.output, result.output'`

### Target

- `python -c 'import click; from click.testing import CliRunner; cli = click.group("cli", context_settings={"help_option_names":["-h","--help"]})(lambda: None); foo = click.command("foo")(click.option("--host","-h")(click.argument("required_arg")(lambda required_arg, host: None))); cli.add_command(foo); runner = CliRunner(); result = runner.invoke(cli, ["foo"]); expected = "Try " + chr(39) + "cli foo --help" + chr(39) + " for help."; bad = "Try " + chr(39) + "cli foo -h" + chr(39) + " for help."; assert result.exit_code == 2, result.output; assert expected in result.output, result.output; assert bad not in result.output, result.output; help_result = runner.invoke(cli, ["foo", "--help"]); assert help_result.exit_code == 0, help_result.output; assert "--help" in help_result.output, help_result.output'`
- `python -c 'import click; from click.testing import CliRunner; cli = click.group("cli", context_settings={"help_option_names":["-h","--help"]})(lambda: None); foo = click.command("foo")(click.option("--host","-h")(click.option("--help-file","--help")(click.argument("required_arg")(lambda required_arg, help_file, host: None)))); cli.add_command(foo); result = CliRunner().invoke(cli, ["foo"]); assert result.exit_code == 2, result.output; assert "Try " not in result.output, result.output'`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `3`

## Tags

- `bugfix`
- `python`
- `cli`
- `error-message`
- `real-issue`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `tool_misuse`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
