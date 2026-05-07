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

Avoid mandatory third-party runtime dependencies for the core loop. If PyYAML is
available, task loading can use it; otherwise a small built-in parser supports
the task-schema subset this project uses.

## Consequences

- The project can run on a stock macOS Python install.
- Tests can use `unittest` without extra setup.
- The YAML fallback parser should stay intentionally small; advanced YAML
  features are out of scope unless the project adopts a required dependency.
- Future web dashboards or richer storage should be added around the CLI, not in
  place of it.
