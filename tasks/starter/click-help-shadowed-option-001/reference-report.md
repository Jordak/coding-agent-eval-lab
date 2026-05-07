# Reference Verification Report: click-help-shadowed-option-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`

## Code-Based Graders

1. Assertion `python3 -c 'import sys; sys.path.insert(0,"src"); import click'`: passed (0)
2. Assertion `python3 -c 'import sys; sys.path.insert(0,"src"); import click; from click.testing import CliRunner; cli = click.group("cli", context_settings={"help_option_names":["-h","--help"]})(lambda: None); foo = click.command("foo")(click.option("--host","-h")(click.argument("required_arg")(lambda required_arg, host: None))); cli.add_command(foo); result = CliRunner().invoke(cli, ["foo"]); expected = "Try " + chr(39) + "cli foo -h" + chr(39) + " for help."; assert result.exit_code == 2, result.output; assert expected in result.output, result.output'`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `python3 -c 'import sys; sys.path.insert(0,"src"); import click; from click.testing import CliRunner; cli = click.group("cli", context_settings={"help_option_names":["-h","--help"]})(lambda: None); foo = click.command("foo")(click.option("--host","-h")(click.argument("required_arg")(lambda required_arg, host: None))); cli.add_command(foo); runner = CliRunner(); result = runner.invoke(cli, ["foo"]); expected = "Try " + chr(39) + "cli foo --help" + chr(39) + " for help."; bad = "Try " + chr(39) + "cli foo -h" + chr(39) + " for help."; assert result.exit_code == 2, result.output; assert expected in result.output, result.output; assert bad not in result.output, result.output; help_result = runner.invoke(cli, ["foo", "--help"]); assert help_result.exit_code == 0, help_result.output; assert "--help" in help_result.output, help_result.output'`: passed (0)
5. Assertion `python3 -c 'import sys; sys.path.insert(0,"src"); import click; from click.testing import CliRunner; cli = click.group("cli", context_settings={"help_option_names":["-h","--help"]})(lambda: None); foo = click.command("foo")(click.option("--host","-h")(click.option("--help-file","--help")(click.argument("required_arg")(lambda required_arg, help_file, host: None)))); cli.add_command(foo); result = CliRunner().invoke(cli, ["foo"]); assert result.exit_code == 2, result.output; assert "Try " not in result.output, result.output'`: passed (0)

## Changed Files

- `src/click/exceptions.py`
