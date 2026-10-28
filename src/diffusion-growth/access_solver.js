/* Independent finite-lattice Poisson solve of expected visits per launch.
   This solver does not use Growth.advance or Probe.advance. */
'use strict';
function solve(points,{launch,kill},{sourceSamples=65536,omega=1.85,tolerance=1e-11,maxSweeps=10000}={}){
 if(!Array.isArray(points)||points.length<1||points.length>5000||!Number.isFinite(launch)||!Number.isFinite(kill)||launch<=0||kill<=launch||kill>256||!Number.isInteger(sourceSamples)||sourceSamples<1||sourceSamples>262144||!Number.isFinite(omega)||omega<=0||omega>=2||!Number.isFinite(tolerance)||tolerance<1e-14||tolerance>1e-4||!Number.isInteger(maxSweeps)||maxSweeps<1||maxSweeps>20000||points.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isInteger)||Math.hypot(...p)>=kill))throw new RangeError('Invalid or unbounded finite-grid reference inputs');
 const h=Math.ceil(kill)+2,side=2*h+1,size=side*side,index=(x,y)=>(y+h)*side+x+h;
 const occupied=new Set(points.map(p=>p.join(','))),kind=new Uint8Array(size),u=new Float64Array(size),source=new Float64Array(size),active=[];
 const dirs=[[1,0],[-1,0],[0,1],[0,-1]],offsets=[1,-1,side,-side];
 for(let y=-h+1;y<h;y++)for(let x=-h+1;x<h;x++){
  const k=index(x,y);if(x*x+y*y>kill*kill||occupied.has(x+','+y))continue;
  if(dirs.some(([dx,dy])=>occupied.has((x+dx)+','+(y+dy))))kind[k]=2;
  else {kind[k]=1;active.push(k);}
 }
 for(let a=0;a<sourceSamples;a++){
  const theta=2*Math.PI*(a+.5)/sourceSamples,x=Math.round(launch*Math.cos(theta)),y=Math.round(launch*Math.sin(theta)),k=index(x,y);
  // Every injected sample must be fluid or an immediate perimeter hit. Rounding
  // can otherwise place a nominally valid launch on occupied/outside cells.
  if(kind[k]!==1&&kind[k]!==2)throw new RangeError('Rounded launch source must be unoccupied and inside the kill circle');
  source[k]+=1/sourceSamples;
 }
 let sweeps=0,change=Infinity;
 for(;sweeps<maxSweeps&&change>tolerance;sweeps++){
  change=0;for(const k of active){let sum=0;for(const offset of offsets)sum+=u[k+offset];const expected=source[k]+sum/4,delta=omega*(expected-u[k]);u[k]+=delta;change=Math.max(change,Math.abs(delta));}
 }
 let residual=0,hit=0,escape=0;const probabilities=[];
 for(const k of active){let sum=0;for(const offset of offsets){const nk=k+offset;sum+=u[nk];if(kind[nk]===0)escape+=u[k]/4;}residual=Math.max(residual,Math.abs(u[k]-source[k]-sum/4));}
 for(let k=0;k<size;k++)if(kind[k]===2){let p=source[k];for(const offset of offsets)p+=u[k+offset]/4;hit+=p;probabilities.push({x:k%side-h,y:Math.floor(k/side)-h,probability:p});}
 probabilities.forEach(p=>p.conditional=hit?p.probability/hit:0);
 const sorted=probabilities.slice().sort((a,b)=>(b.x*b.x+b.y*b.y)-(a.x*a.x+a.y*a.y)||(a.y-b.y)||(a.x-b.x)),outer=sorted.slice(0,Math.ceil(sorted.length/4));
 return {side,active:active.length,sourceSamples,omega,tolerance,maxSweeps,sweeps,change,residual,hit,escape,fluxTotal:hit+escape,outerSiteFraction:outer.length/sorted.length,outerHitFraction:outer.reduce((s,p)=>s+p.conditional,0),probabilities};
}
module.exports={solve};
