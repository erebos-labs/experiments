/* Pure local DOM stub: verifies authored control wiring, NOT browser rendering. */
'use strict';const fs=require('fs'),vm=require('vm'),assert=require('assert');
const values={amplitude:'.25',threshold:'1',noise:'.8',seed:'20261025',samples:'256',metric:'balanced_accuracy'};
const elements={};let checks=0;
function element(id){if(!elements[id])elements[id]={id,value:values[id]||'',checked:false,disabled:false,innerHTML:'',textContent:'',listeners:{},attributes:{},addEventListener(k,fn){this.listeners[k]=fn;},setAttribute(k,v){this.attributes[k]=v;}};if(!elements[id]._coercion){let held=String(elements[id].value);Object.defineProperty(elements[id],'value',{get(){return held;},set(v){held=String(v);}});elements[id]._coercion=true;}return elements[id];}
const context={NoiseLab:require('./core.js'),EXACT_STUDY:JSON.parse(fs.readFileSync('data/exact-control.json')),FROZEN_STUDY:JSON.parse(fs.readFileSync('data/controls.json')),document:{getElementById:element},window:{},performance,setTimeout,clearTimeout,console};vm.createContext(context);vm.runInContext(fs.readFileSync('ui.js','utf8'),context);const render=()=>vm.runInContext('render()',context),result=()=>context.window.lastResult;
assert.equal(result().parameters.a,.25);checks++;
assert(element('trace').innerHTML.includes('<path'));assert(!/NaN|Infinity/.test(element('trace').innerHTML));checks+=2;
element('baseline').onclick();assert.equal(result().parameters.s,0);assert.equal(result().singleRecord.balanced_accuracy,.5);checks+=2;
element('retune').onclick();assert.equal(result().singleRecord.balanced_accuracy,1);assert.equal(result().singleRecord.phase_mi,1);checks+=2;
element('reset').onclick();assert.equal(result().parameters.t,1);checks++;
element('null').checked=true;render();assert.equal(result().parameters.a,0);assert(result().anyActive.null===result().anyActive.signal);checks+=2;
element('null').checked=false;element('seed').value='0';render();const seed0=JSON.stringify(result().singleRecord);render();assert.equal(seed0,JSON.stringify(result().singleRecord));checks++;
element('seed').value='4294967295';render();assert.notEqual(JSON.stringify(result().singleRecord),seed0);checks++;
for(const invalid of ['', '-1','1.5','4294967296','NaN']){element('seed').value=invalid;render();assert.equal(result(),null);assert(element('download').disabled);assert.equal(element('seed').attributes['aria-invalid'],'true');checks+=3;}
element('seed').value='20261025';render();assert(!element('download').disabled);checks++;
for(const metric of ['balanced_accuracy','phase_mi','projection','magnitude','crossing_rate']){element('metric').value=metric;render();assert(!/NaN|Infinity/.test(element('sweep').innerHTML));assert(element('sweep-note').textContent.length>60);checks+=2;}
for(const n of ['64','256','1024']){element('samples').value=n;render();assert.equal(result().parameters.n,Number(n));assert(!/NaN|Infinity/.test(element('trace').innerHTML));checks+=2;}
element('amplitude').value='0';element('threshold').value='-.5';element('noise').value='0';render();assert.equal(result().singleRecord.crossing_rate,1);assert.equal(result().anyActive.null,1);checks+=2;
const out={status:'PASS',checks,scope:'Pure Node VM with minimal DOM stubs. Does not execute a browser or test layout, pixels, accessibility tree, actual downloads, browser console or navigation.'};
fs.writeFileSync('data/ui-wiring-checks.json',JSON.stringify(out,null,2)+'\n');console.log(out);
