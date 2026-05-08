# Invalid JSON should return 400

- Task ID: `python-bugfix-001`
- Suite: `starter-coding`
- Evaluation type: `capability`
- Language: `python`
- Repository: `https://github.com/example/small-flask-app`
- Commit: `abc123`
- Source: `task.yaml`

## Prompt

Fix the bug where invalid JSON request bodies return a 500 instead of a 400.

## Reference

Illustrative placeholder task only. Replace with a real repo commit and a known passing reference patch before using in a publishable eval suite.

## Reference Artifact

No verified reference artifact configured yet.

## Environment

No task-local environment configured.

## Graders

### Setup

- `python -m pip install -e .`

### Baseline

- `pytest`

### Target

- `pytest tests/test_errors.py`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `4`

## Tags

- `bugfix`
- `backend`
- `error-handling`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `over_edit`
- `tool_misuse`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
