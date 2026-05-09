# Reference Verification Report: datawrapper-mcp-docker-requirements-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `5`
- Lines deleted: `2`

## Code-Based Graders

1. Assertion `python3 -c "from pathlib import Path; assert Path('pyproject.toml').is_file(); assert Path('Dockerfile').is_file(); assert Path('deployment/requirements.txt').is_file()"`: passed (0)
2. Assertion `python3 -c "from pathlib import Path; req = Path('deployment/requirements.txt').read_text(); pyproject = Path('pyproject.toml').read_text(); dockerfile = Path('Dockerfile').read_text(); assert 'RUN pip install --no-cache-dir -r /app/deployment/requirements.txt' in dockerfile, dockerfile; assert 'prefab-ui==0.8.0' in pyproject and 'fastmcp[apps]==3.1.1' in pyproject and 'datawrapper>=2.0.14' in pyproject, pyproject; assert 'prefab-ui==0.8.0' not in req and 'fastmcp>=3.0.0' in req and 'datawrapper>=2.0.7' in req, req"`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `python3 -c "from pathlib import Path; req = Path('deployment/requirements.txt').read_text(); dockerfile = Path('Dockerfile').read_text(); expected = ['fastmcp[apps]==3.1.1', 'datawrapper>=2.0.14', 'prefab-ui==0.8.0', 'pandas>=2.0.0', 'starlette>=0.27.0', 'uvicorn>=0.23.0']; missing = [item for item in expected if item not in req]; assert not missing, missing; assert 'fastmcp>=3.0.0' not in req and 'datawrapper>=2.0.7' not in req, req; assert 'RUN pip install --no-cache-dir -r /app/deployment/requirements.txt' in dockerfile, dockerfile"`: passed (0)
5. Assertion `python3 -c "from pathlib import Path; server = Path('datawrapper_mcp/server.py').read_text(); req = Path('deployment/requirements.txt').read_text(); assert 'from fastmcp import FastMCP' in server and 'fastmcp[apps]==3.1.1' in req, req; assert 'from prefab_ui.app import PrefabApp' in server and 'prefab-ui==0.8.0' in req, req"`: passed (0)

## Changed Files

- `deployment/requirements.txt`
