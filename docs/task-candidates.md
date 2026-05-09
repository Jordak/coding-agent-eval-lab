# Task Candidate Backlog

This file records real-repository task candidates found during early curation so
they do not get lost in chat history. A candidate is not publishable until it has
a pinned start commit, deterministic graders, a reviewed reference artifact, and
passing reference verification.

## Selection Criteria

- Public repository with a clear license and accessible history.
- Small, realistic maintenance task a solo developer can understand.
- Pinned starting commit before the fix.
- Known upstream issue or PR that clarifies intended behavior.
- Deterministic code-based graders that do not require brittle external state.
- Setup cost is acceptable for repeated trials.

## Promoted Tasks

### Datawrapper MCP Docker requirements should include app dependencies

- Status: promoted to `tasks/starter/datawrapper-mcp-docker-requirements-001`
- Repository: <https://github.com/palewire/datawrapper-mcp>
- Issue: <https://github.com/palewire/datawrapper-mcp/issues/19>
- PR: <https://github.com/palewire/datawrapper-mcp/pull/21>
- Start commit: `15b5389e068bf5e673789da82a20f31fe3e81bd7`
- Reference commit inspected: `3de025e419fee021e648786a3a0aa21bfda84527`
- Notes: setup/dependency task where the Dockerfile installs
  `deployment/requirements.txt`, but the deployment manifest drifted from
  `pyproject.toml` and omitted app runtime dependencies. Graders avoid live
  package installation by checking the deterministic deployment manifest
  contract and source imports.

### TodoMVC toggle-all checkbox should work directly

- Status: promoted to `tasks/starter/todomvc-toggle-all-checkbox-001`
- Repository: <https://github.com/tastejs/todomvc>
- Start commit: `ff43b02e59dfa604386bb382034b2cd07c2bcd8a`
- Candidate category: JavaScript frontend behavior / DOM state handling
- Notes: strong starter task because it fixes a visible TodoMVC UI control in a
  public MIT-licensed frontend repo while keeping deterministic graders
  browserless. The task checks the JavaScript ES5 source and checked-in dist
  copies so the toggle-all checkbox receives render state directly, handles its
  own change event, and has a label wired to the input id.

### Click should deduplicate help option construction

- Status: promoted to `tasks/starter/click-help-option-refactor-001`
- Repository: <https://github.com/pallets/click>
- PR: <https://github.com/pallets/click/pull/2563>
- Start commit: `9aeb586cbc622c229bbf80ad948e590f596a8d3e`
- Reference commit inspected: `15644915e482b7c7bd7ee1aa77c9c2dbcd934330`
- Notes: behavior-preserving production-code refactor that extracts shared
  default-help-option construction. Graders assert pre/post CLI help behavior
  and require the shared `HelpOption` extraction so a no-op cannot pass.

### Click should not suggest a shadowed help option

- Status: promoted to `tasks/starter/click-help-shadowed-option-001`
- Repository: <https://github.com/pallets/click>
- Issue: <https://github.com/pallets/click/issues/2790>
- PR: <https://github.com/pallets/click/pull/3208>
- Start commit: `f1f191ecd2c790b161187c78e7c88440e9524e5c`
- Reference commit inspected: `1241abaed4e441582a21f4bf90c8482de02b92df`
- Notes: strong starter task because the bug is user-facing, the target behavior
  is easy to explain, and standalone inline graders can assert the fix without
  copying the upstream pytest test into the starting repo.

### Click default_map should split multi-value string defaults

- Status: promoted to `tasks/starter/click-default-map-nargs-001`
- Repository: <https://github.com/pallets/click>
- Issue: <https://github.com/pallets/click/issues/2745>
- PR: <https://github.com/pallets/click/pull/3364>
- Candidate start commit: `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`
- Candidate reference commit: `3a3e0350b6a2ea3e799440d48e779acabcf44de9`
- Candidate category: Python bugfix / CLI parameter behavior
- Notes: promoted with a trimmed production reference patch focused on
  `src/click/core.py`. Graders assert string splitting for `nargs=2` and tuple
  option types, unchanged single-value string defaults, and explicit CLI
  arguments overriding `default_map`.

### Click should cover should_strip_ansi color and stream behavior

