/* Exact stationary, nonatomic symmetric Braess models. No iterative solver. */
(function (root) {
  'use strict';
  const MODELS = Object.freeze({
    teaching: Object.freeze({id:'teaching', name:'Teaching model', a:10, b:45, k:0, s:0, h:0, max:12, initial:4, unit:'min', demandUnit:'thousand modeled drivers', presets:[2,4,4.5,10]}),
    original: Object.freeze({id:'original', name:'Braess’s original model', a:10, b:50, k:1, s:10, h:1, max:20, initial:6, unit:'time units', demandUnit:'abstract flow units', presets:[2,6,8,20]})
  });
  const clamp = (x,lo,hi) => Math.max(lo,Math.min(hi,x));
  function measure(model, flows, shortcut) {
    const [u,v,z] = flows;
    const {a,b,k,s,h} = model;
    const edges = [u+z,u,v,v+z,z]; // S→A, A→T, S→B, B→T, A→B
    const edgeTimes = [a*edges[0],b+k*edges[1],b+k*edges[2],a*edges[3],s+h*z];
    const costs = [edgeTimes[0]+edgeTimes[1],edgeTimes[2]+edgeTimes[3],shortcut ? edgeTimes[0]+edgeTimes[4]+edgeTimes[3] : null];
    const demand = u+v+z;
    const total = flows.reduce((sum,f,i)=>sum+f*(costs[i] ?? 0),0);
    const minimum = Math.min(...costs.filter(x=>x !== null));
    const regret = demand === 0 ? 0 : Math.max(0,...flows.map((f,i)=>f>1e-10 ? costs[i]-minimum : 0));
    const gap = demand === 0 ? 0 : (total-demand*minimum)/demand;
    const marginal = [2*a*edges[0]+b+2*k*edges[1], b+2*k*edges[2]+2*a*edges[3], shortcut ? 2*a*(edges[0]+edges[3])+s+2*h*z : null];
    const mmin = Math.min(...marginal.filter(x=>x!==null));
    const optimalResidual = demand===0 ? 0 : Math.max(0,...flows.map((f,i)=>f>1e-10 ? marginal[i]-mmin : 0));
    return {flows,edges,edgeTimes,costs,demand,total,mean:demand===0?null:total/demand,regret,gap,optimalResidual};
  }
  function solve(model,demand,shortcut,policy='selfish') {
    if (!model || !Number.isFinite(demand) || demand<0 || !['selfish','coordinated'].includes(policy)) throw new RangeError('Invalid model, demand or policy');
    const {a,b,k,s,h} = model;
    const divisor = a+k+2*h;
    const z = shortcut ? clamp(((policy==='selfish'?2:1)*(b-s)-(a-k)*demand)/divisor,0,demand) : 0;
    const side = (demand-z)/2;
    return measure(model,[side,side,z],shortcut);
  }
  function harmInterval(model) {
    // Compare all-shortcut cost (2a+h)q+s to old b+(a+k)q/2.
    const lower = (model.b-model.s)/((3*model.a-model.k)/2+model.h);
    const upper = 2*(model.b-model.s)/(model.a-model.k);
    return [lower,upper];
  }
  const api = {MODELS,solve,measure,harmInterval};
  if (typeof module!=='undefined' && module.exports) module.exports=api;
  else root.Braess=api;
})(typeof globalThis!=='undefined'?globalThis:this);
