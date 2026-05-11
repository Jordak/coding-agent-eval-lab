# Reference Verification Report: remotion-audio-context-autoplay-muted-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `2`
- Lines added: `30`
- Lines deleted: `15`

## Code-Based Graders

1. Assertion `python3 -c 'from pathlib import Path; playback = Path("packages/player/src/use-playback.ts").read_text(); shared = Path("packages/core/src/audio/shared-audio-tags.tsx").read_text(); assert "sharedAudioContext?.resume?.();" in playback; assert "if (!muted)" not in playback.split("sharedAudioContext?.resume?.();", 1)[0][-80:]; assert "if (getIsResumingAudioContext !== null && !muted)" not in playback; assert "const resumePromise = ctxAndGain.audioContext.resume();" not in shared; assert "return ctxAndGain.audioContext.resume().then(() => {" in shared'`: passed (0)
2. Assertion `git apply reference.patch`: passed (0)
3. Assertion `python3 -c 'from pathlib import Path; import re; playback = Path("packages/player/src/use-playback.ts").read_text(); guarded_resume = re.search(r"if\s*\(\s*!muted\s*\)\s*{\s*sharedAudioContext\?\.resume\?\.\(\);\s*}", playback); assert guarded_resume, "sharedAudioContext.resume() must be guarded by !muted"; unguarded_resume = playback.replace(guarded_resume.group(0), ""); assert "sharedAudioContext?.resume?.();" not in unguarded_resume, "no unguarded sharedAudioContext.resume() calls should remain"; assert re.search(r"if\s*\(\s*getIsResumingAudioContext\s*!==\s*null\s*&&\s*!muted\s*\)", playback), "muted playback must not wait on getIsResumingAudioContext()"; assert "getIsResumingAudioContext.then(" in playback, "non-muted playback should still wait for real audio-context resume work"'`: passed (0)
4. Assertion `python3 -c 'from pathlib import Path; import re; shared = Path("packages/core/src/audio/shared-audio-tags.tsx").read_text(); assert "const resumePromise = ctxAndGain.audioContext.resume();" in shared, "resume() should call AudioContext.resume() once and keep its promise"; assert re.search(r"isResuming\.current\s*=\s*new Promise<void>\(\(resolve\)\s*=>\s*{[\s\S]*?resumePromise\.catch\(\(err\)\s*=>\s*{[\s\S]*?Log\.warn\([\s\S]*?resolve\(\);[\s\S]*?}\);[\s\S]*?}\)\.finally", shared), "resume rejection must resolve the shared resume waiter instead of hanging playback"; assert re.search(r"return\s+resumePromise\s*[\s\S]*?\.then\(\(\)\s*=>\s*{[\s\S]*?nodesToResume\.current\.clear\(\);[\s\S]*?}\)\s*[\s\S]*?\.catch\(\(\)\s*=>\s*{", shared), "resume() must swallow AudioContext.resume() rejection after logging"; assert "return ctxAndGain.audioContext.resume().then" not in shared, "returning the raw resume().then() chain can propagate autoplay-policy rejection"'`: passed (0)
5. Assertion `python3 -c 'import subprocess; changed = subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines(); assert changed == ["packages/core/src/audio/shared-audio-tags.tsx", "packages/player/src/use-playback.ts"], changed'`: passed (0)
6. Assertion `git diff --check`: passed (0)

## Changed Files

- `packages/core/src/audio/shared-audio-tags.tsx`
- `packages/player/src/use-playback.ts`
