'use strict';
const fs=require('node:fs'),path=require('node:path');const {Growth,Probe}=require('./model.js');
const out=path.join(__dirname,'output');fs.mkdirSync(out,{recursive:true});
const seeds=[1,7,23,42,83,1981,1983,2026,31415,65537,987654,4294967295];
const rows=[],samples=[];const started=new Date().toISOString(),tic=performance.now();
for(const boundary of['near','far','tight'])for(const choice of[{name:'DLA p=1',mode:'dla',sticking:1},{name:'DLA p=0.1',mode:'dla',sticking:.1},{name:'Eden',mode:'eden',sticking:1}])for(const seed of seeds){
 const m=new Growth({mode:choice.mode,sticking:choice.sticking,boundary,seed,target:1200});while(!m.reason)m.advance(50000);
 const row={choice:choice.name,boundary,seed,reason:m.reason,...m.metrics(),...m.stats};
 if(seed===1981)samples.push(m.snapshot());
 rows.push(row);
}
const probes=[];
for(const sample of samples.filter(s=>s.options.boundary!=='tight')){
 const m=new Growth(sample.options);for(const[x,y]of sample.points.slice(1))m.add(x,y);
 const p=new Probe(m,{seed:9811983,hits:3000,totalCap:60000000});while(!p.reason)p.advance(50000);
 probes.push({options:sample.options,summary:p.summary()});
}
const summary=[];
for(const boundary of['near','far','tight'])for(const choice of['DLA p=1','DLA p=0.1','Eden']){
 const r=rows.filter(x=>x.boundary===boundary&&x.choice===choice),entry={boundary,choice,runs:r.length,completed:r.filter(x=>x.reason==='target').length};
 for(const field of['rg','radius','diskFill','exposedFraction','cycleRank','moves','lifetimeExpired','anisotropy']){const v=r.map(x=>x[field]).sort((a,b)=>a-b);entry[field]={min:v[0],median:(v[5]+v[6])/2,max:v.at(-1),mean:v.reduce((a,b)=>a+b,0)/v.length};}summary.push(entry);
}
const paired=[];for(const boundary of['near','far','tight']){
 const pairs=seeds.map(seed=>{const r=rows.filter(x=>x.boundary===boundary&&x.seed===seed);return {seed,dla:r[0],partial:r[1],eden:r[2]};});
 paired.push({boundary,dlaGreaterRgThanEden:pairs.filter(x=>x.dla.rg>x.eden.rg).length,partialLowerRgThanDla:pairs.filter(x=>x.partial.rg<x.dla.rg).length,partialGreaterFillThanDla:pairs.filter(x=>x.partial.diskFill>x.dla.diskFill).length,dlaGreaterCycleRankThanEden:pairs.filter(x=>x.dla.cycleRank>x.eden.cycleRank).length,total:pairs.length});
}
const result={started,ended:new Date().toISOString(),elapsedMs:performance.now()-tic,seeds,target:1200,note:'Descriptive finite toy sample; seed pairing is bookkeeping, not matched random paths. Eden ignores diffusion boundary parameters.',summary,paired,rows};
fs.writeFileSync(path.join(out,'ensemble.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(out,'samples.json'),JSON.stringify(samples)+'\n');fs.writeFileSync(path.join(out,'probes.json'),JSON.stringify(probes)+'\n');
console.log(JSON.stringify({runs:rows.length,elapsedMs:result.elapsedMs,paired,summary:summary.map(x=>({boundary:x.boundary,choice:x.choice,completed:x.completed,rg:x.rg,diskFill:x.diskFill,lifetimeExpired:x.lifetimeExpired}))},null,2));
