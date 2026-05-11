# Reference Verification Report: vite-deno-workspace-root-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `5`
- Lines added: `39`
- Lines deleted: `0`

## Code-Based Graders

1. Assertion `node --version`: passed (0)

```text
v24.5.0
```

2. Assertion `node -e 'const fs=require("node:fs"),os=require("node:os"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");function write(file,data){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,data)}function fixture(tmp,name,configName){const root=path.join(tmp,name);write(path.join(root,configName),JSON.stringify({workspace:["nested"]}));write(path.join(root,"nested/package.json"),JSON.stringify({private:true}));return root}function load(){let source=fs.readFileSync("packages/vite/src/node/server/searchRoot.ts","utf8").split("\n").filter((line)=>!line.startsWith("import ")).join("\n");source=source.replace(/export function /g,"function ").replace(/\): [A-Za-z][A-Za-z0-9_<>, ]+/g,")").replace(/(\w+): string/g,"$1");const sandbox={fs,dirname:path.dirname,join:path.join,isFileReadable(file){try{fs.accessSync(file,fs.constants.R_OK);return true}catch{return false}},exports:{}};vm.runInNewContext(source+"\nexports.searchForWorkspaceRoot = searchForWorkspaceRoot",sandbox);return sandbox.exports.searchForWorkspaceRoot}const searchForWorkspaceRoot=load(),tmp=fs.mkdtempSync(path.join(os.tmpdir(),"vite-deno-root-baseline-")),denoJsonRoot=fixture(tmp,"deno-json","deno.json");assert.notEqual(searchForWorkspaceRoot(path.join(denoJsonRoot,"nested")),denoJsonRoot);const denoJsoncRoot=fixture(tmp,"deno-jsonc","deno.jsonc");assert.notEqual(searchForWorkspaceRoot(path.join(denoJsoncRoot,"nested")),denoJsoncRoot);const packageWorkspaceRoot=path.join(tmp,"package-workspace");write(path.join(packageWorkspaceRoot,"package.json"),JSON.stringify({workspaces:["nested"]}));write(path.join(packageWorkspaceRoot,"nested/package.json"),JSON.stringify({private:true}));assert.equal(searchForWorkspaceRoot(path.join(packageWorkspaceRoot,"nested")),packageWorkspaceRoot)'`: passed (0)
3. Assertion `git apply reference.patch`: passed (0)
4. Assertion `node -e 'const fs=require("node:fs"),os=require("node:os"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");function write(file,data){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,data)}function fixture(tmp,name,configName){const root=path.join(tmp,name);write(path.join(root,configName),JSON.stringify({workspace:["nested"]}));write(path.join(root,"nested/package.json"),JSON.stringify({private:true}));return root}function load(){let source=fs.readFileSync("packages/vite/src/node/server/searchRoot.ts","utf8").split("\n").filter((line)=>!line.startsWith("import ")).join("\n");source=source.replace(/export function /g,"function ").replace(/\): [A-Za-z][A-Za-z0-9_<>, ]+/g,")").replace(/(\w+): string/g,"$1");const sandbox={fs,dirname:path.dirname,join:path.join,isFileReadable(file){try{fs.accessSync(file,fs.constants.R_OK);return true}catch{return false}},exports:{}};vm.runInNewContext(source+"\nexports.searchForWorkspaceRoot = searchForWorkspaceRoot",sandbox);return sandbox.exports.searchForWorkspaceRoot}const searchForWorkspaceRoot=load(),tmp=fs.mkdtempSync(path.join(os.tmpdir(),"vite-deno-root-test-")),denoJsonRoot=fixture(tmp,"deno-json","deno.json");assert.equal(searchForWorkspaceRoot(path.join(denoJsonRoot,"nested")),denoJsonRoot);assert.equal(searchForWorkspaceRoot(denoJsonRoot),denoJsonRoot);const denoJsoncRoot=fixture(tmp,"deno-jsonc","deno.jsonc");assert.equal(searchForWorkspaceRoot(path.join(denoJsoncRoot,"nested")),denoJsoncRoot);assert.equal(searchForWorkspaceRoot(denoJsoncRoot),denoJsoncRoot);const packageWorkspaceRoot=path.join(tmp,"package-workspace");write(path.join(packageWorkspaceRoot,"package.json"),JSON.stringify({workspaces:["nested"]}));write(path.join(packageWorkspaceRoot,"nested/package.json"),JSON.stringify({private:true}));assert.equal(searchForWorkspaceRoot(path.join(packageWorkspaceRoot,"nested")),packageWorkspaceRoot)'`: passed (0)
5. Assertion `node -e 'const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");const specPath="packages/vite/src/node/server/__tests__/search-root.spec.ts",dirname=path.dirname(specPath),spec=fs.readFileSync(specPath,"utf8");function load(){let source=fs.readFileSync("packages/vite/src/node/server/searchRoot.ts","utf8").split("\n").filter((line)=>!line.startsWith("import ")).join("\n");source=source.replace(/export function /g,"function ").replace(/\): [A-Za-z][A-Za-z0-9_<>, ]+/g,")").replace(/(\w+): string/g,"$1");const sandbox={fs,dirname:path.dirname,join:path.join,isFileReadable(file){try{fs.accessSync(file,fs.constants.R_OK);return true}catch{return false}},exports:{}};vm.runInNewContext(source+"\nexports.searchForWorkspaceRoot = searchForWorkspaceRoot",sandbox);return sandbox.exports.searchForWorkspaceRoot}const searchForWorkspaceRoot=load(),q=String.fromCharCode(39),pattern=new RegExp("searchForWorkspaceRoot\\(\\s*resolve\\(dirname, "+q+"([^"+q+"]+)"+q+"\\)[\\s\\S]*?expect\\(resolved\\)\\.toBe\\(resolve\\(dirname, "+q+"([^"+q+"]+)"+q+"\\)\\)","g"),matches=[...spec.matchAll(pattern)];assert(matches.length>=5,"expected focused search-root.spec.ts cases");for(const match of matches){const input=path.resolve(dirname,match[1]),expected=path.resolve(dirname,match[2]);assert(fs.existsSync(input),`missing fixture path referenced by search-root.spec.ts: ${match[1]}`);assert(fs.existsSync(expected),`missing expected fixture path referenced by search-root.spec.ts: ${match[2]}`);assert.equal(searchForWorkspaceRoot(input),expected,`search-root.spec.ts expectation failed for ${match[1]}`)}'`: passed (0)
6. Assertion `git add -N -- packages/vite/src/node/server/__tests__/fixtures`: passed (0)
7. Assertion `git diff --check`: passed (0)

## Changed Files

- `packages/vite/src/node/server/__tests__/fixtures/deno/deno.json`
- `packages/vite/src/node/server/__tests__/fixtures/deno/nested/package.json`
- `packages/vite/src/node/server/__tests__/search-root.spec.ts`
- `packages/vite/src/node/server/searchRoot.ts`
- `pnpm-lock.yaml`
