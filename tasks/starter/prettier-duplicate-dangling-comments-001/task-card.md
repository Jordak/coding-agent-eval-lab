# Prettier should not duplicate dangling comments in experimental ternaries

- Task ID: `prettier-duplicate-dangling-comments-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `javascript`
- Repository: `https://github.com/prettier/prettier.git`
- Commit: `80a2fdb5e88ce220b88d9122cd74303d71e4d8c0`
- Source: `task.yaml`

## Prompt

Fix Prettier's JavaScript formatter so `experimentalTernaries` no longer prints a dangling comment twice when an empty array or object appears in a ternary branch. For example, formatting `condition ? ifTrue : [ // comment ]` with the Babel parser, `--experimental-ternaries`, `--tab-width 4`, and `--no-semi` should preserve the comment exactly once rather than also placing it after the consequent. Preserve the existing formatter behavior for the affected empty array/object consequent and alternate branches.

## Reference

In the JavaScript ternary printer, stop separately printing dangling comments from the consequent and alternate branch nodes before printing those branch documents. Those branch printers already own their dangling comments, so the extra collection in `printTernary` causes the duplicate output under `experimentalTernaries`. A focused solution updates `src/language-js/print/ternary.js` without broad parser or CLI changes.

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

- `corepack yarn install --immutable --mode=skip-build`

### Baseline

- `node -e 'const prettier = require("./src/index.cjs"); (async () => { const input = `condition ? ifTrue\n: [\n      // Hello, world!\n  ]\n`; const output = await prettier.format(input, { parser: "babel", tabWidth: 4, semi: false, experimentalTernaries: true }); const count = (output.match(/Hello, world!/g) || []).length; if (count !== 2) { console.error(output); throw new Error(`expected start commit to duplicate the comment twice, saw ${count}`); } })().catch((error) => { console.error(error); process.exit(1); })'`

### Target

- `git diff --check`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `3`

## Tags

- `bugfix`
- `javascript`
- `prettier`
- `formatter`
- `comments`
- `real-issue`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `resource_inefficient`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
