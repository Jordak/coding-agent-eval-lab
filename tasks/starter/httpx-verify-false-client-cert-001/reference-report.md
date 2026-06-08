# Reference Verification Report: httpx-verify-false-client-cert-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Task repository: `https://github.com/encode/httpx.git`
- Task commit: `0cb7e5a2e736628e2f506d259fcf0d48cd2bde82`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `3`
- Lines deleted: `4`

Setup-created untracked coverage caveat: 2044 setup-created untracked paths existed outside exact boundary-pattern matching. Changed-file counts/lists and boundary metrics include detected changes, but detection remains best-effort for worktree-only content-preserving edits to those paths.

## Run Surface

- Execution surface: `unknown`
- Runtime version: `unknown`
- Model identity source: `unknown`
- Sandbox mode: `unknown`
- Approval policy: `unknown`
- Tool policy: `unknown`
- Memory scope: `unknown`
- Network policy: `unknown`
- Timeout seconds: `unknown`
- Turn or step budget: `unknown`
- Stop reason: `success`
- Human intervention events: `none`
- Workspace history policy: `base_only`
- Workspace base ref: `5043f1479886c4c5f6e3f524465bbe168c6bb37f`

## Code-Based Graders

1. Assertion `python3 -m venv .agentlab/venv`: passed (0)
2. Assertion `python -m pip install --upgrade pip`: passed (0)

```text
Requirement already satisfied: pip in ./.agentlab/venv/lib/python3.13/site-packages (25.1.1)
Collecting pip
  Downloading pip-26.1.2-py3-none-any.whl.metadata (4.6 kB)
Downloading pip-26.1.2-py3-none-any.whl (1.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB 34.3 MB/s eta 0:00:00
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 25.1.1
    Uninstalling pip-25.1.1:
      Successfully uninstalled pip-25.1.1
Successfully installed pip-26.1.2
```

3. Assertion `python -m pip install -e . "pytest<9"`: passed (0)

```text
21 kB)
Collecting idna (from httpx==0.28.0)
  Using cached idna-3.18-py3-none-any.whl.metadata (6.1 kB)
Collecting iniconfig>=1 (from pytest<9)
  Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
Collecting packaging>=20 (from pytest<9)
  Using cached packaging-26.2-py3-none-any.whl.metadata (3.5 kB)
Collecting pluggy<2,>=1.5 (from pytest<9)
  Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting pygments>=2.7.2 (from pytest<9)
  Using cached pygments-2.20.0-py3-none-any.whl.metadata (2.5 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx==0.28.0)
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached packaging-26.2-py3-none-any.whl (100 kB)
Using cached pygments-2.20.0-py3-none-any.whl (1.2 MB)
Downloading anyio-4.13.0-py3-none-any.whl (114 kB)
Using cached idna-3.18-py3-none-any.whl (65 kB)
Using cached certifi-2026.5.20-py3-none-any.whl (134 kB)
Building wheels for collected packages: httpx
  Building editable for httpx (pyproject.toml): started
  Building editable for httpx (pyproject.toml): finished with status 'done'
  Created wheel for httpx: filename=httpx-0.28.0-py3-none-any.whl size=4921 sha256=badff137afab7bef72bbf4e3e0af07e5e778c12aaefefee844082c50fde662e9
  Stored in directory: /private/var/folders/3m/s27dbmbs1mn8yp8dmfxmtl9h0000gn/T/pip-ephem-wheel-cache-9ml56d2w/wheels/3f/e3/6a/162557ff5d76689efe1dc1cf98ab6eebb739b2cbcda4c53ee2
Successfully built httpx
Installing collected packages: pygments, pluggy, packaging, iniconfig, idna, h11, certifi, pytest, httpcore, anyio, httpx

Successfully installed anyio-4.13.0 certifi-2026.5.20 h11-0.16.0 httpcore-1.0.9 httpx-0.28.0 idna-3.18 iniconfig-2.3.0 packaging-26.2 pluggy-1.6.0 pygments-2.20.0 pytest-8.4.2
```

4. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`: passed (0)
5. Assertion `git apply reference.patch`: passed (0)
6. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`: passed (0)
7. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert="client.pem"); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem",)], calls'`: passed (0)
8. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`: passed (0)
9. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=True, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_REQUIRED, ctx.verify_mode; assert ctx.check_hostname is True, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`: passed (0)

## Changed Files

- `httpx/_config.py`
