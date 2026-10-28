'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const {solve}=require(process.argv[2]?path.resolve(process.argv[2]):'./access_solver.js');
const rejected=[
 {name:'reported occupied-origin loss',points:[[0,0]],radii:{launch:.1,kill:1.1}},
 {name:'partly occupied rounded source',points:[[0,0],[2,0]],radii:{launch:2,kill:6},settings:{sourceSamples:64}},
 {name:'rounded launch outside kill circle',points:[[0,0]],radii:{launch:1.9,kill:2},settings:{sourceSamples:8}}
];
for(const c of rejected)assert.throws(()=>solve(c.points,c.radii,c.settings),{name:'RangeError',message:/Rounded launch source/},c.name);
const cases=[
 {name:'all immediate perimeter hits',points:[[0,0]],radii:{launch:1,kill:5},settings:{sourceSamples:8}},
 ...[4,257,65536].map(sourceSamples=>({name:'fluid source '+sourceSamples,points:[[0,0]],radii:{launch:3,kill:6},settings:{sourceSamples}})),
 {name:'asymmetric cluster',points:[[0,0],[1,0]],radii:{launch:3,kill:7},settings:{sourceSamples:256}}
];
const rows=[];
for(const c of cases){
 const r=solve(c.points,c.radii,c.settings);
 assert(r.sweeps<r.maxSweeps,c.name+' must converge');assert(r.residual<1e-10,c.name+' residual');
 assert(Math.abs(r.hit+r.escape-1)<5e-8,c.name+' unit launch flux must be accounted for');
 assert.equal(r.fluxTotal,r.hit+r.escape);assert(r.hit>=0&&r.escape>=0);
 assert(r.probabilities.every(p=>p.probability>=-1e-12&&p.conditional>=-1e-12));
 assert(Math.abs(r.probabilities.reduce((s,p)=>s+p.probability,0)-r.hit)<1e-12,'site mass must equal total hit mass');
 assert(Math.abs(r.probabilities.reduce((s,p)=>s+p.conditional,0)-1)<1e-12,'conditional first hits normalize');
 if(c.name==='all immediate perimeter hits'){assert.equal(r.hit,1);assert.equal(r.escape,0);for(const p of r.probabilities)assert.equal(p.probability,.25);}
 else assert(r.hit>0&&r.escape>0,'fluid cases have both absorbed and escaped mass');
 rows.push({name:c.name,sourceSamples:r.sourceSamples,sweeps:r.sweeps,residual:r.residual,hit:r.hit,escape:r.escape,fluxTotal:r.fluxTotal});
}
console.log(JSON.stringify({status:'PASS',rejected:rejected.map(c=>c.name),convergedFluxCases:rows},null,2));
