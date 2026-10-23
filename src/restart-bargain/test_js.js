'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {searchMean,searchDistribution,searchQuantile,lowMeanRate}=require('./core.js');
const fixtures=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'data/js-reference.json'),'utf8'));
let comparisons=0;
for(const row of fixtures){
 const {length:L,start:s,reset:r,cost:c,mode,H}=row;
 const m=searchMean(L,s,r,c,mode), S=searchDistribution(L,s,r,H,c,mode);
 assert.ok(Math.abs(m/row.mean-1)<1e-10,`mean ${JSON.stringify(row)}`);comparisons++;
 for(const [t,value] of row.survivals){assert.ok(Math.abs(S[t]-value)<3e-12,`survival ${t}`);comparisons++;}
}
assert.equal(searchQuantile(searchDistribution(40,20,0,10000),.5),774);
assert.equal(searchQuantile(searchDistribution(40,20,.00168,10000),.5),785);
assert.equal(searchMean(40,20,1),Infinity);
assert.ok(Math.abs(searchMean(40,20,1,0,'gated')-440)<1e-8);
assert.ok(lowMeanRate(40,20).rate>.0016&&lowMeanRate(40,20).rate<.0018);
assert.equal(lowMeanRate(40,40).rate,0);
assert.equal(lowMeanRate(40,20,80).rate,0);
for(const args of [[40,0,.1],[40,20,-1],[40,20,NaN],[40,20,.1,1.5]])assert.throws(()=>searchMean(...args));
assert.throws(()=>searchMean(200,200,.9999));
console.log(JSON.stringify({status:'PASS',fixtures:fixtures.length,numerical_comparisons:comparisons,extra_checks:12}));
