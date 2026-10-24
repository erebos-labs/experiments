/* Normal-incidence, coherent, lossless multilayers. Independently written here.
   Phasors exp(-i*omega*t), right-to-left (E,H) characteristic matrices.
   Byrnes arXiv:1603.02720v5 supplies Fresnel conventions and power normalization. */
(function(root){
'use strict';
const LAMBDA0=600, NH=2.3, NL=1.45;
const positive=(x,name)=>{if(!Number.isFinite(x)||x<=0)throw Error(name+' must be finite and positive');};
function validate(layers,w,n0,ns){
 positive(w,'wavelength');positive(n0,'n0');positive(ns,'ns');
 if(layers.length>64)throw Error('At most 64 layers');
 for(const x of layers){positive(x.n,'index');if(!Number.isFinite(x.d)||x.d<0)throw Error('Invalid thickness');}
}
function matrix(layers,w){
 let a=1,b=0,c=0,d=1;
 for(const x of layers){let phase=2*Math.PI*x.n*x.d/w,co=Math.cos(phase),si=Math.sin(phase);
  [a,b,c,d]=[a*co-b*x.n*si,a*si/x.n+b*co,c*co+d*x.n*si,d*co-c*si/x.n];}
 return [a,b,c,d];
}
function divide(ar,ai,br,bi){const den=br*br+bi*bi;return [(ar*br+ai*bi)/den,(ai*br-ar*bi)/den];}
function solve(layers,w,n0=1,ns=1){
 validate(layers,w,n0,ns);const [a,b,c,d]=matrix(layers,w);
 const dr=n0*a+ns*d,di=-(n0*ns*b+c);
 const r=divide(n0*a-ns*d,c-n0*ns*b,dr,di),t=divide(2*n0,0,dr,di);
 const R=r[0]**2+r[1]**2,T=ns/n0*(t[0]**2+t[1]**2);
 return {R,T,r,t,balance_error:Math.abs(R+T-1)};
}
function uniformSequence(seed,count){
 if(!Number.isInteger(seed)||seed<0||seed>0xffffffff)throw Error('Seed must be an unsigned 32-bit integer');
 let state=seed, out=[];
 for(let i=0;i<count;i++){state=(Math.imul(1664525,state)+1013904223)>>>0;out.push(2*((state+.5)/4294967296)-1);}
 return out;
}
function stacks(pairs=4,error=0,mode='independent',seed=7,scale=1,kind='thickness'){
 if(!Number.isInteger(pairs)||pairs<1||pairs>8)throw Error('Pairs must be integer 1..8');
 if(!Number.isFinite(error)||error<0||error>.08)throw Error('Error must be in 0..8%');
 if(!['independent','mirrored','common'].includes(mode))throw Error('Unknown correlation');
 if(!['thickness','index'].includes(kind))throw Error('Unknown perturbation');positive(scale,'scale');
 let first=[];for(let i=0;i<pairs;i++)first.push([NH,'H'],[NL,'L']);
 const materials=first.concat([...first].reverse());let u=uniformSequence(seed,4*pairs);
 if(mode==='mirrored')u=u.slice(0,2*pairs).concat(u.slice(0,2*pairs).reverse());
 if(mode==='common')u=u.map(()=>u[0]);
 const cavity=materials.map(([n,label],i)=>({n:kind==='index'?n*(1+error*u[i]):n,d:LAMBDA0/(4*n)*(kind==='thickness'?1+error*u[i]:1)*scale,label,token:i}));
 const ordinary=cavity.slice(0,2*pairs).concat(cavity.slice(2*pairs).reverse());return [ordinary,cavity];
}
function goldenMax(f,left,right,steps=64){
 const g=(Math.sqrt(5)-1)/2;let x1=right-g*(right-left),x2=left+g*(right-left),y1=f(x1),y2=f(x2);
 for(let i=0;i<steps;i++){
  if(y1<y2){left=x1;x1=x2;y1=y2;x2=left+g*(right-left);y2=f(x2);}
  else{right=x2;x2=x1;y2=y1;x1=right-g*(right-left);y1=f(x1);}
 }
 return [[left,f(left)],[right,f(right)],[x1,y1],[x2,y2]].reduce((a,b)=>b[1]>a[1]?b:a);
}
function peak(layers,n0=1,ns=1,lo=540,hi=660,intervals=300){
 if(!Number.isFinite(lo)||!Number.isFinite(hi)||lo<=0||hi<=lo)throw Error('Invalid peak interval');
 if(!Number.isInteger(intervals)||intervals<4||intervals>10000)throw Error('Invalid intervals');
 const f=w=>-solve(layers,w,n0,ns).R;
 const grid=Array.from({length:intervals+1},(_,i)=>lo+(hi-lo)*i/intervals),vals=grid.map(f);
 const candidates=[[grid[0],vals[0]],[grid[intervals],vals[intervals]]];let brackets=0;
 for(let i=1;i<intervals;i++)if(vals[i]>=vals[i-1]&&vals[i]>=vals[i+1]){brackets++;candidates.push(goldenMax(f,grid[i-1],grid[i+1]));}
 const [w]=candidates.reduce((a,b)=>b[1]>a[1]?b:a),s=solve(layers,w,n0,ns);
 return {wavelength:w,T:s.T,R:s.R,at_boundary:w===lo||w===hi,brackets,grid_max_T:1+Math.max(...vals),grid_step:(hi-lo)/intervals};
}
function fwhm(layers,pw,pT,n0=1,ns=1,lo=540,hi=660){
 const f=w=>solve(layers,w,n0,ns).T-pT/2,crossings=[];
 for(const [dir,bound] of [[-1,lo],[1,hi]]){
  let x=pw,step=.0001,cross=null;
  for(let i=0;i<64;i++){
   let y=Math.max(lo,Math.min(hi,pw+dir*step));
   if(f(y)<=0){let a=Math.min(x,y),b=Math.max(x,y);for(let j=0;j<55;j++){let mid=(a+b)/2;if((f(a)>0)===(f(mid)>0))a=mid;else b=mid;}cross=(a+b)/2;break;}
   if(y===bound)break;x=y;step*=1.7;
  }crossings.push(cross);
 }
 return crossings.includes(null)?null:crossings[1]-crossings[0];
}
function fieldProfile(layers,w,n0=1,ns=1,samples=24){
 const s=solve(layers,w,n0,ns);let E=s.t,H=s.t.map(x=>x*ns),offset=layers.reduce((s,x)=>s+x.d,0),sections=[];
 for(const layer of [...layers].reverse()){
  let left=offset-layer.d,points=[];
  for(let j=0;j<=samples;j++){
   let u=layer.d*j/samples,phase=2*Math.PI*layer.n*(layer.d-u)/w,co=Math.cos(phase),si=Math.sin(phase);
   const e=[co*E[0]+si/layer.n*H[1],co*E[1]-si/layer.n*H[0]],h=[co*H[0]+layer.n*si*E[1],co*H[1]-layer.n*si*E[0]];
   points.push({x:left+u,E2:e[0]**2+e[1]**2,flux:(e[0]*h[0]+e[1]*h[1])/n0,E:e,H:h,label:layer.label});
  }
  sections.push(points);E=points[0].E;H=points[0].H;offset=left;
 }
 return sections.reverse().flat();
}
function multiply(X,Y){const[a,b,c,d]=X,[e,f,g,h]=Y;return[a*e-b*g,a*f+b*h,c*e+d*g,d*h-c*f];}
function sensitivity(pairs=4){
 const layers=stacks(pairs)[1],matrices=layers.map(x=>[0,1/x.n,x.n,0]),gs=[];
 for(let j=0;j<layers.length;j++){
  let p=[1,0,0,1];for(let k=0;k<layers.length;k++)p=multiply(p,j===k?[-Math.PI/2,0,0,-Math.PI/2]:matrices[k]);gs.push(p[2]-p[1]);
 }
 let total=gs.reduce((a,b)=>a+b,0);return gs.map(x=>x/total);
}
function predictedShift(pairs,error,mode,seed){
 const layers=stacks(pairs,error,mode,seed)[1],weights=sensitivity(pairs);
 return LAMBDA0*layers.reduce((s,x,i)=>s+weights[i]*(x.n*x.d/(LAMBDA0/4)-1),0);
}
function adaptiveSimpson(f,a,b,tol=1e-10,maxDepth=18){
 let count=0,capped=false;const ev=x=>{count++;return f(x);};
 function rec(a,b,fa,fm,fb,whole,tol,depth){
  let mid=(a+b)/2,l=(a+mid)/2,r=(mid+b)/2,fl=ev(l),fr=ev(r),left=(mid-a)/6*(fa+4*fl+fm),right=(b-mid)/6*(fm+4*fr+fb),delta=left+right-whole;
  if(Math.abs(delta)<=15*tol)return left+right+delta/15;
  if(depth===0){capped=true;return left+right+delta/15;}
  return rec(a,mid,fa,fl,fm,left,tol/2,depth-1)+rec(mid,b,fm,fr,fb,right,tol/2,depth-1);
 }
 let fa=ev(a),fm=ev((a+b)/2),fb=ev(b),value=rec(a,b,fa,fm,fb,(b-a)/6*(fa+4*fm+fb),tol,maxDepth);
 return {value,count,capped};
}
function bandAverage(layers,center,lineFwhm,n0=1,ns=1,p=null,tol=1e-9){
 positive(center,'center');if(!Number.isFinite(lineFwhm)||lineFwhm<0||lineFwhm>10)throw Error('Line FWHM must be in 0..10 nm');
 if(lineFwhm===0)return{T:solve(layers,center,n0,ns).T,evaluations:1,capped:false};
 const sigma=lineFwhm/(2*Math.sqrt(2*Math.log(2))),lo=center-8*sigma,hi=center+8*sigma;if(lo<=0)throw Error('Invalid spectrum');
 p=p||peak(layers,n0,ns);const width=fwhm(layers,p.wavelength,p.T,n0,ns);
 let knots=[lo,hi,center,...[-4,-2,-1,1,2,4].map(s=>center+s*sigma)];
 if(width!==null)knots.push(...[-8,-4,-2,-1,-.5,0,.5,1,2,4,8].map(s=>p.wavelength+s*width));
 knots=[...new Set(knots.filter(x=>x>=lo&&x<=hi))].sort((a,b)=>a-b);
 const f=w=>solve(layers,w,n0,ns).T*Math.exp(-.5*((w-center)/sigma)**2)/(sigma*Math.sqrt(2*Math.PI));
 let total=0,evaluations=0,capped=false;
 for(let i=0;i<knots.length-1;i++){let r=adaptiveSimpson(f,knots[i],knots[i+1],tol/(knots.length-1));total+=r.value;evaluations+=r.count;capped=capped||r.capped;}
 // erf(8/sqrt(2)) differs from one by <1.3e-15.
 return{T:total,evaluations,capped};
}
function scalingSeries(pairs,mode,seed,ns=1){
 const errors=[.0005,.001,.002,.004,.008,.016,.032,.064];
 return ['thickness','index'].map(kind=>{
  const points=errors.map(error=>{const layers=stacks(pairs,error,mode,seed,1,kind)[1],p=peak(layers,1,ns);return {error,R:p.R,wavelength:p.wavelength};});
  let slope=null;
  if(mode==='independent'&&ns===1&&points.slice(0,4).every(p=>p.R>1e-22)){
   const xs=points.slice(0,4).map(p=>Math.log(p.error)),ys=points.slice(0,4).map(p=>Math.log(p.R));
   const mx=xs.reduce((a,b)=>a+b,0)/4,my=ys.reduce((a,b)=>a+b,0)/4;
   slope=xs.reduce((s,x,i)=>s+(x-mx)*(ys[i]-my),0)/xs.reduce((s,x)=>s+(x-mx)**2,0);
  }
  return {kind,points,slope};
 });
}
const api={LAMBDA0,NH,NL,matrix,solve,uniformSequence,stacks,peak,fwhm,fieldProfile,sensitivity,predictedShift,bandAverage,scalingSeries};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Optics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
