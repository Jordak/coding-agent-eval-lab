# ADR 0001: Use A Standard-Library-First Python CLI

Status: Accepted

Date: 2026-05-07

## Context

Agent Eval Lab should be easy to run in a fresh local checkout while the eval
method is still taking shape. Early work should not be blocked by packaging,
services, or frontend infrastructure.

## Decision

Build the initial harness as a Python package with a standard-library CLI
entrypoint:

```bash
python3 -m agentlab
```

Keep the core harness simple and local-first, but require PyYAML for `task.yaml`
loading. Task bundles are authored YAML artifacts, and real-world task commands
need YAML features such as folded scalars, quoting, nested mappings, and `:`
inside shell/Python/JavaScript snippets. Maintaining a parallel YAML subset
parser would make task loading less predictable than the generated tasks it is
supposed to validate.

## Consequences

- A fresh checkout must install package dependencies before using the CLI.
- Tests can use `unittest` without extra setup.
- Task loading has one parser path, so pre-commit, local CLI use, and installed
  package use agree on YAML semantics.
- Future web dashboards or richer storage should be added around the CLI, not in
  place of it.
