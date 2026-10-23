(function(root){
  'use strict';
  const INITIAL=Object.freeze([1,.2,-.3,.7]);
  const DT=.01, HORIZON=120;
  function derivative(z,k){
    const [x,y,u,v]=z, a=1-x*x-y*y, b=1-u*u-v*v;
    return [a*x-2*y+k*(u-x),a*y+2*x+k*(v-y),b*u-8*v+k*(x-u),b*v+8*u+k*(y-v)];
  }
  function step(z,k,h=DT){
    const a=derivative(z,k),b=derivative(z.map((v,i)=>v+h*a[i]/2),k);
    const c=derivative(z.map((v,i)=>v+h*b[i]/2),k),d=derivative(z.map((v,i)=>v+h*c[i]),k);
    return z.map((v,i)=>v+h*(a[i]+2*b[i]+2*c[i]+d[i])/6);
  }
  function radii(z){return [Math.hypot(z[0],z[1]),Math.hypot(z[2],z[3])];}
  function phase(z){
    if(Math.min(...radii(z))<1e-6)return null;
    const a=Math.atan2(z[3],z[2])-Math.atan2(z[1],z[0]);
    return Math.atan2(Math.sin(a),Math.cos(a));
  }
  function growth(k){return 1-k+(k>=3?Math.sqrt(k*k-9):0);}
  function trajectory(k,h=DT,horizon=HORIZON,initial=INITIAL){
    if(!Number.isFinite(k)||k<0||k>8)throw new RangeError('Coupling must be between 0 and 8.');
    if(!Number.isFinite(h)||h<.0025||h>.02||!Number.isFinite(horizon)||horizon<0||horizon>120)throw new RangeError('Simulation bounds exceeded.');
    let z=[...initial];const samples=[{t:0,z:[...z]}],n=Math.round(horizon/h);
    const stride=Math.max(1,Math.round(.05/h));
    for(let i=1;i<=n;i++){
      z=step(z,k,h);
      if(!z.every(Number.isFinite))throw new Error('Non-finite numerical state.');
      if(i%stride===0||i===n)samples.push({t:i*h,z:[...z]});
    }
    return samples;
  }
  const api={INITIAL,DT,HORIZON,derivative,step,radii,phase,growth,trajectory};
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.OscillatorModel=Object.freeze(api);
})(typeof window!=='undefined'?window:globalThis);
