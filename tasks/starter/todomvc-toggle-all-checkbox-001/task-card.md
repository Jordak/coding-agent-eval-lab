# TodoMVC toggle-all checkbox should work directly

- Task ID: `todomvc-toggle-all-checkbox-001`
- Suite: `starter-coding`
- Evaluation type: `regression`
- Language: `javascript`
- Repository: `https://github.com/tastejs/todomvc.git`
- Commit: `ff43b02e59dfa604386bb382034b2cd07c2bcd8a`
- Source: `task.yaml`

## Prompt

Fix the JavaScript ES5 TodoMVC toggle-all control so the checkbox itself and its label both update all todos correctly. In examples/javascript-es5, the label's for attribute should point to the checkbox, rendering should keep the checkbox input's checked state in sync, and the view should listen for the checkbox's own state change instead of relying on a label click that manually clicks the input. Keep the src and dist copies consistent, avoid double-toggling the checkbox, and run the relevant checks.

## Reference

Add id="toggle-all" to the JavaScript ES5 toggle-all checkbox in both index.html files. In both View implementations, render the toggle-all checked state onto self.$toggleAllInput and bind toggleAll to the checkbox input's change event, passing the input's checked state without manually clicking it.

## Reference Artifact

- Type: `patch`
- Path: `reference.patch`
- Status: `present`

## Environment

No task-local environment configured.

## Visible Validation

- `node -e 'const fs=require("fs"),vm=require("vm"),assert=require("assert"); function exercise(path){const elements={".todo-list":{},".todo-count":{},".clear-completed":{},".main":{style:{}},".footer":{style:{}},".toggle-all":{checked:false,click(){this.clicked=(this.clicked||0)+1;}},".toggle-all-label":{},".new-todo":{}}; const events=[]; const context={window:{},qs:(selector)=>elements[selector]||{style:{},dataset:{}},qsa:()=>[],$on:(element,type,handler)=>events.push({element,type,handler}),$delegate:()=>{},$parent:()=>({dataset:{id:"1"}})}; context.window=context; vm.createContext(context); vm.runInContext(fs.readFileSync(path,"utf8"),context); const view=new context.app.View({}); view.render("toggleAll",{checked:true}); assert.strictEqual(elements[".toggle-all"].checked,true,path); assert.strictEqual(elements[".toggle-all-label"].checked,undefined,path); let payload; view.bind("toggleAll",(data)=>{payload=data;}); assert.strictEqual(events.length,1,path); assert.strictEqual(events[0].element,elements[".toggle-all"],path); assert.strictEqual(events[0].type,"change",path); elements[".toggle-all"].checked=false; events[0].handler.call(elements[".toggle-all"]); assert.strictEqual(payload.completed,false,path); elements[".toggle-all"].checked=true; events[0].handler.call(elements[".toggle-all"]); assert.strictEqual(payload.completed,true,path); assert.strictEqual(elements[".toggle-all"].clicked,undefined,path);} exercise("examples/javascript-es5/src/view.js"); exercise("examples/javascript-es5/dist/view.js");'`
- `node -e 'const fs=require("fs"),assert=require("assert"); for (const path of ["examples/javascript-es5/index.html","examples/javascript-es5/dist/index.html"]){const html=fs.readFileSync(path,"utf8"); const input=html.match(/<input[^>]*class="toggle-all"[^>]*>/); assert(input,path); assert(/\bid="toggle-all"/.test(input[0]),path); assert(/<label[^>]*class="toggle-all-label"[^>]*for="toggle-all"/.test(html),path);}'`

## Graders

### Setup

- `node --version`

### Baseline

