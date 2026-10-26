'use strict';
const fs=require('fs'),assert=require('assert'),L=require('./core.js');let checks=0,maxError=0,maxTheoryError=0;
const fixtures=JSON.parse(fs.readFileSync('data/reference-fixtures.json'));
for(const f of fixtures){const r=L.simulate(...f.args,true),t=L.theory(f.args[0],f.args[1],f.args[2],f.args[4]);for(const k of Object.keys(r)){if(Array.isArray(r[k]))r[k].forEach((x,i)=>{maxError=Math.max(maxError,Math.abs(x-f.simulation[k][i]));assert(Math.abs(x-f.simulation[k][i])<1e-8);checks++;});else {maxError=Math.max(maxError,Math.abs(r[k]-f.simulation[k]));assert(Math.abs(r[k]-f.simulation[k])<(k==='mse'&&f.args[2]===1e6?.001:1e-12));checks++;}}for(const k of Object.keys(t)){const err=Math.abs(t[k]-f.theory[k]);maxTheoryError=Math.max(maxTheoryError,err);assert(err<2e-7,k+' '+err);checks++;}}
assert.deepStrictEqual(L.simulate(),L.simulate());checks++;
for(const a of [0,.25,2])for(const t of [-2,0,2])for(const s of [0,.1,4,1e6]){const r=L.simulate(a,t,s,42,64);assert(Object.values(r).every(Number.isFinite));checks++;}
for(const bad of [[NaN,1,1,0,64],[.2,1,-1,0,64],[.2,1,1,-1,64],[.2,1,1,0,65]]){assert.throws(()=>L.simulate(...bad));checks++;}
const b=L.ensemble(.25,1,.8,20261025,256,32);assert(b.signal.balanced_accuracy.mean>.52);checks++;
const d=L.detection(.25,1,.8);assert(d.training_false<=.05);assert(d.power.rate>d.false_alarm.rate+.2);checks+=2;
const result={status:'PASS',checks,max_simulation_absolute_error:maxError,max_theory_absolute_error:maxTheoryError,notes:'JS uses erfc approximation; Python math.erfc reference. MSE at sigma 1e6 compared by absolute tolerance .001 (relative error near machine precision); all other scalar simulation metrics tolerance1e-12.'};
fs.writeFileSync('data/js-checks.json',JSON.stringify(result,null,2)+'\n');console.log(result);
