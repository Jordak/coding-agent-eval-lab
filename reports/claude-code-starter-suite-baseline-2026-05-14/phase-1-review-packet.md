# Claude Code Phase 1 Review Packet

Date: 2026-05-14

Scope: GitHub issue #52, the Phase 1 full-suite shakedown for the Claude Code
baseline in #49.

## Summary

Phase 1 ran one sequential Claude Code smoke trial for each of the 12 Solo Dev
Starter Suite tasks using the readiness configuration from #51.

- Trials run: `12`
- Valid trials identified: `12`
- Passed graders: `11`
- Failed graders: `1`
- Invalid/excluded trials: `0`
- Requested model: `claude-haiku-4-5-20251001`
- Runtime model source: Claude Code events
- Total reported cost: `$3.2351017`
- Total reported non-cached tokens: `156131`
- Total reported cached input tokens: `19661357`
- Total reported wall time: `1520.908` seconds

The single failed trial is preserved as capability evidence. It was not rerun.
The failure appears fair: setup and pytest passed, but the target structural
grader rejected the shape of the added test.

## Command Shape

Each task used:

```bash
python3 -m agentlab task smoke-test \
  --task tasks/starter/<task-id> \
  --agent claude \
  --claude-model claude-haiku-4-5-20251001 \
  --claude-permission-mode acceptEdits \
  --claude-output-format stream-json \
  --claude-timeout-seconds 1800
```

No `--claude-max-turns` flag was passed. The adapter passed
`--no-session-persistence`, used `stream-json`, and added `--verbose` for Claude
Code print-mode streaming.

## Review Table

