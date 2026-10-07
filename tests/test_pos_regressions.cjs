/* Run: node tests/test_pos_regressions.cjs
   Tests actual payment function bodies and offline interceptor without a browser/server.
   Requires @babel/parser (included transitively by the frontend toolchain).
*/
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const parser = require('@babel/parser');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'frontend/src/pages/POS.jsx'), 'utf8');
const ast = parser.parse(source, {sourceType:'module', plugins:['jsx']});
const nodes = {};
function walk(node) {
  if (!node || typeof node !== 'object') return;
  if (node.type === 'VariableDeclarator' && ['requestPayment','handlePayment'].includes(node.id?.name)) nodes[node.id.name] = node.init;
  if (node.type === 'JSXAttribute' && node.name?.name === 'onKeyDownCapture') nodes.capture = node.value.expression;
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) value.forEach(walk);
    else if (value && typeof value === 'object') walk(value);
  }
}
walk(ast);
function setup(overrides={}) {
  const state = {confirmed:false, submitting:false, calls:0, errors:[], cartCleared:false};
  let release;
  const wait = new Promise(resolve => {release=resolve});
  const ctx = {
    cart:[{product_id:'p',quantity:1,unit_price:25,discount_percent:0,vat_percent:0}],
    cartTotals:{total:25}, cashAmount:'25', couponData:null, paymentMethod:'cash',
    isDebt:false, debtorName:'', customerName:'', customerNote:'', printReceipt:false,
    paymentInFlight:{current:false}, confirmSale:false, user:{id:'u',tenant_id:'t'},
    toCents:v=>Math.round(v*100), prepareSaleAttempt:()=>({key:'test-sale-request'}),completeSaleAttempt:()=>{},releaseRejectedSaleAttempt:()=>{},
    toast:{error:msg=>state.errors.push(msg),success:()=>{}},
    api:{post:async()=>{state.calls++; await wait; if (ctx.fail) throw new Error('offline'); return {data:{receipt_number:'R1'}};}},
    setConfirmSale:v=>{state.confirmed=v;ctx.confirmSale=v;},
    setPaymentSubmitting:v=>{state.submitting=v;},
    setCart:()=>{state.cartCleared=true;ctx.cart=[];},
    setCouponData:()=>{},setCouponCode:()=>{},setShowPayment:()=>{},setCashAmount:()=>{},
    setCustomerName:()=>{},setCustomerNote:()=>{},setSelectedItemIndex:()=>{},setIsDebt:()=>{},setDebtorName:()=>{},
    loadData:()=>{}, ...overrides
  };
  vm.createContext(ctx);
  for (const name of ['handlePayment','requestPayment','capture']) {
    const node = nodes[name]; assert(node,`Missing ${name}`);
    vm.runInContext(`this.${name} = (${source.slice(node.start,node.end)});`,ctx);
  }
  return {ctx,state,release};
}
async function run() {
  const event = repeat=>({key:'Enter',repeat,preventDefault(){},stopPropagation(){}});
  let t=setup();t.ctx.capture(event(false));
  assert(t.state.confirmed);assert.equal(t.state.calls,0);
  t.ctx.capture(event(true));assert.equal(t.state.calls,0);
  t.ctx.capture(event(false));t.ctx.capture(event(false));
  assert.equal(t.state.calls,1); assert(t.state.submitting);t.release();
  await new Promise(r=>setImmediate(r));assert(t.state.cartCleared);assert(!t.state.submitting);
  console.log('PASS F2 payment dialog: first Enter confirms, second submits once, held Enter ignored');
  t=setup({cashAmount:'5'});t.ctx.requestPayment();assert.equal(t.state.calls,0);assert(!t.state.confirmed);assert.equal(t.state.errors.length,1);
  console.log('PASS insufficient cash is rejected');
  t=setup({paymentMethod:'bank',cashAmount:''});t.ctx.requestPayment();assert(t.state.confirmed);
  console.log('PASS bank payment supports confirmation without cash input');
  t=setup({fail:true});t.ctx.requestPayment();const pending=t.ctx.handlePayment();t.release();await pending;
  assert(!t.state.submitting);assert(!t.ctx.paymentInFlight.current);assert(!t.state.cartCleared);
  console.log('PASS failed sale keeps cart and releases submission lock');
  t=setup();t.ctx.requestPayment();let pending2=t.ctx.handlePayment();t.ctx.handlePayment();t.release();await pending2;
  assert.equal(t.state.calls,1);console.log('PASS repeated clicks do not duplicate request');
  const offlineSource=fs.readFileSync(path.join(root,'frontend/src/lib/offline.js'),'utf8')
    .replace(/export default offlineApi;/g,'').replace(/export (const|let|function) /g,'$1 ');
  const localStorage={'datapos_cache:/sales':'old','datapos_cache:/cashier/current':'old'};
  localStorage.setItem=(k,v)=>{localStorage[k]=v;};localStorage.getItem=k=>localStorage[k]||null;
  localStorage.removeItem=k=>{delete localStorage[k];};
  const handlers={};const offctx={localStorage,navigator:{onLine:true},window:{dispatchEvent(){}},
    CustomEvent:class{},Event:class{},console,Date,JSON,setTimeout,clearTimeout};
  vm.createContext(offctx);vm.runInContext(offlineSource+';this.attach=attachInterceptors;',offctx);
  const api={interceptors:{response:{use:(ok,error)=>{handlers.ok=ok;handlers.error=error;}}}};offctx.attach(api);
  handlers.ok({config:{method:'post',url:'/admin/reset-data'},data:{}});
  assert(!localStorage['datapos_cache:/sales']);assert(!localStorage['datapos_cache:/cashier/current']);
  console.log('PASS reset clears stale sales/drawer cache');
  await assert.rejects(()=>handlers.error({message:'Network Error',config:{method:'delete',url:'/sales/sale1'}}));
  console.log('PASS offline deletion fails visibly and is never queued');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
