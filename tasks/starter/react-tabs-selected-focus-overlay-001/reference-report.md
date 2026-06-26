# Reference Verification Report: react-tabs-selected-focus-overlay-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Task repository: `https://github.com/reactjs/react-tabs.git`
- Task commit: `186631aca0458e0b991c94180bc3a4a785151c04`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `3`
- Lines added: `0`
- Lines deleted: `30`

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
- Workspace base ref: `6988e9a8967cac275d083850c99ea400719f0054`

## Public Graders

1. Assertion `python3 -c 'from pathlib import Path; css = Path("style/react-tabs.css").read_text(); scss = Path("style/react-tabs.scss").read_text(); less = Path("style/react-tabs.less").read_text(); assert ".react-tabs__tab:focus:after" in css, css; assert "background: #fff" in css and "bottom: -5px" in css, css; assert "&:after" in scss and "&:after" in less'`: passed (0)
2. Assertion `git apply reference.patch`: passed (0)
3. Assertion `git diff --check`: passed (0)

## Hidden Verifier

- Patch: `verifier.patch`

1. Assertion `git apply hidden verifier patch: verifier.patch`: passed (0)
2. Assertion `python3 .agentlab_hidden/check_behavior.py`: passed (0)

```text
$ python3 -c 'from pathlib import Path; css = Path("style/react-tabs.css").read_text(); scss = Path("style/react-tabs.scss").read_text(); less = Path("style/react-tabs.less").read_text(); assert ".react-tabs__tab:focus:after" not in css, css; assert "&:after" not in scss, scss; assert "&:after" not in less, less; assert ".react-tabs__tab:focus" in css and "&:focus" in scss and "&:focus" in less; assert ".react-tabs__tab--selected" in css and "&--selected" in scss and "&--selected" in less; assert "border-color: #aaa" in css and "border-color: #aaa" in scss and "border-color: #aaa" in less'
```


## Changed Files

- `style/react-tabs.css`
- `style/react-tabs.less`
- `style/react-tabs.scss`
