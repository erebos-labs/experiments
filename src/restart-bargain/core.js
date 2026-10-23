/* Finite search computation, independent browser implementation. No dependencies. */
'use strict';
function solveTri(lower,diag,upper,rhs) {
  const b=diag.slice(), d=rhs.slice(), n=b.length, x=Array(n).fill(0);
  for(let i=1;i<n;i++){const f=lower[i-1]/b[i-1];b[i]-=f*upper[i-1];d[i]-=f*d[i-1];}
  x[n-1]=d[n-1]/b[n-1];
  for(let i=n-2;i>=0;i--) x[i]=(d[i]-upper[i]*x[i+1])/b[i];
  return x;
}
function check(L,s,r,c=0) {
  if(!Number.isInteger(L)||L<1||L>200||!Number.isInteger(s)||s<1||s>L||!Number.isFinite(r)||r<0||r>1||!Number.isInteger(c)||c<0||c>100) throw new Error('Invalid search parameters.');
}
function resolvent(L,s,r,mode,rhs){
  const qs=Array.from({length:L},(_,i)=>1-((mode==='blind'||i+1>s)?r:0));
  const diag=Array(L).fill(1);diag[L-1]-=qs[L-1]/2;
  return solveTri(qs.slice(1).map(q=>-q/2),diag,qs.slice(0,-1).map(q=>-q/2),rhs);
}
function searchMean(L,s,r,c=0,mode='blind'){
  check(L,s,r,c);
  if(mode==='blind'){
    if(r===1)return Infinity;
    const a=resolvent(L,s,r,mode,Array(L).fill(1))[s-1];
    const f=resolvent(L,s,r,mode,[(1-r)/2,...Array(L-1).fill(0)])[s-1];
    if(!f)throw new Error('Success probability underflow; use higher precision.');
    const result=(1+r*c)*a/f;
    if(!Number.isFinite(result))throw new Error('Mean exceeds floating-point range.');
    return result;
  }
  const rates=Array.from({length:L},(_,i)=>i+1>s?r:0);
  const a=resolvent(L,s,r,mode,rates.map(v=>1+v*c));
  const b=resolvent(L,s,r,mode,rates);
  return a[s-1]/(1-b[s-1]);
}
function searchDistribution(L,s,r,H,c=0,mode='blind'){
  check(L,s,r,c);
  if(!Number.isInteger(H)||H<0||H>200000)throw new Error('Invalid time horizon.');
  let p=Array(L+1).fill(0),delay=Array(c).fill(0);p[s]=1;
  const S=[1];
  for(let t=0;t<H;t++){
    const out=Array(L+1).fill(0);
    let resetMass=0;
    for(let i=1;i<=L;i++){
      const ri=(mode==='blind'||i>s)?r:0;
      resetMass+=ri*p[i];
      const m=(1-ri)*p[i]/2;
      if(i>1)out[i-1]+=m;
      out[Math.min(L,i+1)]+=m;
    }
    if(c){out[s]+=delay[0];delay=delay.slice(1);delay.push(resetMass);}
    else out[s]+=resetMass;
    p=out;
    S.push(p.reduce((a,b)=>a+b,0)+delay.reduce((a,b)=>a+b,0));
  }
  return S;
}
function searchQuantile(S,p){const t=S.findIndex(s=>s<=1-p+1e-13);return t<0?null:t;}
function lowMeanRate(L,s,c=0,mode='blind'){
  // Bounded grid plus local refinement, not an analytic global-optimum claim.
  let bestR=0,best=searchMean(L,s,0,c,mode);
  for(let i=1;i<=1000;i++){
    const r=i/4000,m=searchMean(L,s,r,c,mode);
    if(m<best){best=m;bestR=r;}
  }
  const lo=Math.max(0,bestR-.00025),hi=Math.min(.25,bestR+.00025);
  for(let i=0;i<=500;i++){
    const r=lo+(hi-lo)*i/500,m=searchMean(L,s,r,c,mode);
    if(m<best){best=m;bestR=r;}
  }
  return {rate:bestR,mean:best};
}
if(typeof module!=='undefined')module.exports={searchMean,searchDistribution,searchQuantile,lowMeanRate};
