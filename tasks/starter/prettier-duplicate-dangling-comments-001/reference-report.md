# Reference Verification Report: prettier-duplicate-dangling-comments-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `1`
- Lines added: `0`
- Lines deleted: `18`

## Code-Based Graders

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
➤ YN0000: └ Completed in 2s 405ms
➤ YN0000: · Done with warnings in 2s 658ms
```

2. Assertion `node -e 'const prettier = require("./src/index.cjs"); (async () => { const input = `condition ? ifTrue\n: [\n      // Hello, world!\n  ]\n`; const output = await prettier.format(input, { parser: "babel", tabWidth: 4, semi: false, experimentalTernaries: true }); const count = (output.match(/Hello, world!/g) || []).length; if (count !== 2) { console.error(output); throw new Error(`expected start commit to duplicate the comment twice, saw ${count}`); } })().catch((error) => { console.error(error); process.exit(1); })'`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `node -e 'const prettier = require("./src/index.cjs"); (async () => { const cases = [`condition ? ifTrue\n: [\n      // Hello, world!\n  ]\n`, `condition ? [\n      // Hello, world!\n  ]\n: ifFalse\n`, `condition ? ifTrue\n: {\n      // Hello, world!\n  }\n`, `condition ? {\n    // Hello, world!\n  }\n: ifFalse\n`, `condition ? ifTrue\n: [\n      // Hello, world!\n    1,\n  ]\n`]; for (const input of cases) { const output = await prettier.format(input, { parser: "babel", tabWidth: 4, semi: false, experimentalTernaries: true }); const count = (output.match(/Hello, world!/g) || []).length; if (count !== 1) { console.error(output); throw new Error(`expected exactly one preserved comment, saw ${count}`); } } })().catch((error) => { console.error(error); process.exit(1); })'`: passed (0)
5. Assertion `git diff --check`: passed (0)

## Changed Files

- `src/language-js/print/ternary.js`
