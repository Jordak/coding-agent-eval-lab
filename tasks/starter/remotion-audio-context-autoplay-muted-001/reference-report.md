# Reference Verification Report: remotion-audio-context-autoplay-muted-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Task repository: `https://github.com/remotion-dev/remotion.git`
- Task commit: `631ce3d2ab757e44cfb542a108a21f1e9a9c6c0f`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `2`
- Lines added: `30`
- Lines deleted: `15`

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
- Workspace history policy: `focused_substitute`
- Workspace base ref: `focused-two-file-validation`

## Public Graders

1. Assertion `python3 -c 'from pathlib import Path; playback = Path("packages/player/src/use-playback.ts").read_text(); shared = Path("packages/core/src/audio/shared-audio-tags.tsx").read_text(); assert "sharedAudioContext?.resume?.();" in playback; assert "if (!muted)" not in playback.split("sharedAudioContext?.resume?.();", 1)[0][-80:]; assert "if (getIsResumingAudioContext !== null && !muted)" not in playback; assert "const resumePromise = ctxAndGain.audioContext.resume();" not in shared; assert "return ctxAndGain.audioContext.resume().then(() => {" in shared'`: passed (0)
2. Assertion `git apply reference.patch`: passed (0)
3. Assertion `git diff --check`: passed (0)

## Hidden Verifier

- Patch: `verifier.patch`

1. Assertion `git apply hidden verifier patch: verifier.patch`: passed (0)
2. Assertion `python3 .agentlab_hidden/check_behavior.py`: passed (0)

```text
check: assert_playback
check: assert_shared_audio
check: assert_changed_files
```


## Grader Notes

- Remotion full verify-reference was attempted twice and interrupted during large-repo synthetic-base materialization; this reference artifact was regenerated from the focused two-file validation workspace /private/tmp/ael-remotion-mini-123-fix2 using the same reference patch, hidden verifier patch, and public git diff --check command.

## Changed Files

- `packages/core/src/audio/shared-audio-tags.tsx`
- `packages/player/src/use-playback.ts`
