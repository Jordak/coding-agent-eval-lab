# Reference Verification Report: httpx-verify-false-client-cert-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `3`
- Lines deleted: `4`

## Code-Based Graders

1. Assertion `python3 -m venv .agentlab/venv`: passed (0)
2. Assertion `python -m pip install --upgrade pip`: passed (0)

```text
Requirement already satisfied: pip in ./.agentlab/venv/lib/python3.9/site-packages (21.2.4)
Collecting pip
  Downloading pip-26.0.1-py3-none-any.whl (1.8 MB)
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 21.2.4
    Uninstalling pip-21.2.4:
      Successfully uninstalled pip-21.2.4
Successfully installed pip-26.0.1
```

3. Assertion `python -m pip install -e . "pytest<9"`: passed (0)

```text
.metadata (2.5 kB)
Collecting tomli>=1 (from pytest<9)
  Using cached tomli-2.4.1-py3-none-any.whl.metadata (10 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx==0.28.0)
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting typing-extensions>=4.6.0 (from exceptiongroup>=1->pytest<9)
  Downloading typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Downloading exceptiongroup-1.3.1-py3-none-any.whl (16 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached iniconfig-2.1.0-py3-none-any.whl (6.0 kB)
Using cached packaging-26.2-py3-none-any.whl (100 kB)
Using cached pygments-2.20.0-py3-none-any.whl (1.2 MB)
Using cached tomli-2.4.1-py3-none-any.whl (14 kB)
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached anyio-4.12.1-py3-none-any.whl (113 kB)
Downloading idna-3.13-py3-none-any.whl (68 kB)
Downloading certifi-2026.4.22-py3-none-any.whl (135 kB)
Building wheels for collected packages: httpx
  Building editable for httpx (pyproject.toml): started
  Building editable for httpx (pyproject.toml): finished with status 'done'
  Created wheel for httpx: filename=httpx-0.28.0-py3-none-any.whl size=4920 sha256=d3c18ea2f3c7c8e58cd3926ae873615ef532fc0d6d3afce498b258af0c43c4ca
  Stored in directory: /private/var/folders/3m/s27dbmbs1mn8yp8dmfxmtl9h0000gn/T/pip-ephem-wheel-cache-qp8yljya/wheels/13/25/26/e47a5b65be87600783d7f8d1bf91da51955a10bc9f1f338cf2
Successfully built httpx
Installing collected packages: typing-extensions, tomli, pygments, pluggy, packaging, iniconfig, idna, h11, certifi, httpcore, exceptiongroup, pytest, anyio, httpx

Successfully installed anyio-4.12.1 certifi-2026.4.22 exceptiongroup-1.3.1 h11-0.16.0 httpcore-1.0.9 httpx-0.28.0 idna-3.13 iniconfig-2.1.0 packaging-26.2 pluggy-1.6.0 pygments-2.20.0 pytest-8.4.2 tomli-2.4.1 typing-extensions-4.15.0
```

4. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`: passed (0)
5. Assertion `git apply reference.patch`: passed (0)
6. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`: passed (0)
7. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert="client.pem"); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem",)], calls'`: passed (0)
8. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`: passed (0)
9. Assertion `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=True, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_REQUIRED, ctx.verify_mode; assert ctx.check_hostname is True, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`: passed (0)

## Changed Files

- `httpx/_config.py`
