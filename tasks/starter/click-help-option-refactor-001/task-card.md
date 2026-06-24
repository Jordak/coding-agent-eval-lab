# Click should deduplicate help option construction

- Task ID: `click-help-option-refactor-001`
- Suite: `starter-coding`
- Evaluation type: `capability`
- Language: `python`
- Repository: `https://github.com/pallets/click.git`
- Commit: `9aeb586cbc622c229bbf80ad948e590f596a8d3e`
- Source: `task.yaml`

## Prompt

Refactor Click's default help option construction so the automatic help option and the public help_option decorator share one reusable implementation. Preserve the existing CLI behavior for default help, custom help aliases, and commands with add_help_option disabled. Avoid changing externally visible behavior.

## Reference

Extract a HelpOption subclass in click.decorators, make help_option use it as the default option class, export HelpOption from click, and have Command.get_help_option instantiate the shared class. The reference patch is based on upstream pallets/click PR #2563.

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

- `python -c 'import click; assert not hasattr(click, "HelpOption")'`
- `python -c 'import click; from click.testing import CliRunner; cmd = click.Command("demo", params=[click.Option(["--name"], help="Name")], callback=lambda name: click.echo("hello " + name if name else "hello")); result = CliRunner().invoke(cmd, ["--help"]); assert result.exit_code == 0, result.output; assert "Usage: demo [OPTIONS]" in result.output, result.output; assert "--help" in result.output, result.output; assert "Show this message and exit." in result.output, result.output; disabled = click.Command("plain", add_help_option=False, callback=lambda: None); disabled_result = CliRunner().invoke(disabled, ["--help"]); assert disabled_result.exit_code == 2, disabled_result.output; assert "No such option: --help" in disabled_result.output, disabled_result.output'`
- `python -c 'import click; from click.testing import CliRunner; cli = click.help_option("-h", "--halp")(click.command()(lambda: click.echo("ran"))); runner = CliRunner(); short_help = runner.invoke(cli, ["-h"]); long_help = runner.invoke(cli, ["--halp"]); normal_run = runner.invoke(cli, []); assert short_help.exit_code == 0, short_help.output; assert long_help.exit_code == 0, long_help.output; assert "Usage:" in short_help.output, short_help.output; assert "Usage:" in long_help.output, long_help.output; assert normal_run.exit_code == 0, normal_run.output; assert normal_run.output.strip() == "ran", normal_run.output'`

### Target

- `python -c 'from pathlib import Path; core = Path("src/click/core.py").read_text(); decorators = Path("src/click/decorators.py").read_text(); assert "def show_help(ctx: Context" not in core, "automatic help should no longer define its own nested callback"; assert "def callback(ctx: Context" not in decorators.split("def help_option", 1)[1], "help_option should reuse shared help implementation instead of defining a duplicate callback"; assert ("HelpOption" in core and "HelpOption" in decorators) or ("_make_help_option" in core and "_make_help_option" in decorators), "automatic help and help_option should share a reusable implementation"'`
- `python -c 'import click; from click.testing import CliRunner; cmd = click.Command("demo", params=[click.Option(["--name"], help="Name")], callback=lambda name: click.echo("hello " + name if name else "hello")); result = CliRunner().invoke(cmd, ["--help"]); assert result.exit_code == 0, result.output; assert "Usage: demo [OPTIONS]" in result.output, result.output; assert "--help" in result.output, result.output; assert "Show this message and exit." in result.output, result.output; disabled = click.Command("plain", add_help_option=False, callback=lambda: None); disabled_result = CliRunner().invoke(disabled, ["--help"]); assert disabled_result.exit_code == 2, disabled_result.output; assert "No such option: --help" in disabled_result.output, disabled_result.output'`
- `python -c 'import click; from click.testing import CliRunner; cli = click.help_option("-h", "--halp")(click.command()(lambda: click.echo("ran"))); runner = CliRunner(); short_help = runner.invoke(cli, ["-h"]); long_help = runner.invoke(cli, ["--halp"]); normal_run = runner.invoke(cli, []); assert short_help.exit_code == 0, short_help.output; assert long_help.exit_code == 0, long_help.output; assert "Usage:" in short_help.output, short_help.output; assert "Usage:" in long_help.output, long_help.output; assert normal_run.exit_code == 0, normal_run.output; assert normal_run.output.strip() == "ran", normal_run.output'`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `3`

## Tags

- `refactor`
- `python`
- `cli`
- `help-option`
- `real-pr`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `resource_inefficient`
- `tool_misuse`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