| Task | Preliminary outcome | Runtime | Cost | Tokens | Patch | Artifacts |
| --- | --- | ---: | ---: | ---: | --- | --- |
| [datawrapper-mcp-docker-requirements-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/datawrapper-mcp-docker-requirements-001/task-card.md>) | passed, valid | 47s | `$0.1013462` | 4,856 | 1 file, +5/-2 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120001-datawrapper-mcp-docker-requirements-001-claude-59b21ded/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120001-datawrapper-mcp-docker-requirements-001-claude-59b21ded/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120001-datawrapper-mcp-docker-requirements-001-claude-59b21ded/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120001-datawrapper-mcp-docker-requirements-001-claude-59b21ded/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120001-datawrapper-mcp-docker-requirements-001-claude-59b21ded/result.json>) |
| [2048-advanced-snake-params-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/2048-advanced-snake-params-001/task-card.md>) | passed, valid | 80s | `$0.15655615` | 8,492 | 2 files, +6/-6 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120114-2048-advanced-snake-params-001-claude-b6c4cb95/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120114-2048-advanced-snake-params-001-claude-b6c4cb95/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120114-2048-advanced-snake-params-001-claude-b6c4cb95/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120114-2048-advanced-snake-params-001-claude-b6c4cb95/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120114-2048-advanced-snake-params-001-claude-b6c4cb95/result.json>) |
| [click-default-map-nargs-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/click-default-map-nargs-001/task-card.md>) | passed, valid | 225s | `$0.44235895` | 18,796 | 1 file, +12/-0 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120240-click-default-map-nargs-001-claude-54de5b71/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120240-click-default-map-nargs-001-claude-54de5b71/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120240-click-default-map-nargs-001-claude-54de5b71/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120240-click-default-map-nargs-001-claude-54de5b71/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120240-click-default-map-nargs-001-claude-54de5b71/result.json>) |
| [click-help-option-refactor-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/click-help-option-refactor-001/task-card.md>) | passed, valid | 158s | `$0.38072035` | 16,574 | 3 files, +33/-28 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120634-click-help-option-refactor-001-claude-c4f69f39/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120634-click-help-option-refactor-001-claude-c4f69f39/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120634-click-help-option-refactor-001-claude-c4f69f39/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120634-click-help-option-refactor-001-claude-c4f69f39/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120634-click-help-option-refactor-001-claude-c4f69f39/result.json>) |
| [click-help-shadowed-option-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/click-help-shadowed-option-001/task-card.md>) | passed, valid | 218s | `$0.5106382` | 19,988 | 2 files, +47/-8 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120920-click-help-shadowed-option-001-claude-5566808c/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120920-click-help-shadowed-option-001-claude-5566808c/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120920-click-help-shadowed-option-001-claude-5566808c/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120920-click-help-shadowed-option-001-claude-5566808c/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-120920-click-help-shadowed-option-001-claude-5566808c/result.json>) |
| [click-should-strip-ansi-tests-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/click-should-strip-ansi-tests-001/task-card.md>) | failed, valid | 83s | `$0.17350745` | 11,711 | 1 file, +57/-1 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121306-click-should-strip-ansi-tests-001-claude-a63f2827/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121306-click-should-strip-ansi-tests-001-claude-a63f2827/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121306-click-should-strip-ansi-tests-001-claude-a63f2827/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121306-click-should-strip-ansi-tests-001-claude-a63f2827/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121306-click-should-strip-ansi-tests-001-claude-a63f2827/result.json>) |
| [httpx-verify-false-client-cert-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/httpx-verify-false-client-cert-001/task-card.md>) | passed, valid | 96s | `$0.19463375` | 10,220 | 1 file, +6/-6 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121440-httpx-verify-false-client-cert-001-claude-044965c1/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121440-httpx-verify-false-client-cert-001-claude-044965c1/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121440-httpx-verify-false-client-cert-001-claude-044965c1/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121440-httpx-verify-false-client-cert-001-claude-044965c1/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121440-httpx-verify-false-client-cert-001-claude-044965c1/result.json>) |
| [prettier-duplicate-dangling-comments-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/prettier-duplicate-dangling-comments-001/task-card.md>) | passed, valid | 200s | `$0.35947635` | 18,748 | 1 file, +6/-0 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121636-prettier-duplicate-dangling-comments-001-claude-5694847a/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121636-prettier-duplicate-dangling-comments-001-claude-5694847a/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121636-prettier-duplicate-dangling-comments-001-claude-5694847a/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121636-prettier-duplicate-dangling-comments-001-claude-5694847a/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-121636-prettier-duplicate-dangling-comments-001-claude-5694847a/result.json>) |
| [react-tabs-selected-focus-overlay-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/react-tabs-selected-focus-overlay-001/task-card.md>) | passed, valid | 40s | `$0.0820727` | 4,993 | 3 files, +0/-30 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122010-react-tabs-selected-focus-overlay-001-claude-1c53c8cd/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122010-react-tabs-selected-focus-overlay-001-claude-1c53c8cd/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122010-react-tabs-selected-focus-overlay-001-claude-1c53c8cd/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122010-react-tabs-selected-focus-overlay-001-claude-1c53c8cd/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122010-react-tabs-selected-focus-overlay-001-claude-1c53c8cd/result.json>) |
| [remotion-audio-context-autoplay-muted-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/remotion-audio-context-autoplay-muted-001/task-card.md>) | passed, valid | 131s | `$0.2694114` | 16,941 | 2 files, +27/-16 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122258-remotion-audio-context-autoplay-muted-001-claude-1fc7a864/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122258-remotion-audio-context-autoplay-muted-001-claude-1fc7a864/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122258-remotion-audio-context-autoplay-muted-001-claude-1fc7a864/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122258-remotion-audio-context-autoplay-muted-001-claude-1fc7a864/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122258-remotion-audio-context-autoplay-muted-001-claude-1fc7a864/result.json>) |
| [todomvc-toggle-all-checkbox-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/todomvc-toggle-all-checkbox-001/task-card.md>) | passed, valid | 119s | `$0.27802275` | 12,589 | 4 files, +8/-10 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122653-todomvc-toggle-all-checkbox-001-claude-dfe6d568/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122653-todomvc-toggle-all-checkbox-001-claude-dfe6d568/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122653-todomvc-toggle-all-checkbox-001-claude-dfe6d568/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122653-todomvc-toggle-all-checkbox-001-claude-dfe6d568/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122653-todomvc-toggle-all-checkbox-001-claude-dfe6d568/result.json>) |
| [vite-deno-workspace-root-001](</Users/jordanharry/Documents/Agent Eval Lab/tasks/starter/vite-deno-workspace-root-001/task-card.md>) | passed, valid | 119s | `$0.28635745` | 12,223 | 6 files, +53/-0 | [report](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122902-vite-deno-workspace-root-001-claude-867ec512/report.md>) [diff](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122902-vite-deno-workspace-root-001-claude-867ec512/diff.patch>) [transcript](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122902-vite-deno-workspace-root-001-claude-867ec512/transcript.md>) [events](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122902-vite-deno-workspace-root-001-claude-867ec512/claude-events.jsonl>) [result](</Users/jordanharry/Documents/Agent Eval Lab/runs/20260514-122902-vite-deno-workspace-root-001-claude-867ec512/result.json>) |

## Human Review Notes

Review all 12 first fair trials before Phase 2. Suggested starting points:

- `click-should-strip-ansi-tests-001`: only failed grader. Pytest passed, but
  the structural grader failed. The patch calls the imported
  `should_strip_ansi(...)` directly; the task's structural grader expects an
  attribute-style `should_strip_ansi` call shape and other exact test coverage
  signals.
- `click-help-shadowed-option-001`: highest reported cost and token usage in
  Phase 1.
- `vite-deno-workspace-root-001`: largest patch by changed file count.

No invalid trials were found in this Phase 1 pass, so no exclusion review files
were written.
