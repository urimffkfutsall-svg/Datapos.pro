/* Tests actual SuperAdmin handler bodies; no browser, real HTTP or React rendering. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict'),parser=require('@babel/parser');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'frontend/src/pages/SuperAdmin.jsx'),'utf8');
const ast=parser.parse(source,{sourceType:'module',plugins:['jsx']}),nodes={};
const names=['reportError','beginMutation','endMutation','handleSubmit','handleDelete','handleCreateUser'];
function walk(node){if(!node||typeof node!=='object')return;if(node.type==='VariableDeclarator'&&names.includes(node.id?.name))nodes[node.id.name]=node.init;for(const v of Object.values(node)){if(Array.isArray(v))v.forEach(walk);else if(v&&typeof v==='object')walk(v)}}walk(ast);
function setup(extra={}){
 const state={calls:[],errors:[],saving:false};let release;
 const wait=new Promise(r=>release=r);
 const ctx={mutationLock:{current:false},editingTenant:null,editingUser:null,selectedTenant:{id:'A'},formData:{name:'marketnlagje',subscription_months:3},userFormData:{username:'admin',password:'test',full_name:'Admin',role:'admin',pin:''},setSaving:v=>state.saving=v,setActionError:v=>state.error=v,setShowDialog:()=>{},setShowUserDialog:()=>{},loadTenants:async()=>{},window:{confirm:()=>true},toast:{error:m=>state.errors.push(m),success:()=>{}},api:Object.fromEntries(['post','put','delete'].map(method=>[method,async(url,data)=>{state.calls.push({method,url,data});await wait;if(ctx.fail)throw ctx.fail;return {data:{}}}])),...extra};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'frontend/src/lib/apiError.js'),'utf8').replace('export function','function')+';this.apiErrorMessage=apiErrorMessage;',ctx);
 for(const name of names)vm.runInContext(`this.${name}=(${source.slice(nodes[name].start,nodes[name].end)});`,ctx);
 return {ctx,state,release};
}
(async()=>{
 let t=setup(),pending=t.ctx.handleSubmit();t.ctx.handleSubmit();assert.equal(t.state.calls.length,1);assert.equal(t.state.calls[0].url,'/tenants');assert.equal(t.state.calls[0].data.subscription_months,3);t.release();await pending;assert(!t.state.saving);console.log('PASS create tenant forwards subscription and prevents duplicate submissions');
 t=setup({editingTenant:{id:'A'},formData:{company_name:'Changed',email:'valid@example.com'}});pending=t.ctx.handleSubmit();assert.equal(t.state.calls[0].method,'put');assert.equal(t.state.calls[0].url,'/tenants/A');t.release();await pending;console.log('PASS editing uses the correct tenant route');
 t=setup({window:{confirm:()=>false}});await t.ctx.handleDelete('A');assert.equal(t.state.calls.length,0);console.log('PASS cancelled deletion sends no request');
 t=setup();pending=t.ctx.handleDelete('A');t.ctx.handleDelete('A');assert.equal(t.state.calls.length,1);assert.equal(t.state.calls[0].method,'delete');t.release();await pending;console.log('PASS confirmed deletion is single-flight');
 t=setup({fail:{response:{status:404,data:{detail:'Firma nuk u gjet'}}}});pending=t.ctx.handleDelete('A');t.release();await pending;assert.equal(t.state.error,'Firma nuk u gjet');assert(!t.ctx.mutationLock.current);console.log('PASS backend errors are visible and failed deletion releases the lock');
 t=setup({editingUser:{id:'u'},userFormData:{username:'admin',password:'',full_name:'Admin',role:'admin',pin:''}});pending=t.ctx.handleCreateUser();assert.equal(t.state.calls[0].url,'/tenants/A/users/u');assert.equal(t.state.calls[0].method,'put');assert(!('password' in t.state.calls[0].data));assert(!('username' in t.state.calls[0].data));t.release();await pending;console.log('PASS blank password during edit leaves the password unchanged');
 t=setup({editingUser:{id:'u'}});pending=t.ctx.handleCreateUser();assert.equal(t.state.calls[0].data.password,'test');t.release();await pending;console.log('PASS super-admin can submit a new tenant-user password');
 t=setup();const msg=t.ctx.apiErrorMessage({response:{status:422,data:{detail:[{loc:['body','name'],msg:'Invalid value'}]}}});assert.equal(msg,'name: Invalid value');console.log('PASS validation arrays become readable text instead of invalid toast objects');
})().catch(e=>{console.error(e);process.exitCode=1});
