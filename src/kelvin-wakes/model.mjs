// Original bounded implementation of the deep-water Gaussian residue integral.
// Sources and conventions are documented in README.md; no dependencies.
export const KELVIN = Math.asin(1/3);
export const derivativeCoefficient = order => 1/((8*(5+4*order))**0.25*Math.sqrt(Math.PI));
export const C_GAUSS = derivativeCoefficient(0);
export const deg = x => x*180/Math.PI;
export const rad = x => x*Math.PI/180;
export function rayAngle(q) {
  if (!(q >= 1) || !Number.isFinite(q)) throw Error('q must be finite and >= 1');
  return Math.atan(Math.sqrt(q-1)/(2*q-1));
}
export function gaussianSpectrum(K) { return Math.exp(-K*K/(4*Math.PI*Math.PI)); }
export function hardCutoffAngle(fr) {
  if (!(fr>0)) throw Error('positive Fr required');
  return fr <= Math.sqrt(3/(4*Math.PI)) ? KELVIN : rayAngle(2*Math.PI*fr*fr);
}
export function saddleTs(phi) {
  if (!(phi>0 && phi<KELVIN)) return [];
  const s=Math.sin(phi), c=Math.cos(phi), d=Math.sqrt(1-9*s*s);
  // Rationalized transverse root avoids cancellation near the centerline.
  return [2*s/(c+d), (c+d)/(4*s)];
}
export function phase(t,phi,r) {
  return 2*Math.PI*r*(Math.cos(phi)-t*Math.sin(phi))*Math.sqrt(1+t*t);
}
export function saddleTerm(t,phi,r,fr) {
  const q=1+t*t, s=Math.sin(phi), c=Math.cos(phi);
  const s2=2*Math.PI*r*(c-4*s*t)/Math.sqrt(q);
  const amp=q/(fr**4)*gaussianSpectrum(q/(fr*fr))*Math.sqrt(2*Math.PI/Math.abs(s2));
  const ph=phase(t,phi,r)+Math.sign(s2)*Math.PI/4;
  return {amp,re:amp*Math.cos(ph),im:amp*Math.sin(ph)};
}
export function stationary(phi,r,fr) {
  const terms=saddleTs(phi).map(t=>saddleTerm(t,phi,r,fr));
  return {terms,re:terms.reduce((s,x)=>s+x.re,0),im:terms.reduce((s,x)=>s+x.im,0)};
}
export function recommendedN(fr,rmax=11,angleMax=26,tailExponent=30) {
  const qmax=2*Math.PI*fr*fr*Math.sqrt(tailExponent), tmax=Math.sqrt(Math.max(0,qmax-1));
  const need=8*rmax*tmax*(1+2*Math.sin(rad(angleMax))*Math.sqrt(qmax));
  return Math.max(1024,2**Math.ceil(Math.log2(need)));
}
export function prepareQuadrature(fr,n=16384,tailExponent=30) {
  if (!(fr>=0.2 && fr<=5) || !Number.isInteger(n) || n<32 || n>262144 || n%2) throw Error('bounded Fr / even n required');
  const maxQ=2*Math.PI*fr*fr*Math.sqrt(tailExponent);
  const tmax=Math.sqrt(Math.max(0,maxQ-1));
  const dt=2*tmax/n;
  const a=new Float64Array(n+1), bx=new Float64Array(n+1), by=new Float64Array(n+1);
  for(let i=0;i<=n;i++) {
    const t=-tmax+i*dt, q=1+t*t;
    const weight=(i===0||i===n)?1:(i%2?4:2);
    a[i]=weight*dt/3*q/(fr**4)*gaussianSpectrum(q/(fr*fr));
    bx[i]=2*Math.PI*Math.sqrt(q); by[i]=bx[i]*t;
  }
  return {fr,n,tailExponent,tmax,a,bx,by};
}
export function phaseStepBound(prep,phi,r) {
  return 2*Math.PI*r*(Math.abs(Math.cos(phi))+2*Math.abs(Math.sin(phi))*Math.sqrt(1+prep.tmax**2))*2*prep.tmax/prep.n;
}
export function integrate(prep,phi,r,{allowUnderresolved=false}={}) {
  if (!allowUnderresolved && phaseStepBound(prep,phi,r)>Math.PI/2) throw Error('quadrature phase-step bound exceeded');
  const {a,bx,by,fr}=prep, c=Math.cos(phi), s=Math.sin(phi);
  let re=0,im=0,gx=0,gy=0,lap=0;
  for(let i=0;i<a.length;i++) {
    const ph=r*(c*bx[i]-s*by[i]), si=Math.sin(ph),co=Math.cos(ph);
    const kx=bx[i]/(2*Math.PI*fr*fr),ky=-by[i]/(2*Math.PI*fr*fr),k2=kx*kx+ky*ky;
    re+=a[i]*co; im+=a[i]*si;
    gx+=a[i]*kx*co; gy+=a[i]*ky*co; lap-=a[i]*k2*si;
  }
  return {re,im,abs:Math.hypot(re,im),surface:im,gx,gy,slope:Math.hypot(gx,gy),laplacian:lap}; // common pi omitted
}
export function profile(fr,{r0=10,radialSpan=1,radialN=49,angleStep=0.125,angleMax=26,n=null,tailExponent=30}={}) {
  n ??= recommendedN(fr,r0+radialSpan,angleMax,tailExponent);
  const prep=prepareQuadrature(fr,n,tailExponent), values=[];
  for(let j=0;j<=Math.round(angleMax/angleStep);j++) {
    const angle=j*angleStep, phi=rad(angle); let height=0,slope=0,laplacian=0;
    for(let k=0;k<radialN;k++) {
      const r=r0+radialSpan*k/(radialN-1),z=integrate(prep,phi,r);
      height=Math.max(height,Math.abs(z.surface));
      slope=Math.max(slope,z.slope); laplacian=Math.max(laplacian,Math.abs(z.laplacian));
    }
    values.push({angle,height,slope,laplacian});
  }
  const metrics={};
  for(const key of ['height','slope','laplacian']) {
    const peak=Math.max(...values.map(x=>x[key]));
    metrics[key]={peakAngle:values.find(x=>x[key]===peak).angle,peak,
      values:values.map(x=>({angle:x.angle,max:x[key],relative:x[key]/peak}))};
  }
  return {fr,r0,radialSpan,radialN,angleStep,angleMax,n,tailExponent,metrics};
}
export function thresholdIntervals(values,threshold) {
  // Linear crossings of sampled angular profile, including disconnected bands.
  const out=[]; let start=values[0].relative>=threshold?values[0].angle:null;
  for(let i=1;i<values.length;i++) {
    const a=values[i-1],b=values[i], up=a.relative<threshold && b.relative>=threshold,
      down=a.relative>=threshold && b.relative<threshold;
    if(up||down) {
      const x=a.angle+(b.angle-a.angle)*(threshold-a.relative)/(b.relative-a.relative);
      if(up) start=x; else {out.push([start,x]);start=null;}
    }
  }
  if(start!==null) out.push([start,values.at(-1).angle]);
  return out;
}
