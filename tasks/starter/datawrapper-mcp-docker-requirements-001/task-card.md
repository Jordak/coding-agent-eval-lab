# Datawrapper MCP Docker requirements should include app dependencies

- Task ID: `datawrapper-mcp-docker-requirements-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `python`
- Repository: `https://github.com/palewire/datawrapper-mcp.git`
- Commit: `15b5389e068bf5e673789da82a20f31fe3e81bd7`
- Source: `task.yaml`

## Prompt

Fix the Docker deployment dependency drift in datawrapper-mcp. The Dockerfile installs from deployment/requirements.txt, but that file is missing or pinning older runtime dependencies than pyproject.toml, which causes the deployed app to fail at startup with missing modules such as prefab_ui. Keep the Dockerfile's requirements.txt install strategy and update the deployment requirements so the app dependencies match pyproject.toml.

## Reference

Sync deployment/requirements.txt with pyproject.toml by using fastmcp[apps]==3.1.1, datawrapper>=2.0.14, and prefab-ui==0.8.0 while keeping the Dockerfile's existing pip install -r /app/deployment/requirements.txt path.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

- PYTEST_ADDOPTS=-p no:cacheprovider
- PYTHONDONTWRITEBYTECODE=1

## Graders

### Setup

- `python3 -c "from pathlib import Path; assert Path('pyproject.toml').is_file(); assert Path('Dockerfile').is_file(); assert Path('deployment/requirements.txt').is_file()"`

### Baseline

- `python3 -c "from pathlib import Path; req = Path('deployment/requirements.txt').read_text(); pyproject = Path('pyproject.toml').read_text(); dockerfile = Path('Dockerfile').read_text(); assert 'RUN pip install --no-cache-dir -r /app/deployment/requirements.txt' in dockerfile, dockerfile; assert 'prefab-ui==0.8.0' in pyproject and 'fastmcp[apps]==3.1.1' in pyproject and 'datawrapper>=2.0.14' in pyproject, pyproject; assert 'prefab-ui==0.8.0' not in req and 'fastmcp>=3.0.0' in req and 'datawrapper>=2.0.7' in req, req"`

### Target

- `python3 -c "from pathlib import Path; req = Path('deployment/requirements.txt').read_text(); dockerfile = Path('Dockerfile').read_text(); expected = ['fastmcp[apps]==3.1.1', 'datawrapper>=2.0.14', 'prefab-ui==0.8.0', 'pandas>=2.0.0', 'starlette>=0.27.0', 'uvicorn>=0.23.0']; missing = [item for item in expected if item not in req]; assert not missing, missing; assert 'fastmcp>=3.0.0' not in req and 'datawrapper>=2.0.7' not in req, req; assert 'RUN pip install --no-cache-dir -r /app/deployment/requirements.txt' in dockerfile, dockerfile"`
- `python3 -c "from pathlib import Path; server = Path('datawrapper_mcp/server.py').read_text(); req = Path('deployment/requirements.txt').read_text(); assert 'from fastmcp import FastMCP' in server and 'fastmcp[apps]==3.1.1' in req, req; assert 'from prefab_ui.app import PrefabApp' in server and 'prefab-ui==0.8.0' in req, req"`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `2`

## Tags

- `setup`
- `dependency`
- `docker`
- `python`
- `real-issue`

## Expected Failure Modes

- `dependency_issue`
- `tool_misuse`
- `stuck_or_timeout`
- `resource_inefficient`
- `context_miss`
- `bad_local_fix`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
