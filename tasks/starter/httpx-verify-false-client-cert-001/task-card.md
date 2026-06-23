# HTTPX should keep client certs with verify disabled

- Task ID: `httpx-verify-false-client-cert-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `python`
- Repository: `https://github.com/encode/httpx.git`
- Commit: `0cb7e5a2e736628e2f506d259fcf0d48cd2bde82`
- Source: `task.yaml`

## Prompt

A user doing a local mTLS smoke test reports that HTTPX behaves oddly when they pass both verify=False and a client certificate. They are intentionally skipping server certificate verification for a local or self-signed endpoint, but they still expect the client certificate to be configured. Make the conservative compatibility choice: verify=False should disable server certificate checks only, not ignore client-side certs. Keep the existing verify=True with cert behavior and verify=False without cert behavior intact. This v1 task is non-interactive, so proceed with that assumption and keep the patch focused.

## Reference

In create_ssl_context, make the verify=False branch assign the unverified SSL context to the same ctx variable used by the other branches, then allow the existing cert-loading block to run before returning the context. Human review should accept a focused patch that preserves verify=False as CERT_NONE/check_hostname=False, loads string and tuple client certificates through the existing cert path, and does not broaden unrelated SSL or request behavior.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

- PATH prepends: `.agentlab/venv/bin`
- PYTEST_ADDOPTS=-p no:cacheprovider
- PYTHONDONTWRITEBYTECODE=1
- VIRTUAL_ENV={workspace}/.agentlab/venv

## Visible Validation

- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`
- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert="client.pem"); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem",)], calls'`
- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`
- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=True, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_REQUIRED, ctx.verify_mode; assert ctx.check_hostname is True, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`

## Graders

### Setup

- `python3 -m venv .agentlab/venv`
- `python -m pip install --upgrade pip`
- `python -m pip install -e . "pytest<9"`

### Baseline

- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`

### Target

- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`
- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False, cert="client.pem"); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [("client.pem",)], calls'`
- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=False); assert ctx.verify_mode == ssl.CERT_NONE, ctx.verify_mode; assert ctx.check_hostname is False, ctx.check_hostname; assert calls == [], calls'`
- `python -c 'import ssl, httpx; calls = []; ssl.SSLContext.load_cert_chain = lambda self, *args, **kwargs: calls.append(args); ctx = httpx.create_ssl_context(verify=True, cert=("client.pem", "client.key")); assert ctx.verify_mode == ssl.CERT_REQUIRED, ctx.verify_mode; assert ctx.check_hostname is True, ctx.check_hostname; assert calls == [("client.pem", "client.key")], calls'`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `2`

## Tags

- `bugfix`
- `python`
- `ssl`
- `client-cert`
- `ambiguous-behavior`
- `real-pr`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `resource_inefficient`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
