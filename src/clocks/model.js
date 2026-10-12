/* A phase-only toy model, not a biological or mechanical simulation.
   dθ_i = [ω_i + Σ_j w_ij sin(θ_j − θ_i)]dt + √(2D)dW_i.
   Undirected weighted edges; ring edge weight K/2, complete edge K/(N−1).
   Deterministic RK4; Euler–Maruyama with additive independent/common noise.
   Phases stay unwrapped. All units are dimensionless. */
(function(root) {
'use strict';
const TAU = 2*Math.PI;
function rng(seed) {
  let s=seed>>>0;
  return () => {s+=0x6D2B79F5; let t=s; t=Math.imul(t^(t>>>15),t|1); t^=t+Math.imul(t^(t>>>7),t|61); return ((t^(t>>>14))>>>0)/4294967296;};
}
function gaussian(random) {return Math.sqrt(-2*Math.log(Math.max(random(),Number.MIN_VALUE)))*Math.cos(TAU*random());}
function edges(n,kind='ring',K=1) {
  const e=[];
  if(kind==='complete') { for(let i=0;i<n;i++) for(let j=i+1;j<n;j++) e.push([i,j,K/(n-1)]); }
  else { for(let i=0;i<n-1;i++) e.push([i,i+1,K/2]); if(kind!=='open') e.push([n-1,0,K/2]); }
  return e;
}
function drift(theta,edge,omega) {
  const v=theta.map((_,i)=>Array.isArray(omega)?omega[i]:omega);
  for(const [i,j,w] of edge) {const force=w*Math.sin(theta[j]-theta[i]);v[i]+=force;v[j]-=force;}
  return v;
}
function step(theta,edge,omega,dt,D=0,random=Math.random,noiseKind='independent') {
  if(D>0) {
    const v=drift(theta,edge,omega), scale=Math.sqrt(2*D*dt);
    const common=noiseKind==='common'?scale*gaussian(random):0;
    return theta.map((x,i)=>x+dt*v[i]+(noiseKind==='common'?common:scale*gaussian(random)));
  }
  const k1=drift(theta,edge,omega);
  const k2=drift(theta.map((x,i)=>x+dt*k1[i]/2),edge,omega);
  const k3=drift(theta.map((x,i)=>x+dt*k2[i]/2),edge,omega);
  const k4=drift(theta.map((x,i)=>x+dt*k3[i]),edge,omega);
  return theta.map((x,i)=>x+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);
}
function wrap(x) {return ((x+Math.PI)%TAU+TAU)%TAU-Math.PI;}
function metrics(theta,edge,omega=1) {
  const n=theta.length;
  const re=theta.reduce((s,x)=>s+Math.cos(x),0)/n, im=theta.reduce((s,x)=>s+Math.sin(x),0)/n;
  const ringGaps=theta.map((x,i)=>wrap(theta[(i+1)%n]-x));
  const weightedSum=edge.reduce((s,e)=>s+e[2],0);
  const C=weightedSum?edge.reduce((s,[i,j,w])=>s+w*Math.cos(theta[j]-theta[i]),0)/weightedSum:null;
  const energy=edge.reduce((s,[i,j,w])=>s+w*(1-Math.cos(theta[j]-theta[i])),0);
  const v=drift(theta,edge,omega), mean=v.reduce((s,x)=>s+x,0)/n;
  return {R:Math.hypot(re,im),C,q:ringGaps.reduce((s,x)=>s+x,0)/TAU,
    maxGap:Math.max(...ringGaps.map(Math.abs)),energy,
    driftSpread:Math.sqrt(v.reduce((s,x)=>s+(x-mean)**2,0)/n)};
}
function initial(n,kind,seed=7,q=1,perturb=.12) {
  const random=rng(seed);
  return Array.from({length:n},(_,i)=>(kind==='random'?TAU*random():TAU*q*i/n)+perturb*(random()-.5));
}
function simulate({theta,edge,omega=1,dt=.025,T=400,D=0,seed=1,noiseKind='independent',sampleEvery=1,noiseUntil=Infinity}) {
  theta=theta.slice();const random=rng(seed), steps=Math.round(T/dt),stride=Math.max(1,Math.round(sampleEvery/dt));
  const samples=[{t:0,...metrics(theta,edge,omega),theta:theta.slice()}];
  let slips=0, oldQ=Math.round(samples[0].q),lastSlip=0;
  for(let i=1;i<=steps;i++) {
    theta=step(theta,edge,omega,dt,((i-1)*dt<noiseUntil)?D:0,random,noiseKind);
    const q=Math.round(theta.reduce((s,x,j)=>s+wrap(theta[(j+1)%theta.length]-x),0)/TAU);
    if(q!==oldQ){slips+=Math.abs(q-oldQ);lastSlip=i*dt;oldQ=q;}
    if(i%stride===0||i===steps) samples.push({t:i*dt,...metrics(theta,edge,omega),theta:theta.slice()});
  }
  return {theta,samples,slips,lastSlip,final:samples.at(-1)};
}
const api={TAU,rng,gaussian,edges,drift,step,wrap,metrics,initial,simulate};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
else root.Clocks=api;
})(typeof globalThis!=='undefined'?globalThis:this);
