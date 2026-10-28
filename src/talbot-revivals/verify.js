/* Numerical JS engine cross-check against independently evaluated Python fixtures. */
'use strict';
const fs=require('node:fs'),path=require('node:path');require('./model.js');
const M=globalThis.TalbotModel,art=path.join(__dirname,'data');
const fixtures=JSON.parse(fs.readFileSync(path.join(art,'fixtures.json'),'utf8'));
let checks=0,maxError=0;
function near(a,b,tol=2e-10){checks++;const d=Math.abs(a-b);maxError=Math.max(maxError,d);if(!Number.isFinite(a)||d>tol)throw Error(`Mismatch ${a} vs ${b}: ${d}`);}
for(const f of fixtures){
 const c=M.coefficients(f.width,32,f.chirp,f.profile),e=M.propagate(c,f.t,f.alpha,f.exact);
 near(M.fidelity(c,e),f.fidelity);
 for(const [x,re,im] of f.fields){const got=M.field(e,x);near(got[0],re);near(got[1],im);}
}
for(const q of [2,3,4,5,6,8,12]){
 const c=M.coefficients(.08,16,.06),e=M.propagate(c,1/q);
 for(let j=0;j<31;j++){const a=M.field(e,j/31),b=M.replicaField(c,j/31,1,q);near(a[0],b[0]);near(a[1],b[1]);}
}
const ref=JSON.parse(fs.readFileSync(path.join(art,'study.json'),'utf8')).retuning.pulse;
const tuned=M.findReturn(M.coefficients(),.01);near(tuned.t,ref.t,1e-7);near(tuned.fidelity,ref.fidelity);
for(const args of [[32,1,.04],[1,9,.01],[1,1,NaN]]){
 checks++;let rejected=false;try{M.residualPhase(...args);}catch(e){rejected=true;}if(!rejected)throw Error('Invalid propagation accepted');
}
console.log(JSON.stringify({status:'PASS',fixtureRows:fixtures.length,checks,maxAbsError:maxError,node:process.version,scope:'numerical model; no browser/DOM/render claim'},null,2));
