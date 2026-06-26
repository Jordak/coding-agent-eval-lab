# Reference Verification Report: prettier-duplicate-dangling-comments-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Task repository: `https://github.com/prettier/prettier.git`
- Task commit: `80a2fdb5e88ce220b88d9122cd74303d71e4d8c0`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `0`
- Lines deleted: `18`

Setup-created untracked coverage caveat: 31106 setup-created untracked paths existed outside exact boundary-pattern matching. Changed-file counts/lists and boundary metrics include detected changes, but detection remains best-effort for worktree-only content-preserving edits to those paths.

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
- Workspace base ref: `d2c78eaaf1ba3b0cd4a12438feb22f5c9ae2ef98`

## Public Graders

1. Assertion `corepack yarn install --immutable --mode=skip-build`: passed (0)

```text
➤ YN0000: · Yarn 4.12.0
➤ YN0000: ┌ Resolution step
➤ YN0000: └ Completed
➤ YN0000: ┌ Post-resolution validation
➤ YN0002: │ prettier@workspace:. doesn't provide rollup (pd38a67), requested by rollup-plugin-license.
➤ YN0086: │ Some peer dependencies are incorrectly met by your project; run yarn explain peer-requirements <hash> for details, where <hash> is the six-letter p-prefixed code.
➤ YN0086: │ Some peer dependencies are incorrectly met by dependencies; run yarn explain peer-requirements for details.
➤ YN0000: └ Completed
➤ YN0000: ┌ Fetch step
➤ YN0000: └ Completed
➤ YN0000: ┌ Link step
➤ YN0000: └ Completed in 2s 317ms
➤ YN0000: · Done with warnings in 2s 544ms
```

2. Assertion `node -e 'const prettier = require("./src/index.cjs"); (async () => { const input = `condition ? ifTrue\n: [\n      // Hello, world!\n  ]\n`; const output = await prettier.format(input, { parser: "babel", tabWidth: 4, semi: false, experimentalTernaries: true }); const count = (output.match(/Hello, world!/g) || []).length; if (count !== 2) { console.error(output); throw new Error(`expected start commit to duplicate the comment twice, saw ${count}`); } })().catch((error) => { console.error(error); process.exit(1); })'`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `git diff --check`: passed (0)

## Hidden Verifier

- Patch: `verifier.patch`

1. Assertion `git apply hidden verifier patch: verifier.patch`: passed (0)
2. Assertion `python3 .agentlab_hidden/check_behavior.py`: passed (0)

```text
$ node -e 'const prettier = require("./src/index.cjs"); (async () => { const cases = [`condition ? ifTrue\n: [\n      // Hello, world!\n  ]\n`, `condition ? [\n      // Hello, world!\n  ]\n: ifFalse\n`, `condition ? ifTrue\n: {\n      // Hello, world!\n  }\n`, `condition ? {\n    // Hello, world!\n  }\n: ifFalse\n`, `condition ? ifTrue\n: [\n      // Hello, world!\n    1,\n  ]\n`]; for (const input of cases) { const output = await prettier.format(input, { parser: "babel", tabWidth: 4, semi: false, experimentalTernaries: true }); const count = (output.match(/Hello, world!/g) || []).length; if (count !== 1) { console.error(output); throw new Error(`expected exactly one preserved comment, saw ${count}`); } } })().catch((error) => { console.error(error); process.exit(1); })'
```


## Changed Files

- `src/language-js/print/ternary.js`
