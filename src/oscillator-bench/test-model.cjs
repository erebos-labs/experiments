'use strict';
const assert=require('node:assert/strict'),M=require('./model.js');
const tests=[];function check(name,fn){fn();tests.push(name);}
const end=(k,h=.01,initial=M.INITIAL,T=120)=>M.trajectory(k,h,T,initial).at(-1).z;
const maxDiff=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
check('uncoupled unit orbits against analytic solution',()=>{const z=end(0,.0025,[1,0,1,0],2);assert.ok(maxDiff(z,[Math.cos(4),Math.sin(4),Math.cos(16),Math.sin(16)])<1e-7);});
check('documented amplitude-death cases',()=>{for(const k of [1.5,2,4])assert.ok(Math.max(...M.radii(end(k)))<1e-15);});
check('strong-coupling amplitude and phase reference',()=>{const z=end(6),r=Math.sqrt(1-6+Math.sqrt(36-9));assert.ok(M.radii(z).every(v=>Math.abs(v-r)<1e-7));assert.ok(Math.abs(M.phase(z)-Math.PI/6)<1e-10);});
check('weak coupling keeps slipping',()=>{const data=M.trajectory(.5).filter(s=>s.t>=100);let net=0;for(let i=1;i<data.length;i++){const d=M.phase(data[i].z)-M.phase(data[i-1].z);net+=Math.atan2(Math.sin(d),Math.cos(d));}assert.ok(net>100);});
check('smooth trajectory step refinement',()=>{const a=end(6,.02),b=end(6,.01),c=end(6,.005);assert.ok(maxDiff(b,c)<maxDiff(a,b)/12);});
check('phase hidden at negligible amplitude',()=>{assert.equal(M.phase([0,0,1,0]),null);assert.equal(M.phase(end(2)),null);});
check('energy balance',()=>{const z=[.7,.1,-.2,.3],k=2,d=M.derivative(z,k);const lhs=2*z.reduce((a,v,i)=>a+v*d[i],0),r=M.radii(z);const rhs=2*(r[0]**2+r[1]**2)-2*(r[0]**4+r[1]**4)-2*k*((z[0]-z[2])**2+(z[1]-z[3])**2);assert.ok(Math.abs(lhs-rhs)<1e-12);});
check('stability interval and boundaries',()=>{assert.ok(M.growth(.5)>0);assert.ok(M.growth(2)<0);assert.ok(M.growth(4)<0);assert.ok(M.growth(6)>0);assert.equal(M.growth(1),0);assert.equal(M.growth(5),0);});
check('bounded inputs and deterministic reset',()=>{assert.throws(()=>M.trajectory(9));assert.throws(()=>M.trajectory(NaN));assert.throws(()=>M.trajectory(2,.0001));assert.deepEqual(M.trajectory(2),M.trajectory(2));assert.deepEqual(M.INITIAL,[1,.2,-.3,.7]);});
console.log(JSON.stringify({passed:tests.length,tests,references:[.5,2,4,6].map(k=>({k,amplitudes:M.radii(end(k)),phase:M.phase(end(k))}))},null,2));
