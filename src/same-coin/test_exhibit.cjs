'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const lib=require('./exhibit.js');
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let raceCases=0,fixedCases=0;
for(const row of cases){
  const r=lib.race(row.a,row.b,row.h);
  for(const [key,value] of Object.entries(row.race))assert.equal(lib.exact(r[key]),value,`${row.a}/${row.b} h=${row.h} ${key}`);
  raceCases++;
  for(const [n,expected] of Object.entries(row.fixed)){
    const scores=lib.fixed(row.a,row.b,Number(n),row.h);
    for(const [key,value] of Object.entries(expected))assert.equal(lib.exact(scores[key]),value,`${row.a}/${row.b} h=${row.h} n=${n} ${key}`);
    fixedCases++;
  }
}
assert.deepEqual(lib.inspectSequence('hh thh','HHT','THH'),{sequence:'HHTHH',hitsA:[3],hitsB:[5],first:{winner:'A',end:3}});
assert.deepEqual(lib.inspectSequence('HT','HHT','THH'),{sequence:'HT',hitsA:[],hitsB:[],first:null});
assert.deepEqual(lib.inspectSequence('','HHT','THH'),{sequence:'',hitsA:[],hitsB:[],first:null});
assert.throws(()=>lib.inspectSequence('HH<script>','HHT','THH'));
assert.throws(()=>lib.inspectSequence('H'.repeat(201),'HHT','THH'));
assert.throws(()=>lib.race('HHT','HHT'));
assert.throws(()=>lib.race('HHH','TTT',0));
assert.throws(()=>lib.race('HHH','TTT',20));
assert.throws(()=>lib.fixed('HHH','TTT',101));
assert.throws(()=>lib.fixed('HHH','TTT',2));
console.log(`PASS ${raceCases} race cases (${raceCases*5} exact probability/mean assertions)`);
console.log(`PASS ${fixedCases} fixed-horizon cases (${fixedCases*3} exact score assertions)`);
console.log('PASS sequence parsing, first-arrival/count interpretation, and invalid-input checks');
console.log('Arithmetic tests do not verify browser interaction or layout.');
