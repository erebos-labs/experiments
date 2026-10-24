const O=require('./core.js'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const OUT=path.join(__dirname,'data');
const lines=fs.readFileSync(path.join(OUT,'scaling-slopes.csv'),'utf8').trim().split(/\r?\n/);
const headers=lines.shift().split(','),rows=lines.map(x=>Object.fromEntries(x.split(',').map((v,i)=>[headers[i],v])));
const seeds=[...new Set(rows.map(x=>Number(x.seed)))].slice(0,8);
let checks=0,maxDifference=0;
for(const seed of seeds){
 const series=O.scalingSeries(6,'independent',seed);
 for(const s of series){const expected=Number(rows.find(x=>x.kind===s.kind&&Number(x.seed)===seed).log_log_slope);maxDifference=Math.max(maxDifference,Math.abs(s.slope-expected));assert.ok(Math.abs(s.slope-expected)<1e-4);checks++;}
}
for(const mode of ['mirrored','common'])for(const s of O.scalingSeries(6,mode,7)){assert.equal(s.slope,null);checks++;}
for(const s of O.scalingSeries(6,'independent',7,1.5)){assert.equal(s.slope,null);checks++;}
console.log(JSON.stringify({status:'PASS',checks,seed_count:seeds.length,max_slope_difference:maxDifference,controls:'Paired/shared errors and unequal surroundings suppress the zero-baseline fit'},null,2));