- `node -e 'const fs=require("fs"),vm=require("vm"),assert=require("assert"); function exercise(path){const elements={".todo-list":{},".todo-count":{},".clear-completed":{},".main":{style:{}},".footer":{style:{}},".toggle-all":{checked:false,click(){this.checked=!this.checked;this.clicked=(this.clicked||0)+1;}},".toggle-all-label":{},".new-todo":{}}; const events=[]; const context={window:{},qs:(selector)=>elements[selector]||{style:{},dataset:{}},qsa:()=>[],$on:(element,type,handler)=>events.push({element,type,handler}),$delegate:()=>{},$parent:()=>({dataset:{id:"1"}})}; context.window=context; vm.createContext(context); vm.runInContext(fs.readFileSync(path,"utf8"),context); const view=new context.app.View({}); view.render("toggleAll",{checked:true}); assert.strictEqual(elements[".toggle-all"].checked,false,path); assert.strictEqual(elements[".toggle-all-label"].checked,true,path); let payload; view.bind("toggleAll",(data)=>{payload=data;}); assert.strictEqual(events.length,1,path); assert.strictEqual(events[0].element,elements[".toggle-all-label"],path); assert.strictEqual(events[0].type,"click",path); events[0].handler.call(elements[".toggle-all-label"]); assert.strictEqual(payload.completed,true,path); assert.strictEqual(elements[".toggle-all"].clicked,1,path);} exercise("examples/javascript-es5/src/view.js"); exercise("examples/javascript-es5/dist/view.js");'`
- `node -e 'const fs=require("fs"),assert=require("assert"); for (const path of ["examples/javascript-es5/index.html","examples/javascript-es5/dist/index.html"]){const html=fs.readFileSync(path,"utf8"); const input=html.match(/<input[^>]*class="toggle-all"[^>]*>/); assert(input,path); assert(!/\bid="toggle-all"/.test(input[0]),path); assert(/<label[^>]*class="toggle-all-label"[^>]*for="toggle-all"/.test(html),path);}'`

### Target

- `node -e 'const fs=require("fs"),vm=require("vm"),assert=require("assert"); function exercise(path){const elements={".todo-list":{},".todo-count":{},".clear-completed":{},".main":{style:{}},".footer":{style:{}},".toggle-all":{checked:false,click(){this.clicked=(this.clicked||0)+1;}},".toggle-all-label":{},".new-todo":{}}; const events=[]; const context={window:{},qs:(selector)=>elements[selector]||{style:{},dataset:{}},qsa:()=>[],$on:(element,type,handler)=>events.push({element,type,handler}),$delegate:()=>{},$parent:()=>({dataset:{id:"1"}})}; context.window=context; vm.createContext(context); vm.runInContext(fs.readFileSync(path,"utf8"),context); const view=new context.app.View({}); view.render("toggleAll",{checked:true}); assert.strictEqual(elements[".toggle-all"].checked,true,path); assert.strictEqual(elements[".toggle-all-label"].checked,undefined,path); let payload; view.bind("toggleAll",(data)=>{payload=data;}); assert.strictEqual(events.length,1,path); assert.strictEqual(events[0].element,elements[".toggle-all"],path); assert.strictEqual(events[0].type,"change",path); elements[".toggle-all"].checked=false; events[0].handler.call(elements[".toggle-all"]); assert.strictEqual(payload.completed,false,path); elements[".toggle-all"].checked=true; events[0].handler.call(elements[".toggle-all"]); assert.strictEqual(payload.completed,true,path); assert.strictEqual(elements[".toggle-all"].clicked,undefined,path);} exercise("examples/javascript-es5/src/view.js"); exercise("examples/javascript-es5/dist/view.js");'`
- `node -e 'const fs=require("fs"),assert=require("assert"); for (const path of ["examples/javascript-es5/index.html","examples/javascript-es5/dist/index.html"]){const html=fs.readFileSync(path,"utf8"); const input=html.match(/<input[^>]*class="toggle-all"[^>]*>/); assert(input,path); assert(/\bid="toggle-all"/.test(input[0]),path); assert(/<label[^>]*class="toggle-all-label"[^>]*for="toggle-all"/.test(html),path);}'`

## Success Criteria

- Tests must pass: `true`
- Max files changed: `4`

## Tags

- `bugfix`
- `javascript`
- `frontend`
- `dom-events`
- `state-handling`
- `real-repo`

## Expected Failure Modes

- `context_miss`
- `spec_misread`
- `bad_local_fix`
- `test_gap`
- `over_edit`
- `resource_inefficient`

_Generated from `task.yaml`. Do not edit by hand; regenerate with the task-card skill._
