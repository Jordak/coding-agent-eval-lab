# Reference Verification Report: todomvc-toggle-all-checkbox-001

- Trial kind: `reference_verification`
- Agent harness: `reference`
- Evaluation suite: `starter-coding`
- Evaluation type: `regression`
- Reference artifact: patch `reference.patch`
- Status: `passed`
- Outcome: `passed`
- Files changed: `4`
- Lines added: `6`
- Lines deleted: `8`

## Code-Based Graders

1. Assertion `node --version`: passed (0)

```text
v24.5.0
```

2. Assertion `node -e 'const fs=require("fs"),vm=require("vm"),assert=require("assert"); function exercise(path){const elements={".todo-list":{},".todo-count":{},".clear-completed":{},".main":{style:{}},".footer":{style:{}},".toggle-all":{checked:false,click(){this.checked=!this.checked;this.clicked=(this.clicked||0)+1;}},".toggle-all-label":{},".new-todo":{}}; const events=[]; const context={window:{},qs:(selector)=>elements[selector]||{style:{},dataset:{}},qsa:()=>[],$on:(element,type,handler)=>events.push({element,type,handler}),$delegate:()=>{},$parent:()=>({dataset:{id:"1"}})}; context.window=context; vm.createContext(context); vm.runInContext(fs.readFileSync(path,"utf8"),context); const view=new context.app.View({}); view.render("toggleAll",{checked:true}); assert.strictEqual(elements[".toggle-all"].checked,false,path); assert.strictEqual(elements[".toggle-all-label"].checked,true,path); let payload; view.bind("toggleAll",(data)=>{payload=data;}); assert.strictEqual(events.length,1,path); assert.strictEqual(events[0].element,elements[".toggle-all-label"],path); assert.strictEqual(events[0].type,"click",path); events[0].handler.call(elements[".toggle-all-label"]); assert.strictEqual(payload.completed,true,path); assert.strictEqual(elements[".toggle-all"].clicked,1,path);} exercise("examples/javascript-es5/src/view.js"); exercise("examples/javascript-es5/dist/view.js");'`: passed (0)
3. Assertion `node -e 'const fs=require("fs"),assert=require("assert"); for (const path of ["examples/javascript-es5/index.html","examples/javascript-es5/dist/index.html"]){const html=fs.readFileSync(path,"utf8"); const input=html.match(/<input[^>]*class="toggle-all"[^>]*>/); assert(input,path); assert(!/\bid="toggle-all"/.test(input[0]),path); assert(/<label[^>]*class="toggle-all-label"[^>]*for="toggle-all"/.test(html),path);}'`: passed (0)
4. Assertion `git apply reference.patch`: passed (0)
5. Assertion `node -e 'const fs=require("fs"),vm=require("vm"),assert=require("assert"); function exercise(path){const elements={".todo-list":{},".todo-count":{},".clear-completed":{},".main":{style:{}},".footer":{style:{}},".toggle-all":{checked:false,click(){this.clicked=(this.clicked||0)+1;}},".toggle-all-label":{},".new-todo":{}}; const events=[]; const context={window:{},qs:(selector)=>elements[selector]||{style:{},dataset:{}},qsa:()=>[],$on:(element,type,handler)=>events.push({element,type,handler}),$delegate:()=>{},$parent:()=>({dataset:{id:"1"}})}; context.window=context; vm.createContext(context); vm.runInContext(fs.readFileSync(path,"utf8"),context); const view=new context.app.View({}); view.render("toggleAll",{checked:true}); assert.strictEqual(elements[".toggle-all"].checked,true,path); assert.strictEqual(elements[".toggle-all-label"].checked,undefined,path); let payload; view.bind("toggleAll",(data)=>{payload=data;}); assert.strictEqual(events.length,1,path); assert.strictEqual(events[0].element,elements[".toggle-all"],path); assert.strictEqual(events[0].type,"change",path); elements[".toggle-all"].checked=false; events[0].handler.call(elements[".toggle-all"]); assert.strictEqual(payload.completed,false,path); elements[".toggle-all"].checked=true; events[0].handler.call(elements[".toggle-all"]); assert.strictEqual(payload.completed,true,path); assert.strictEqual(elements[".toggle-all"].clicked,undefined,path);} exercise("examples/javascript-es5/src/view.js"); exercise("examples/javascript-es5/dist/view.js");'`: passed (0)
6. Assertion `node -e 'const fs=require("fs"),assert=require("assert"); for (const path of ["examples/javascript-es5/index.html","examples/javascript-es5/dist/index.html"]){const html=fs.readFileSync(path,"utf8"); const input=html.match(/<input[^>]*class="toggle-all"[^>]*>/); assert(input,path); assert(/\bid="toggle-all"/.test(input[0]),path); assert(/<label[^>]*class="toggle-all-label"[^>]*for="toggle-all"/.test(html),path);}'`: passed (0)

## Changed Files

- `examples/javascript-es5/dist/index.html`
- `examples/javascript-es5/dist/view.js`
- `examples/javascript-es5/index.html`
- `examples/javascript-es5/src/view.js`