- Status: promoted to `tasks/starter/click-should-strip-ansi-tests-001`
- Repository: <https://github.com/pallets/click>
- PR: <https://github.com/pallets/click/pull/2731>
- Start commit: `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`
- Reference commit inspected: `cf0c36d33734af1de9ecd5d3305970eb26ebba7f`
- Candidate category: Python test-writing / CLI compatibility coverage
- Notes: tests-only starter task. Graders assert the targeted compat test file
  passes, the final diff stays in `tests/test_compat.py`, and the added tests
  structurally exercise color override and stream/Jupyter detection behavior
  without requiring production-code changes.

### HTTPX should keep client certs with verify disabled

- Status: promoted to `tasks/starter/httpx-verify-false-client-cert-001`
- Repository: <https://github.com/encode/httpx>
- Related issue: <https://github.com/encode/httpx/issues/3441>
- PR: <https://github.com/encode/httpx/pull/3442>
- Start commit: `0cb7e5a2e736628e2f506d259fcf0d48cd2bde82`
- Reference commit inspected: `b1c39523ae3b5d6a3b8c3e49b0feca21242db2c9`
- Notes: promoted for the ambiguous product-behavior slice. The prompt asks the
  agent to make a conservative compatibility choice: `verify=False` disables
  server certificate checks but should not skip client-certificate loading.
  Graders assert tuple and single-file cert handling, the no-cert `verify=False`
  path, and the existing `verify=True` with cert path.

## Strong Candidates

### Prettier duplicate dangling comments in experimental ternaries

- Repository: <https://github.com/prettier/prettier>
- Issue: <https://github.com/prettier/prettier/issues/18944>
- PR: <https://github.com/prettier/prettier/pull/18963>
- Candidate start commit: `80a2fdb5e88ce220b88d9122cd74303d71e4d8c0`
- Candidate reference commit inspected: `0bf6a9e01ab18c41d9eef397aed1a9fa95063301`
- Candidate category: JavaScript formatter bugfix
- Why promising: real formatting bug with a concrete before/after output.
- Risks / checks: Prettier setup may be heavier than starter Python tasks; need a
  narrow formatter invocation that avoids full repo setup cost if possible.

### Vite should detect Deno workspace roots

- Repository: <https://github.com/vitejs/vite>
- Issue: <https://github.com/vitejs/vite/issues/22237>
- PR: <https://github.com/vitejs/vite/pull/22238>
- Candidate start commit: `dfc8aa5057dd8ec2b1223980d1e2eeb946ac3384`
- Candidate reference commit: `2ea005e5ec4bf2e5c0f4ed5030d84d713f747fac`
- Candidate category: TypeScript behavior bugfix / monorepo tooling
- Why promising: realistic modern JS tooling issue with focused expected
  behavior.
- Risks / checks: Vite's package manager and test setup may make repeated trials
  expensive. Candidate should be deferred until the lab handles JS/TS setup well.

## Possible Later Candidates

### Express req.acceptsCharsets flexible input formats

- Repository: <https://github.com/expressjs/express>
- PR: <https://github.com/expressjs/express/pull/6088>
- Candidate start commit: `8cb53ea5c3329032a1db47be019b717d8350fb0e`
- Candidate reference commit inspected: `285e19dc3b6c53099f196396ffc7e769fb9555a5`
- Candidate category: JavaScript API behavior
- Why interesting: compact JS library task with behavior and tests.
- Risks / checks: no linked issue was found during initial curation; clarify the
  intended behavior from the PR body and tests before promoting.

### Remotion AudioContext autoplay / muted fixes

- Repository: <https://github.com/remotion-dev/remotion>
- Issues: <https://github.com/remotion-dev/remotion/issues/7236>,
  <https://github.com/remotion-dev/remotion/issues/7238>
- PR: <https://github.com/remotion-dev/remotion/pull/7240>
- Candidate category: TypeScript/media runtime bugfix
- Why interesting: realistic frontend/media runtime task.
- Risks / checks: likely heavier setup and harder deterministic grading. Keep for
  later after the lab supports JS/TS task environments and possibly browser-like
  validation.

## Curation Follow-Ups

- Resolve exact parent/reference commits for any candidate not yet pinned.
- Prototype baseline and target graders before creating task bundles.
- Record setup cost and whether full upstream tests are available to the agent.
- Prefer adding one candidate at a time, with verified reference artifacts and a
  small pilot trial batch before expanding the suite.
