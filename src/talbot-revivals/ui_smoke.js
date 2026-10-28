/* Runs actual app code with a minimal DOM/canvas stand-in. NOT browser QA. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const art=__dirname;
const html=fs.readFileSync(path.join(art,'index.html'),'utf8');
let checks=0,carpets=0;
class Element{
 constructor(id){this.id=id;this.value='';this.textContent='';this.innerHTML='';this.checked=false;this.hidden=false;this.disabled=false;this.style={};this.dataset={};this.listeners={};this.attributes={};}
 addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
 setAttribute(k,v){this.attributes[k]=v;}
 fire(name,e={}){for(const fn of this.listeners[name]||[])fn(e);}
 getBoundingClientRect(){return {top:0,height:254};}
 getContext(){return {createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:img=>{this.pixels=img.data;carpets++;}};}
}
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]),els=new Map(ids.map(id=>[id,new Element(id)]));
assert.equal(new Set(ids).size,ids.length);checks++;
for(const match of html.matchAll(/<select id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)){
 els.get(match[1]).options=[...match[2].matchAll(/<option[^>]*value="([^"]+)"[^>]*>([^<]*)<\/option>/g)].map(m=>({value:m[1],textContent:m[2]}));
}
for(const [id,value] of Object.entries({width:'0.025',alpha:'0.01',chirp:'0',profile:'pulse',distance:'1'}))els.get(id).value=value;
const frac=[...html.matchAll(/<button[^>]*data-t="([^"]+)"[^>]*>/g)].map(m=>{const e=new Element('fraction');e.dataset.t=m[1];return e;});
const scenario=[...html.matchAll(/<button[^>]*data-scenario="([^"]+)"[^>]*>/g)].map(m=>{const e=new Element('scenario');e.dataset.scenario=m[1];return e;});
const document={getElementById:id=>{if(!els.has(id))throw Error('Unknown ID '+id);return els.get(id);},querySelectorAll:selector=>selector==='[data-t]'?frac:selector==='[data-scenario]'?scenario:[]};
const context=vm.createContext({document,Math,Number,Map,Array,Error,Uint8ClampedArray});
const inline=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);assert.equal(inline.length,2);checks++;
for(const code of inline)vm.runInContext(code,context,{timeout:10000});
function check(value,msg){checks++;assert.ok(value,msg);}
function el(id){return els.get(id);}
function clean(){check(el('error').textContent==='','App reported error');check(!/NaN|Infinity/.test(el('slice-plot').innerHTML),'Non-finite curve');}
check(el('chirp-current').textContent==='Selected: None · real input','Full phase selection text');check(el('profile-current').textContent==='Selected: Smooth periodic pulses','Full spectrum selection text');
clean();check(el('f-para').textContent==='100.000%','Full return');check(el('f-exact').textContent==='87.753%','Exact return fixture');
el('retune').fire('click');clean();check(el('tuning-result').textContent.includes('95.929'),'Tuned return improvement');
const before=el('exact-carpet').pixels.slice();
scenario.find(e=>e.dataset.scenario==='thirds').fire('click');clean();check(el('mixture').checked&&!el('mixture').disabled,'Thirds control enabled');check(el('mixture-result').textContent.includes('0.4550'),'Thirds discrepancy fixture');
scenario.find(e=>e.dataset.scenario==='twins').fire('click');clean();check(el('twins-result').textContent.includes('22.568')&&el('twins-result').textContent.includes('2.053'),'Twins fixture');
check(el('chirp-current').textContent==='Selected: + phase · b = +0.06','Scenario updates full phase selection');
check(before.some((v,i)=>v!==el('exact-carpet').pixels[i]),'Carpet changed with input');
el('chirp').value='-0.06';el('chirp').fire('change');clean();
frac.find(e=>e.dataset.t==='0.25').fire('click');clean();check(el('mixture-result').textContent.includes('Dropping copy phase changes'),'Complex quarter control');
scenario.find(e=>e.dataset.scenario==='null').fire('click');clean();check(el('mixture-result').textContent.includes('Agreement here'),'Real quarter null');
el('distance').value='0.4';el('distance').fire('input');clean();check(el('mixture').disabled,'No named fraction at arbitrary distance');
el('profile').value='three';el('profile').fire('change');clean();check(el('width').disabled&&el('phase-gap').textContent==='order absent','Absent-order diagnostic');check(el('profile-current').textContent==='Selected: Three orders · analytic check','Changed spectrum selection text');
el('profile').value='pulse';el('width').value='0.02';el('alpha').value='0.025';el('profile').fire('change');clean();
// A canvas click changes the selection without recalculating its pixel carpet.
const count=carpets;el('para-carpet').fire('click',{clientY:127});clean();check(carpets===count,'Slice-only navigation');check(el('status').textContent.includes('half a return'),'Canvas selection half return');
check(!/<(?:script|link|img)[^>]+(?:src|href)=/i.test(html),'Unexpected external asset');
check(!/\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|setTimeout|localStorage)\b/.test(inline.join('\n')),'Unexpected network/storage/timer capability');
console.log(JSON.stringify({status:'PASS',checks,carpetsComputed:carpets,scope:'actual inline scripts evaluated with stand-in DOM/canvas; no browser, layout, accessibility-tree or console claim',node:process.version},null,2));
