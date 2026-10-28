/* Finite angular spectrum. No network, dependencies, storage, or timers. */
(function(root){
'use strict';
const TAU=2*Math.PI;
function mul(a,b){return [a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]];}
function norm2(a){return a[0]*a[0]+a[1]*a[1];}
function cis(a){return [Math.cos(a),Math.sin(a)];}
function coefficients(width=.025,orders=32,chirp=0,profile='pulse'){
 if(!Number.isFinite(width)||width<.015||width>.15||!Number.isInteger(orders)||orders<1||orders>64||!Number.isFinite(chirp)||Math.abs(chirp)>.1||!['pulse','three'].includes(profile))throw Error('Invalid bounded input');
 const cs=[];let power=0;
 for(let n=-orders;n<=orders;n++){
  const a=profile==='pulse'?Math.exp(-2*Math.PI**2*width**2*n*n):(n===0?1:Math.abs(n)===1?.25:0);
  const c=cis(TAU*chirp*n*n).map(v=>v*a);cs.push({n,c});power+=a*a;
 }
 const scale=1/Math.sqrt(power);return cs.map(({n,c})=>({n,c:c.map(v=>v*scale)}));
}
function residualPhase(n,t,alpha){
 if(!Number.isFinite(t)||Math.abs(t)>4||!Number.isFinite(alpha)||alpha<0||alpha>=1||Math.abs(n*alpha)>=1)throw Error('Mode must propagate; finite t and alpha required');
 const s=Math.sqrt(1-(n*alpha)**2);return -TAU*t*alpha*alpha*n**4/(1+s)**2;
}
function phase(n,t,alpha=0,exact=false){const r=residualPhase(n,t,alpha);return -TAU*t*n*n+(exact?r:0);}
function propagate(cs,t,alpha=0,exact=false){return cs.map(({n,c})=>({n,c:mul(c,cis(phase(n,t,alpha,exact)))}));}
function field(cs,x){let re=0,im=0;for(const {n,c} of cs){const p=TAU*n*x,co=Math.cos(p),si=Math.sin(p);re+=c[0]*co-c[1]*si;im+=c[0]*si+c[1]*co;}return [re,im];}
function intensity(cs,x){return norm2(field(cs,x));}
function fidelity(a,b){
 let re=0,im=0,na=0,nb=0;const bm=new Map(b.map(v=>[v.n,v.c]));
 for(const {n,c} of a){const d=bm.get(n)||[0,0];re+=c[0]*d[0]+c[1]*d[1];im+=c[0]*d[1]-c[1]*d[0];na+=norm2(c);}
 for(const {c} of b)nb+=norm2(c);return (re*re+im*im)/(na*nb);
}
function replicas(p,q){
 if(!Number.isInteger(p)||!Number.isInteger(q)||q<1||q>32)throw Error('Bounded integer fraction required');
 return Array.from({length:q},(_,j)=>{let re=0,im=0;for(let r=0;r<q;r++){const a=TAU*(r*j-p*r*r)/q;re+=Math.cos(a);im+=Math.sin(a);}return [re/q,im/q];});
}
function replicaField(cs,x,p,q){let re=0,im=0;replicas(p,q).forEach((k,j)=>{const a=mul(k,field(cs,x-j/q));re+=a[0];im+=a[1];});return [re,im];}
function incoherentReplicaIntensity(cs,x,p,q){return replicas(p,q).reduce((a,k,j)=>a+norm2(k)*intensity(cs,x-j/q),0);}
function findReturn(cs,alpha){
 const left=.98,right=1,steps=256,score=t=>fidelity(cs,propagate(cs,t,alpha,true));
 const grid=Array.from({length:steps+1},(_,j)=>left+(right-left)*j/steps);
 let i=0;for(let j=1;j<grid.length;j++)if(score(grid[j])>score(grid[i]))i=j;
 let a=grid[Math.max(0,i-1)],b=grid[Math.min(steps,i+1)],g=(Math.sqrt(5)-1)/2;
 let x1=b-g*(b-a),x2=a+g*(b-a),f1=score(x1),f2=score(x2);
 for(let k=0;k<64;k++){if(f1>f2){b=x2;x2=x1;f2=f1;x1=b-g*(b-a);f1=score(x1);}else{a=x1;x1=x2;f1=f2;x2=a+g*(b-a);f2=score(x2);}}
 const candidates=[grid[i],left,right,a,b,x1,x2];let t=candidates[0];for(const c of candidates)if(score(c)>score(t))t=c;
 return {t,fidelity:score(t)};
}
root.TalbotModel={TAU,mul,cis,norm2,coefficients,residualPhase,phase,propagate,field,intensity,fidelity,replicas,replicaField,incoherentReplicaIntensity,findReturn};
})(globalThis);
