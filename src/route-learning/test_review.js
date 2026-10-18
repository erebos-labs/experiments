const assert=require('node:assert/strict'),M=require('./model.js');
assert.throws(()=>M.measure(M.MODELS.original,Number.MAX_VALUE,[Number.MAX_VALUE,0,0]),RangeError);
for(const model of Object.values(M.MODELS))for(const demand of [0,model.initial,model.max]){
 const e=M.exactEquilibrium(model,demand);assert(e.costs.every(Number.isFinite));
 const s=M.simulate(model,demand,e.flows,{days:20});assert.equal(s.states.length,21);
}
console.log('PASS arithmetic-overflow rejection and six bounded-model trajectories');

const monotone=M.simulate(M.MODELS.original,1,M.preShortcutSplit(1),{days:20,mode:'gradual',step:.18});
const synchronous=M.simulate(M.MODELS.original,1,M.preShortcutSplit(1),{days:20});
assert.equal(M.lateWindowSpan(synchronous),0);
assert.ok(M.lateWindowSpan(monotone)>.11);
assert.ok(monotone.states.every((s,i,a)=>i===0||s.flows[2]>=a[i-1].flows[2]));
assert.equal(M.oscillationRange(monotone),M.lateWindowSpan(monotone));
assert.throws(()=>M.measure(M.MODELS.original,1,[1,5e-11,-5e-11]),RangeError);
for(const [trace,index]of [[null,2],[{states:Array(2002).fill({flows:[0,0,0]})},2],[{states:[]},-1],[{states:[{flows:[0,0,NaN]}]},2]])assert.throws(()=>M.lateWindowSpan(trace,index),RangeError);
assert.equal(M.lateWindowSpan({states:[]}),0);
console.log('PASS monotonic-span counterexample, strict negative flows and bounded span inputs');
