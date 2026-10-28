/* Lattice growth toy, version 1. No physical time or material calibration. */
(function(root){
'use strict';
const DIRECTIONS=[[1,0],[-1,0],[0,1],[0,-1]];
function random(seed){let a=seed>>>0;return ()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};}
const presets={near:{padding:8,killFactor:2,killMargin:24},far:{padding:20,killFactor:3,killMargin:24},tight:{padding:8,killFactor:1.25,killMargin:10}};
class Growth{
 constructor(options={}){
  this.options={mode:'dla',seed:1981,target:1200,sticking:1,boundary:'near',half:256,walkerCap:100000,totalCap:100000000,...options};
  const o=this.options;
  if(!['dla','eden'].includes(o.mode)||!presets[o.boundary]||!Number.isInteger(o.seed)||o.seed<0||o.seed>4294967295||!Number.isInteger(o.target)||o.target<1||o.target>5000||!Number.isFinite(o.sticking)||o.sticking<=0||o.sticking>1||!Number.isInteger(o.half)||o.half<32||o.half>1024||![o.walkerCap,o.totalCap].every(x=>Number.isSafeInteger(x)&&x>0&&x<=100000000))throw new RangeError('Invalid growth options');
  this.rng=random(o.seed);this.side=2*o.half+1;this.grid=new Uint8Array(this.side*this.side);this.points=[];this.frontier=[];this.frontierIndex=new Map();this.maxR=0;this.walker=null;this.reason=null;
  this.stats={moves:0,iterations:0,launched:0,escaped:0,lifetimeExpired:0,contacts:0,rejected:0,blockedMoves:0};
  this.add(0,0);if(o.target===1)this.reason='target';
 }
 key(x,y){return (y+this.options.half)*this.side+x+this.options.half;}
 occupied(x,y){return Math.abs(x)<=this.options.half&&Math.abs(y)<=this.options.half&&this.grid[this.key(x,y)]===1;}
 adjacent(x,y){return DIRECTIONS.some(([dx,dy])=>this.occupied(x+dx,y+dy));}
 add(x,y){
  if(this.occupied(x,y)||Math.abs(x)>=this.options.half||Math.abs(y)>=this.options.half)throw new Error('Invalid occupied cell');
  const key=this.key(x,y);this.grid[key]=1;this.points.push([x,y]);this.maxR=Math.max(this.maxR,Math.hypot(x,y));
  if(this.frontierIndex.has(key)){const i=this.frontierIndex.get(key),last=this.frontier.pop();this.frontierIndex.delete(key);if(i<this.frontier.length){this.frontier[i]=last;this.frontierIndex.set(last.key,i);}}
  for(const [dx,dy] of DIRECTIONS){const nx=x+dx,ny=y+dy,k=this.key(nx,ny);if(Math.abs(nx)<this.options.half&&Math.abs(ny)<this.options.half&&!this.occupied(nx,ny)&&!this.frontierIndex.has(k)){this.frontierIndex.set(k,this.frontier.length);this.frontier.push({x:nx,y:ny,key:k});}}
 }
 radii(){const b=presets[this.options.boundary];return {launch:Math.max(5,this.maxR+b.padding),kill:Math.max(this.maxR+b.padding+5,this.maxR*b.killFactor+b.killMargin)};}
 spawn(){const r=this.radii();if(r.kill+2>=this.options.half){this.reason='domain';return;}const a=2*Math.PI*this.rng();this.walker={x:Math.round(r.launch*Math.cos(a)),y:Math.round(r.launch*Math.sin(a)),moves:0,kill2:r.kill*r.kill};this.stats.launched++;}
 advance(budget){
  if(!Number.isSafeInteger(budget)||(budget<1||budget>100000))throw new RangeError('Budget must be a positive integer');
  const initial=this.points.length;
  for(let i=0;i<budget&&!this.reason;i++){
   this.stats.iterations++;
   if(this.options.mode==='eden'){
    if(!this.frontier.length){this.reason='domain';break;}
    const p=this.frontier[Math.floor(this.rng()*this.frontier.length)];this.add(p.x,p.y);
   }else{
    if(!this.walker)this.spawn();if(this.reason)break;
    const w=this.walker;
    if(this.adjacent(w.x,w.y)){
     this.stats.contacts++;
     if(this.options.sticking===1||this.rng()<this.options.sticking){this.add(w.x,w.y);this.walker=null;}
     else this.stats.rejected++;
    }
    if(this.walker){
     if(w.moves>=this.options.walkerCap){this.stats.lifetimeExpired++;this.walker=null;continue;}
     if(this.stats.moves>=this.options.totalCap){this.reason='work-cap';break;}
     const [dx,dy]=DIRECTIONS[Math.floor(this.rng()*4)];const nx=w.x+dx,ny=w.y+dy;
     if(!this.occupied(nx,ny)){w.x=nx;w.y=ny;}else this.stats.blockedMoves++;
     w.moves++;this.stats.moves++;
     if(w.x*w.x+w.y*w.y>w.kill2){this.stats.escaped++;this.walker=null;}
    }
   }
   if(this.points.length>=this.options.target)this.reason='target';
  }
  return this.points.length-initial;
 }
 metrics(){
  const n=this.points.length;let sx=0,sy=0,sxx=0,syy=0,sxy=0;
  for(const [x,y] of this.points){sx+=x;sy+=y;sxx+=x*x;syy+=y*y;sxy+=x*y;}
  const cx=sx/n,cy=sy/n,vx=sxx/n-cx*cx,vy=syy/n-cy*cy,xy=sxy/n-cx*cy;
  const trace=vx+vy,diff=Math.hypot(vx-vy,2*xy);
  let edges=0,exposed=0;for(const [x,y] of this.points){edges+=Number(this.occupied(x+1,y))+Number(this.occupied(x,y+1));if(DIRECTIONS.some(([dx,dy])=>!this.occupied(x+dx,y+dy)))exposed++;}
  return {mass:n,radius:this.maxR,rg:Math.sqrt(Math.max(0,trace)),diskFill:n/(Math.PI*(this.maxR+0.5)**2),exposedFraction:exposed/n,edges,cycleRank:edges-n+1,anisotropy:trace?diff/trace:0,frontier:this.frontier.length};
 }
 snapshot(){return {version:1,options:{...this.options},points:this.points.map(p=>p.slice()),stats:{...this.stats},reason:this.reason,metrics:this.metrics()};}
}
/* First-hit probe does not add particles or advance growth RNG. Conditional hits
   are a finite-domain diagnostic, not the harmonic measure from infinity. */
class Probe{
 constructor(growth,{seed=7281983,hits=1000,totalCap=20000000}={}){
  if(!Number.isInteger(seed)||seed<0||seed>4294967295||!Number.isInteger(hits)||hits<1||hits>10000||!Number.isSafeInteger(totalCap)||(totalCap<1||totalCap>100000000))throw new RangeError('Invalid probe options');
  this.model=new Growth({...growth.options,target:5000,sticking:1});
  for(const [x,y] of growth.points.slice(1))this.model.add(x,y);
  this.model.rng=random(seed);this.model.stats={moves:0,iterations:0,launched:0,escaped:0,lifetimeExpired:0,contacts:0,rejected:0,blockedMoves:0};this.model.reason=null;
  this.seed=seed;this.target=hits;this.totalCap=totalCap;this.counts=new Map();this.hits=0;this.reason=null;
 }
 advance(budget){
  if(!Number.isSafeInteger(budget)||(budget<1||budget>100000))throw new RangeError('Budget must be a positive integer');
  const m=this.model;
  for(let i=0;i<budget&&!this.reason;i++){
   m.stats.iterations++;
   if(!m.walker)m.spawn();if(m.reason){this.reason=m.reason;break;}const w=m.walker;
   if(m.adjacent(w.x,w.y)){const k=m.key(w.x,w.y);this.counts.set(k,(this.counts.get(k)||0)+1);this.hits++;m.stats.contacts++;m.walker=null;if(this.hits>=this.target)this.reason='target';continue;}
   if(w.moves>=m.options.walkerCap){m.stats.lifetimeExpired++;m.walker=null;continue;}
   if(m.stats.moves>=this.totalCap){this.reason='work-cap';break;}
   const [dx,dy]=DIRECTIONS[Math.floor(m.rng()*4)];w.x+=dx;w.y+=dy;w.moves++;m.stats.moves++;
   if(w.x*w.x+w.y*w.y>w.kill2){m.stats.escaped++;m.walker=null;}
  }
 }
 summary(){
  const frontier=this.model.frontier,sorted=frontier.slice().sort((a,b)=>(b.x*b.x+b.y*b.y)-(a.x*a.x+a.y*a.y)||a.key-b.key);
  const outer=new Set(sorted.slice(0,Math.ceil(frontier.length/4)).map(p=>p.key));
  const values=frontier.map(p=>this.counts.get(p.key)||0).sort((a,b)=>b-a);const hot=values.slice(0,Math.ceil(frontier.length/10)).reduce((a,b)=>a+b,0);
  const outerHits=[...this.counts].filter(([key])=>outer.has(key)).reduce((s,[,v])=>s+v,0);
  return {seed:this.seed,hits:this.hits,target:this.target,status:this.reason==='target'?'complete':this.reason||'partial',complete:this.reason==='target',reason:this.reason,frontier:frontier.length,visitedSites:this.counts.size,outerSiteFraction:outer.size/frontier.length,outerHitFraction:this.hits?outerHits/this.hits:null,hottestTenPercentShare:this.hits?hot/this.hits:null,stats:{...this.model.stats},counts:[...this.counts]};
 }
}
const api={Growth,Probe,random,presets,DIRECTIONS};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.GrowthLab=api;
})(typeof globalThis!=='undefined'?globalThis:this);
