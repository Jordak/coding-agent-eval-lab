# Vite should detect Deno workspace roots

- Task ID: `vite-deno-workspace-root-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `typescript`
- Repository: `https://github.com/vitejs/vite.git`
- Commit: `dfc8aa5057dd8ec2b1223980d1e2eeb946ac3384`
- Source: `task.yaml`

## Prompt

Fix Vite's workspace-root search so Deno workspace configs are treated as workspace root markers. When `searchForWorkspaceRoot` is called from a nested package inside a Deno workspace declared by a `workspace` field in `deno.json` or in a valid-JSON `deno.jsonc`, it should return the Deno workspace root instead of the nested package directory. Calling it at the Deno workspace root should also return that root. Keep the existing package-manager workspace behavior intact, keep the patch focused on the server root-search logic and focused root-search tests/fixtures, and avoid full Vite test-suite, browser/e2e, or broad monorepo validation.

## Reference

Add a Deno workspace-root detector in `packages/vite/src/node/server/searchRoot.ts` that checks readable `deno.json` and `deno.jsonc` files, parses them as JSON, and treats a truthy `workspace` field as a workspace root marker. Call that detector from `searchForWorkspaceRoot` alongside existing root-file and package.json workspace checks, and add focused `search-root.spec.ts` coverage plus fixtures for a nested Deno workspace.

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

- `node --version`

### Baseline

- `node -e 'const fs=require("node:fs"),os=require("node:os"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");function write(file,data){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,data)}function fixture(tmp,name,configName){const root=path.join(tmp,name);write(path.join(root,configName),JSON.stringify({workspace:["nested"]}));write(path.join(root,"nested/package.json"),JSON.stringify({private:true}));return root}function load(){let source=fs.readFileSync("packages/vite/src/node/server/searchRoot.ts","utf8").split("\n").filter((line)=>!line.startsWith("import ")).join("\n");source=source.replace(/export function /g,"function ").replace(/\): [A-Za-z][A-Za-z0-9_<>, ]+/g,")").replace(/(\w+): string/g,"$1");const sandbox={fs,dirname:path.dirname,join:path.join,isFileReadable(file){try{fs.accessSync(file,fs.constants.R_OK);return true}catch{return false}},exports:{}};vm.runInNewContext(source+"\nexports.searchForWorkspaceRoot = searchForWorkspaceRoot",sandbox);return sandbox.exports.searchForWorkspaceRoot}const searchForWorkspaceRoot=load(),tmp=fs.mkdtempSync(path.join(os.tmpdir(),"vite-deno-root-baseline-")),denoJsonRoot=fixture(tmp,"deno-json","deno.json");assert.notEqual(searchForWorkspaceRoot(path.join(denoJsonRoot,"nested")),denoJsonRoot);const denoJsoncRoot=fixture(tmp,"deno-jsonc","deno.jsonc");assert.notEqual(searchForWorkspaceRoot(path.join(denoJsoncRoot,"nested")),denoJsoncRoot);const packageWorkspaceRoot=path.join(tmp,"package-workspace");write(path.join(packageWorkspaceRoot,"package.json"),JSON.stringify({workspaces:["nested"]}));write(path.join(packageWorkspaceRoot,"nested/package.json"),JSON.stringify({private:true}));assert.equal(searchForWorkspaceRoot(path.join(packageWorkspaceRoot,"nested")),packageWorkspaceRoot)'`

### Target

- `git add -N -- packages/vite/src/node/server/__tests__/fixtures`
- `git diff --check`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `8`

## Tags

- `bugfix`
- `typescript`
- `vite`
- `monorepo`
- `real-issue`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `dependency_issue`
- `resource_inefficient`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
