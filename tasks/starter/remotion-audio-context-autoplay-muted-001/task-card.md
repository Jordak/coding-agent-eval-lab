# Remotion Player muted playback should not wait on AudioContext resume

- Task ID: `remotion-audio-context-autoplay-muted-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `typescript`
- Repository: `https://github.com/remotion-dev/remotion.git`
- Commit: `631ce3d2ab757e44cfb542a108a21f1e9a9c6c0f`
- Source: `task.yaml`

## Prompt

Fix Remotion Player playback so muted playback, including playback whose effective volume is zero, does not resume or wait for the shared Web Audio context before advancing frames. Also make shared AudioContext resume failures from browser autoplay/audio policy non-blocking: if `AudioContext.resume()` rejects, playback should continue without hanging or producing an unhandled promise rejection. Keep the patch focused on `packages/core/src/audio/shared-audio-tags.tsx` and `packages/player/src/use-playback.ts`; do not run the full Remotion monorepo test suite or browser/e2e tests for this task.

## Reference

In `shared-audio-tags.tsx`, store the AudioContext resume promise, resolve the shared `isResuming` waiter if that promise rejects, log the failure, and swallow the returned rejection because playback callers do not await it. In `use-playback.ts`, only call `sharedAudioContext.resume()` and wait on `getIsResumingAudioContext()` when playback is not muted, so muted or volume-zero playback can keep advancing frames without shared audio-context resume work.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

No task-local environment configured.

## Hidden Verifier

- Patch: `verifier.patch`
- Commands: `1 command configured`

## Graders

### Setup

None configured.

### Baseline

- `python3 -c 'from pathlib import Path; playback = Path("packages/player/src/use-playback.ts").read_text(); shared = Path("packages/core/src/audio/shared-audio-tags.tsx").read_text(); assert "sharedAudioContext?.resume?.();" in playback; assert "if (!muted)" not in playback.split("sharedAudioContext?.resume?.();", 1)[0][-80:]; assert "if (getIsResumingAudioContext !== null && !muted)" not in playback; assert "const resumePromise = ctxAndGain.audioContext.resume();" not in shared; assert "return ctxAndGain.audioContext.resume().then(() => {" in shared'`

### Target

- `git diff --check`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `2`

## Tags

- `bugfix`
- `typescript`
- `remotion`
- `web-audio`
- `autoplay`
- `media-runtime`
- `real-issue`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `resource_inefficient`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
