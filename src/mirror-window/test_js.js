'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const O=require('./core.js');
const out=path.join(__dirname,'data');
const fixtures=JSON.parse(fs.readFileSync(path.join(out,'reference-fixtures.json'),'utf8'));
let checks=0,maxT=0,maxPeak=0,maxField=0,maxBand=0;
function near(a,b,tol,msg){checks++;assert.ok(Math.abs(a-b)<=tol,`${msg}: ${a} vs ${b}, tolerance ${tol}`);}
for(const f of fixtures){
 const [a,b]=O.stacks(f.m,f.error,f.mode,f.seed,1,f.kind);
 for(let i=0;i<b.length;i++){near(b[i].n,f.layers[i].n,2e-14,'layer n');near(b[i].d,f.layers[i].d,2e-12,'layer thickness');}
 const s=O.solve(b,f.wavelength,1,f.ns);maxT=Math.max(maxT,Math.abs(s.T-f.cavity_T));
 near(s.T,f.cavity_T,3e-11,'cavity T');near(O.solve(a,f.wavelength,1,f.ns).T,f.ordinary_T,3e-11,'ordinary T');near(s.R+s.T,1,2e-11,'power balance');
 const p=O.peak(b,1,f.ns);maxPeak=Math.max(maxPeak,Math.abs(p.wavelength-f.peak.wavelength));
 near(p.wavelength,f.peak.wavelength,2e-6,'peak wavelength');near(p.T,f.peak.T,3e-10,'peak T');
 const field=O.fieldProfile(b,f.wavelength,1,f.ns,8),emax=Math.max(...field.map(x=>x.E2));
 maxField=Math.max(maxField,Math.abs(emax-f.field_E2_max));near(emax,f.field_E2_max,Math.max(1e-10,1e-10*emax),'E2');
 const weights=O.sensitivity(f.m);weights.forEach((w,i)=>near(w,f.sensitivity[i],1e-13,'sensitivity'));
 near(O.predictedShift(f.m,f.error,f.mode,f.seed),f.predicted_shift,2e-10,'shift');
 if(f.band){const q=O.bandAverage(b,p.wavelength,1,1,f.ns,p);maxBand=Math.max(maxBand,Math.abs(q.T-f.band.T));near(q.T,f.band.T,2e-8,'Gaussian average');assert.equal(q.capped,false);checks++;}
}
for(const fn of [()=>O.stacks(9),()=>O.stacks(4,.1),()=>O.stacks(4,0,'bad'),()=>O.stacks(4,0,'independent',-1),()=>O.stacks(4,0,'independent',7,1,'bad'),()=>O.solve([],NaN),()=>O.solve([{n:1,d:-1}],600),()=>O.bandAverage([],600,-1)]){assert.throws(fn);checks++;}
console.log(JSON.stringify({fixtures:fixtures.length,checks,max_power_difference:maxT,max_peak_nm_difference:maxPeak,max_field_E2_difference:maxField,max_band_difference:maxBand,status:'PASS'},null,2));
