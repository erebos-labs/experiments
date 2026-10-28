'use strict';
const {Growth,Probe}=require('./model.js'),{solve}=require('./access_solver.js'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');const out=path.join(__dirname,'output');fs.mkdirSync(out,{recursive:true});
const rows=[];const start=performance.now();
for(const target of[1,200,600])for(const boundary of['near','far']){
 const m=new Growth({target,boundary,seed:1981});while(!m.reason)m.advance(50000);
 const reference=solve(m.points,m.radii());assert(reference.sweeps<reference.maxSweeps);assert(reference.residual<1e-10);assert(Math.abs(reference.fluxTotal-1)<1e-6);assert(reference.probabilities.every(p=>p.probability>=-1e-12));
 if(target===1){for(const p of reference.probabilities)assert(Math.abs(p.conditional-.25)<1e-7);}
 const p=new Probe(m,{hits:6000,totalCap:100000000,seed:81983});while(!p.reason)p.advance(50000);assert.equal(p.reason,'target');const mc=p.summary();assert.equal(mc.stats.lifetimeExpired,0,'Observed probe lifetime expirations invalidate this numerical comparison');
 const comparison={target,boundary,solverOuterHitFraction:reference.outerHitFraction,mcOuterHitFraction:mc.outerHitFraction,absoluteDifference:Math.abs(reference.outerHitFraction-mc.outerHitFraction),binomialSE:Math.sqrt(reference.outerHitFraction*(1-reference.outerHitFraction)/mc.hits)};
 assert(comparison.absoluteDifference<5*comparison.binomialSE+.002);
 const calibration=reference.probabilities.map(s=>({...s,hits:p.counts.get(m.key(s.x,s.y))||0}));
 rows.push({comparison,solver:{...reference,probabilities:calibration},probe:{...mc,counts:undefined},points:m.points,radii:m.radii()});console.log(JSON.stringify({comparison,solver:{sweeps:reference.sweeps,residual:reference.residual,fluxTotal:reference.fluxTotal,hit:reference.hit}}));
}
fs.writeFileSync(path.join(out,'access-validation.json'),JSON.stringify({status:'PASS',elapsedMs:performance.now()-start,note:'Six finite geometry cases with zero observed lifetime expirations compare only the outer-quarter hit aggregate, plus solver invariants. Hottest-tenth and full site distributions are not validated by this check. No infinite-domain certification; source uses 65,536 angular bins.',rows},null,2)+'\n');
