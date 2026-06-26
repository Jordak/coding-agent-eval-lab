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

Setup-created untracked coverage caveat: 1299 setup-created untracked paths existed outside exact boundary-pattern matching. Changed-file counts/lists and boundary metrics include detected changes, but detection remains best-effort for worktree-only content-preserving edits to those paths.

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

## Public Graders

1. Assertion `python3 -m venv .agentlab/venv`: passed (0)
2. Assertion `python -m pip install --upgrade pip`: passed (0)

```text
Requirement already satisfied: pip in ./.agentlab/venv/lib/python3.9/site-packages (21.2.4)
Collecting pip
  Using cached pip-26.0.1-py3-none-any.whl (1.8 MB)
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 21.2.4
    Uninstalling pip-21.2.4:
      Successfully uninstalled pip-21.2.4
Successfully installed pip-26.0.1
```

3. Assertion `python -m pip install -e . "pytest<9"`: passed (0)

```text
data (2.5 kB)
Collecting tomli>=1 (from pytest<9)
  Using cached tomli-2.4.1-py3-none-any.whl.metadata (10 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx==0.28.0)
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting typing-extensions>=4.6.0 (from exceptiongroup>=1->pytest<9)
  Using cached typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached exceptiongroup-1.3.1-py3-none-any.whl (16 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached iniconfig-2.1.0-py3-none-any.whl (6.0 kB)
Using cached packaging-26.2-py3-none-any.whl (100 kB)
Using cached pygments-2.20.0-py3-none-any.whl (1.2 MB)
Using cached tomli-2.4.1-py3-none-any.whl (14 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached anyio-4.12.1-py3-none-any.whl (113 kB)
Using cached idna-3.18-py3-none-any.whl (65 kB)
Using cached certifi-2026.6.17-py3-none-any.whl (133 kB)
Building wheels for collected packages: httpx
  Building editable for httpx (pyproject.toml): started
  Building editable for httpx (pyproject.toml): finished with status 'done'
  Created wheel for httpx: filename=httpx-0.28.0-py3-none-any.whl size=4878 sha256=35161bedc4cde7225abf08a86ca87ad77e324aad97ffc9fc30d3f7b725474ae0
  Stored in directory: /private/var/folders/3m/s27dbmbs1mn8yp8dmfxmtl9h0000gn/T/pip-ephem-wheel-cache-o1vu442_/wheels/b4/1f/31/93c94facf0f7e16355c86f731264009a167ff283a25bcb8898
Successfully built httpx
Installing collected packages: typing-extensions, tomli, pygments, pluggy, packaging, iniconfig, idna, h11, certifi, httpcore, exceptiongroup, pytest, anyio, httpx

Successfully installed anyio-4.12.1 certifi-2026.6.17 exceptiongroup-1.3.1 h11-0.16.0 httpcore-1.0.9 httpx-0.28.0 idna-3.18 iniconfig-2.1.0 packaging-26.2 pluggy-1.6.0 pygments-2.20.0 pytest-8.4.2 tomli-2.4.1 typing-extensions-4.15.0
```

4. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`: passed (0)
5. Assertion `git apply reference.patch`: passed (0)

## Hidden Verifier

- Patch: `verifier.patch`

1. Assertion `git apply hidden verifier patch: verifier.patch`: passed (0)
2. Assertion `python .agentlab_hidden/check_behavior.py`: passed (0)

```text
$ python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'
$ python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert="client.pem"); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem",)], calls'
$ python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'
$ python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=True, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_REQUIRED, ctx.verify_mode; assert ctx.check_hostname is True, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'
```


## Changed Files

- `httpx/_config.py`
