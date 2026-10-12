'use strict';
const assert=require('node:assert/strict');
const M=require('../src/clocks/model.js');
const results=[];
function test(name,f){f();results.push(name);console.log('PASS',name);}
const n=32,edge=M.edges(n),a=M.initial(n,'random',7);
const near=(a,b,tol=1e-10)=>assert.ok(Math.abs(a-b)<tol,`${a} != ${b} (tol ${tol})`);
test('uncoupled analytic motion and coherence invariant',()=>{
 const omega=a.map((_,i)=>1+i*.001),r=M.simulate({theta:a,edge:[],omega,T:10,dt:.05});
 r.theta.forEach((x,i)=>near(x,a[i]+10*omega[i],1e-11));
 const r2=M.simulate({theta:a,edge:[],omega:1,T:10,dt:.05});near(r2.final.R,M.metrics(a,[],1).R);
});
test('rotation equivariance of drift and metrics',()=>{
 const b=a.map(x=>x+1.37);M.drift(a,edge,1).forEach((x,i)=>near(x,M.drift(b,edge,1)[i]));
 const ma=M.metrics(a,edge),mb=M.metrics(b,edge);for(const k of ['R','C','energy','q','driftSpread'])near(ma[k],mb[k]);
});
test('undirected coupling conserves mean drift',()=>near(M.drift(a,edge,1).reduce((s,x)=>s+x,0)/n,1));
test('q=1 exact wave: zero global coherence, high neighbor agreement, same frequency',()=>{
 const twist=Array.from({length:n},(_,i)=>M.TAU*i/n),m=M.metrics(twist,edge);
 near(m.R,0);near(m.C,Math.cos(M.TAU/n));near(m.q,1);near(m.driftSpread,0);
 M.drift(twist,edge,1).forEach(x=>near(x,1));
});
test('energy gradient identity and monotone deterministic relaxation',()=>{
 const h=1e-6,v=M.drift(a,edge,0),expected=-v.reduce((s,x)=>s+x*x,0);
 const derivative=(M.metrics(a.map((x,i)=>x+h*v[i]),edge).energy-M.metrics(a.map((x,i)=>x-h*v[i]),edge).energy)/(2*h);
 near(derivative,expected,1e-7);
 const r=M.simulate({theta:a,edge,T:40,dt:.025,sampleEvery:.1});
 r.samples.slice(1).forEach((x,i)=>assert.ok(x.energy<=r.samples[i].energy+1e-10));
});
test('linear stability: low twist decays, high twist grows with predicted rate',()=>{
 for(const q of [1,9]){
  const base=Array.from({length:n},(_,i)=>M.TAU*q*i/n),eps=1e-5;
  const b=base.map((x,i)=>x+eps*((i%2)?-1:1));
  const r=M.simulate({theta:b,edge,omega:0,T:1,dt:.01});
  const amplitude=r.theta.reduce((s,x,i)=>s+M.wrap(x-base[i])*((i%2)?-1:1),0)/n;
  near(Math.log(Math.abs(amplitude/eps)),-2*Math.cos(M.TAU*q/n),2e-7);
 }
});
test('RK4 refinement agrees on a nontrivial transient',()=>{
 const runs=[.1,.05,.025].map(dt=>M.simulate({theta:a,edge,T:10,dt}));
 const err=(p,q)=>Math.max(...p.theta.map((x,i)=>Math.abs(M.wrap(x-q.theta[i]))));
 const e1=err(runs[0],runs[2]),e2=err(runs[1],runs[2]);
 assert.ok(e2<e1/8);assert.ok(e2<2e-6);console.log('  errors dt=.1/.05 vs .025',e1,e2);
});
test('common additive noise preserves relative phases compared with same Euler drift',()=>{
 let quiet=a.slice(),noisy=a.slice();const random=M.rng(88),dt=.01;
 for(let k=0;k<1000;k++){
  const v=M.drift(quiet,edge,1);quiet=quiet.map((x,i)=>x+dt*v[i]);
  noisy=M.step(noisy,edge,1,dt,.5,random,'common');
 }
 for(let i=1;i<n;i++)near(noisy[i]-noisy[0],quiet[i]-quiet[0],1e-10);
});
test('noise variance convention: uncoupled variance = 2 D T',()=>{
 const D=.2,T=1,dt=.02,N=2000;
 const r=M.simulate({theta:Array(N).fill(0),edge:[],omega:0,D,T,dt,seed:123,sampleEvery:1});
 const mean=r.theta.reduce((s,x)=>s+x,0)/N,variance=r.theta.reduce((s,x)=>s+(x-mean)**2,0)/N;
 assert.ok(Math.abs(variance-2*D*T)<.04);console.log('  observed variance',variance,'expected',2*D*T);
});
test('seed replay reproduces independent-noise trajectory exactly',()=>{
 const config={theta:a,edge,D:.2,T:2,seed:123};assert.deepEqual(M.simulate(config),M.simulate(config));
});
console.log(JSON.stringify({passed:results.length,tests:results},null,2));
