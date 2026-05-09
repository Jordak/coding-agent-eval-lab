# Reference Verification Report: react-tabs-selected-focus-overlay-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `3`
- Lines added: `0`
- Lines deleted: `30`

## Code-Based Graders

1. Assertion `python3 -c 'from pathlib import Path; css = Path("style/react-tabs.css").read_text(); scss = Path("style/react-tabs.scss").read_text(); less = Path("style/react-tabs.less").read_text(); assert ".react-tabs__tab:focus:after" in css, css; assert "background: #fff" in css and "bottom: -5px" in css, css; assert "&:after" in scss and "&:after" in less'`: passed (0)
2. Assertion `git apply reference.patch`: passed (0)
3. Assertion `python3 -c 'from pathlib import Path; css = Path("style/react-tabs.css").read_text(); scss = Path("style/react-tabs.scss").read_text(); less = Path("style/react-tabs.less").read_text(); assert ".react-tabs__tab:focus:after" not in css, css; assert "&:after" not in scss, scss; assert "&:after" not in less, less; assert ".react-tabs__tab:focus" in css and "&:focus" in scss and "&:focus" in less; assert ".react-tabs__tab--selected" in css and "&--selected" in scss and "&--selected" in less; assert "border-color: #aaa" in css and "border-color: #aaa" in scss and "border-color: #aaa" in less'`: passed (0)
4. Assertion `git diff --check`: passed (0)

## Changed Files

- `style/react-tabs.css`
- `style/react-tabs.less`
- `style/react-tabs.scss`
