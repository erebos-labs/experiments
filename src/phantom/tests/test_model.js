'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const M=require('../src/model.js'),out=path.resolve(__dirname,'../results');
fs.mkdirSync(out,{recursive:true});
const started=new Date(),results=[];
function check(name,fn){const t=performance.now();const details=fn();results.push({name,status:'PASS',ms:performance.now()-t,details});}
const close=(a,b,e=1e-9)=>assert.ok(Math.abs(a-b)<=e,`${a} vs ${b}, allowed ${e}`);
function maxAbs(v){let max=0;for(const x of v){assert.ok(Number.isFinite(x));max=Math.max(max,Math.abs(x));}return max;}
check('candidate grid rejects non-progressing steps and bounds direct API work',()=>{
 for(const step of [Number.MIN_VALUE,1e-18,0.0249,0,-1,361,NaN,Infinity])assert.throws(()=>M.candidates(30,20,15,step),RangeError);
 for(const args of [[Infinity,20,15],[30,NaN,15],[30,20,Infinity],[30,20,-1]])assert.throws(()=>M.candidates(...args),RangeError);
 const dense=M.candidates(30,20,15,0.025);assert.ok(dense.single.length<=14400);assert.ok(dense.both.length<=dense.single.length);
 assert.equal(M.candidates(30,0,0,0.25).single.length,2);
 return {maximum_grid_samples:14400,invalid_cases:12,default_grid_unchanged:true};
});
check('analytic cardinal directions and sign convention',()=>{
 close(M.delay(0),0);close(M.delay(180),0);close(M.delay(90),1e6*0.18/343);close(M.delay(-90),-1e6*0.18/343);
 close(M.delay(30),1e6*0.09/343);close(M.delay(30,30),0);close(M.delay(30,0,90),0);
 return {maximum_us:M.MAX_US,front30_us:M.delay(30),yaw20_A_us:M.delay(30,20),yaw20_B_us:M.delay(150,20)};
});
check('front/back reflection preserves individual finite-range path lengths',()=>{
 let maxError=0,cases=0;
 for(const distance of [0.12,0.2,0.5,2,10])for(let az=-180;az<180;az+=0.5)for(const el of [-60,0,60]){
  // Independently calculate each path before taking their difference.
  const x=distance*Math.sin(az*Math.PI/180)*Math.cos(el*Math.PI/180),y=distance*Math.cos(az*Math.PI/180)*Math.cos(el*Math.PI/180),z=distance*Math.sin(el*Math.PI/180);
  for(const earX of [-0.09,0.09]){
   const original=Math.hypot(x-earX,y,z),reflected=Math.hypot(x-earX,-y,z);
   maxError=Math.max(maxError,Math.abs(original-reflected));close(original,reflected,1e-12);cases++;
  }
  close(M.exactDelay(az,0,distance,el),M.exactDelay(M.mirror(az),0,distance,el),1e-8);
 }
 return {individual_paths_checked:cases,max_path_mirror_error_m:maxError};
});
check('far-field approximation converges to finite-range geometry',()=>{
 const rows=[];
 for(const distance of [0.2,0.5,1,2,5,10,50]){
  let maxError=0;for(let az=-180;az<180;az+=0.25)maxError=Math.max(maxError,Math.abs(M.exactDelay(az,0,distance)-M.delay(az)));
  rows.push({range_m:distance,max_error_us:maxError});
 }
 for(let i=1;i<rows.length;i++)assert.ok(rows[i].max_error_us<rows[i-1].max_error_us);
 assert.ok(rows[3].max_error_us<0.6);assert.ok(rows.at(-1).max_error_us<0.001);
 return rows;
});
check('horizontal two-pose inverse recovers all azimuths; zero and 180 deg poses singular',()=>{
 let n=0,maxError=0;
 for(const yaw of [-90,-45,-20,-1,0.01,1,20,45,90])for(let az=-180;az<180;az+=0.25){
  const r=M.reconstruct(M.delay(az),M.delay(az,yaw),yaw),error=Math.abs(M.wrap(r.azimuth-az));
  maxError=Math.max(maxError,error);assert.ok(error<1e-7);n++;
 }
 assert.equal(M.reconstruct(0,0,0),null);assert.equal(M.reconstruct(0,0,180),null);
 return {cases:n,max_error_deg:maxError};
});
check('3D cone and vertical mirror survive all yaw poses',()=>{
 let n=0,maxError=0;
 for(const q of [-0.9,-0.5,0,0.5,0.9])for(let orbit=0;orbit<360;orbit+=5){
  const v=M.cone(q,orbit);close(Math.hypot(...v),1);close(M.delayVector(v),M.MAX_US*q);
  for(let yaw=-180;yaw<=180;yaw+=10){
   const mirror=[v[0],v[1],-v[2]],error=Math.abs(M.delayVector(v,yaw)-M.delayVector(mirror,yaw));
   maxError=Math.max(maxError,error);close(error,0);n++;
  }
 }
 return {comparisons:n,max_mirror_difference_us:maxError};
});
check('candidate sets retain truth and shrink under second constraint',()=>{
 let cases=0;const example=[];
 for(const az of [-80,-30,0,30,80])for(const yaw of [-45,-20,0,20,45])for(const tolerance of [0,5,15,40]){
  const c=M.candidates(az,yaw,tolerance),initial=new Set(c.single);assert.ok(initial.has(az));assert.ok(c.both.includes(az));assert.ok(c.both.every(a=>initial.has(a)));
  if(yaw===0)assert.deepEqual(c.both,c.single);
  if(az===30&&tolerance===15)example.push({azimuth:az,yaw,tolerance_us:tolerance,single:c.single.length,both:c.both.length});cases++;
 }
 assert.deepEqual(M.candidates(30,0,0).single,[30,150]);assert.deepEqual(M.candidates(30,20,0).both,[30]);
 return {cases,example};
});
check('audio defaults are exactly silent; fixed bound; correct channel direction',()=>{
 const rows=[];
 for(const sampleRate of [44100,48000,96000])for(const tau of [-M.MAX_US,-262.39067055393585,0,262.39067055393585,M.MAX_US]){
  const silent=M.stereo(tau,undefined,sampleRate,0.1);assert.equal(maxAbs(silent.left),0);assert.equal(maxAbs(silent.right),0);
  const data=M.stereo(tau,0.04,sampleRate,0.1);const peak=Math.max(maxAbs(data.left),maxAbs(data.right));assert.ok(peak<=0.04000001);
  close((data.leftDelay-data.rightDelay)*1e6,tau,1e-9);
  assert.equal(data.left[0],0);assert.equal(data.right[0],0);assert.equal(data.left.at(-1),0);assert.equal(data.right.at(-1),0);
  if(tau===0)assert.deepEqual(data.left,data.right);
  rows.push({sampleRate,tau_us:tau,peak,duration_s:data.duration});
 }
 for(const gain of [-1,0.041,Infinity,NaN])assert.throws(()=>M.stereo(0,gain));
 for(const tau of [M.MAX_US+1,NaN,Infinity])assert.throws(()=>M.stereo(tau,0));
 for(const duration of [0.01,4,NaN,Infinity])assert.throws(()=>M.stereo(0,0,48000,duration));
 return rows;
});
check('front/back candidates synthesize indistinguishable channels at zero yaw',()=>{
 const a=M.stereo(M.delay(30),0.04),b=M.stereo(M.delay(150),0.04);let max=0;
 for(let i=0;i<a.left.length;i++)max=Math.max(max,Math.abs(a.left[i]-b.left[i]),Math.abs(a.right[i]-b.right[i]));
 assert.ok(max<1e-8);return {samples_per_channel:a.left.length,maximum_sample_difference:max,peak:Math.max(maxAbs(a.left),maxAbs(a.right))};
});
const report={started_utc:started.toISOString(),ended_utc:new Date().toISOString(),runtime_ms:Date.now()-started.getTime(),node:process.version,model:'two unobstructed point receivers; far-field plane wave; d=0.18m,c=343m/s',tests:results,status:'PASS',limits:'Unit/numerical checks, not browser output or human perception.'};
fs.writeFileSync(path.join(out,'model-tests.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
