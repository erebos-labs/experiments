'use strict';
const $=id=>document.getElementById(id),{Growth,Probe}=GrowthLab;
let models={},running=false,probing=false,probeModels={},showProbe=false,frame=0;
const fmt=x=>x.toLocaleString('en-US'),pct=x=>(100*x).toFixed(1)+'%';
function canProbe(){return models.dla?.reason==='target'&&models.eden?.reason==='target'&&models.dla.points.length===models.eden.points.length&&models.dla.points.length>1;}
function announce(message){$('announcements').textContent=message;}
function clearProbes(){probeModels={};showProbe=false;probing=false;$('probe-box').hidden=true;}
function cancelProbes(){probing=false;for(const p of Object.values(probeModels))if(!p.reason)p.reason='cancelled';}
function options(){const seed=Number($('seed').value);if($('seed').value.trim()===''||!Number.isInteger(seed)||seed<0||seed>4294967295)throw new RangeError('Enter a whole seed from 0 to 4,294,967,295.');return {seed,sticking:Number($('sticking').value),boundary:$('boundary').value,target:Number($('target').value),half:512};}
function error(e){$('error').textContent=e.message;$('error').hidden=false;}
function fromSample(s){const m=new Growth({...s.options,half:512});for(const[x,y]of s.points.slice(1))m.add(x,y);m.stats={...s.stats};m.reason=s.reason;return m;}
function schedule(){if(!frame&&(running||probing))frame=requestAnimationFrame(tick);}
function reset(useRecorded=false){
 try{const o=options();running=false;probing=false;if(frame)cancelAnimationFrame(frame);frame=0;showProbe=false;probeModels={};$('probe-box').hidden=true;$('error').hidden=true;
  models={dla:new Growth({...o,mode:'dla'}),eden:new Growth({...o,mode:'eden',sticking:1})};
  const loaded=[];if(useRecorded)for(const id of['dla','eden']){const s=RECORDED.samples.find(s=>s.options.mode===id&&s.options.seed===o.seed&&s.options.boundary===o.boundary&&(id==='eden'||s.options.sticking===o.sticking)&&s.options.target===o.target);if(s){models[id]=fromSample(s);loaded.push(id);}}
  $('status').textContent=(loaded.length===2?'Recorded pair':loaded.length?'Partly recorded pair':'Ready (no recorded sample)')+' · seed '+o.seed;update();announce($('status').textContent);return true;
 }catch(e){error(e);return false;}
}
function render(id,extent){
 const m=models[id],canvas=$(id),ctx=canvas.getContext('2d'),W=canvas.width,scale=W/(2*extent),pointSize=Math.max(1.2,scale*.86);
 ctx.fillStyle='#f0f1e8';ctx.fillRect(0,0,W,W);ctx.strokeStyle='#dbe0d3';ctx.lineWidth=1;
 for(let i=-extent;i<=extent;i+=20){const v=W/2+i*scale;ctx.beginPath();ctx.moveTo(v,0);ctx.lineTo(v,W);ctx.stroke();ctx.beginPath();ctx.moveTo(0,v);ctx.lineTo(W,v);ctx.stroke();}
 const count=m.points.length;
 for(let i=0;i<count;i++){const[x,y]=m.points[i],t=i/Math.max(1,m.options.target-1);ctx.fillStyle=showProbe?'#91a497':t<.5?'#285a49':`rgb(${Math.round(62+145*(t-.5)*2)},${Math.round(101+15*(t-.5)*2)},${Math.round(71-12*(t-.5)*2)})`;ctx.fillRect(W/2+x*scale-pointSize/2,W/2+y*scale-pointSize/2,pointSize,pointSize);}
 if(showProbe&&probeModels[id]){const p=probeModels[id],max=Math.max(1,...p.counts.values());for(const[k,n]of p.counts){const y=Math.floor(k/p.model.side)-p.model.options.half,x=k%p.model.side-p.model.options.half;ctx.fillStyle=`rgba(211,99,42,${.2+.8*Math.sqrt(n/max)})`;ctx.fillRect(W/2+x*scale-pointSize/2,W/2+y*scale-pointSize/2,pointSize,pointSize);}}
 if(running&&m.walker){ctx.fillStyle='#cf743b';ctx.beginPath();ctx.arc(W/2+m.walker.x*scale,W/2+m.walker.y*scale,2.5,0,Math.PI*2);ctx.fill();}
 ctx.fillStyle='#183e35';ctx.beginPath();ctx.arc(W/2,W/2,2.5,0,Math.PI*2);ctx.fill();$('scale-'+id).textContent='Grid spacing 20 cells · ±'+extent;
 const metric=m.metrics();const mode=showProbe?'Probe mode: amber marks sampled first-hit frequency, not attachment age.':'Attachment-order mode: dark cells are early and amber cells are later.';
 const description=(id==='dla'?'DLA':'Eden')+': '+count+' cells; spread Rg '+metric.rg.toFixed(1)+'. '+mode;
 canvas.setAttribute('aria-label',description);$('description-'+id).textContent=description;
 $(id+'-mass').textContent=fmt(count)+' / '+fmt(m.options.target);
 $('metrics-'+id).innerHTML=`<div><span>Spread Rg</span><strong>${metric.rg.toFixed(1)}</strong></div><div><span>Seed-disk proxy</span><strong>${pct(metric.diskFill)}</strong></div><div><span>Lattice cycles</span><strong>${fmt(metric.cycleRank)}</strong></div>`;
}
function reasonLabel(m){return {target:'mass reached',domain:'domain boundary reached','work-cap':'100M move cap reached'}[m.reason]||'growing';}
function update(){
 for(const id of ['sticking','boundary','target']){
  const select=$(id),label=Array.from(select.options||[]).find(option=>option.value===select.value)?.textContent||select.value;
  $(id+'-current').textContent='Selected: '+label;select.title=label;
 }
 const extent=Math.max(80,Math.ceil((Math.max(models.dla.maxR,models.eden.maxR)+15)/20)*20);for(const id of['dla','eden'])render(id,extent);
 $('dla-subtitle').textContent='Four-way random walk · p = '+models.dla.options.sticking;
 $('age-early').hidden=showProbe;$('age-late').hidden=showProbe;$('legend-mode').textContent=showProbe?'Amber marks first-hit frequency. Growth is frozen; this is not attachment age.':'Dark early, amber late; both plots share a coordinate scale. No physical clock.';
 $('pause').disabled=!running&&!probing;$('pause').textContent=probing?'Cancel probe':'Pause';$('probe').disabled=running||probing||!canProbe();$('probe-availability').textContent=canProbe()?'Both plots reached '+fmt(models.dla.points.length)+' cells; equal-mass probing is ready.':'Finish both plots at the selected mass before probing. Current DLA '+fmt(models.dla.points.length)+', Eden '+fmt(models.eden.points.length)+' cells.';$('grow').disabled=probing;
 $('grow').textContent=models.dla.reason&&models.eden.reason?'Replay this seed':running?'Growing…':'Grow this seed';
 if(probing)updateProbe();
}
function updateProbe(){
 const data=['dla','eden'].map(id=>probeModels[id].summary());$('probe-masses').textContent='Frozen masses: DLA '+fmt(probeModels.dla.model.points.length)+', Eden '+fmt(probeModels.eden.model.points.length)+' cells.';$('probe-status').textContent=probing?'Sampling independent walkers…':data.map((s,i)=>(i?'Eden':'DLA')+': '+fmt(s.hits)+' hits · '+(s.reason==='target'?'sample complete':s.reason)).join(' / ');
 $('probe-results').innerHTML='<div class="probe-stats">'+data.map((s,i)=>`<div><span>${i?'Eden':'DLA'} · outermost quarter of perimeter sites</span><b>${s.hits?pct(s.outerHitFraction):'—'}</b><span>of first hits (uniform-site baseline ${pct(s.outerSiteFraction)})</span><p class="fine">Hottest 10% of sites: ${s.hits?pct(s.hottestTenPercentShare):'—'} of hits; ${fmt(s.visitedSites)} / ${fmt(s.frontier)} sites hit.</p></div>`).join('')+'</div>';
}
function tick(){
 frame=0;
 if(running){for(const id of['dla','eden'])if(!models[id].reason)models[id].advance(id==='eden'?12:30000);if(models.dla.reason&&models.eden.reason){running=false;$('status').textContent='DLA: '+reasonLabel(models.dla)+' · Eden: '+reasonLabel(models.eden);announce($('status').textContent);}else $('status').textContent='Seed '+models.dla.options.seed+' · '+fmt(models.dla.stats.moves)+' walk moves';update();}
 if(probing){for(const id of['dla','eden'])if(!probeModels[id].reason)probeModels[id].advance(40000);showProbe=true;update();if(probeModels.dla.reason&&probeModels.eden.reason){probing=false;updateProbe();announce($('probe-status').textContent);update();}}
 schedule();
}
$('grow').onclick=()=>{if(probing)return;if(models.dla.reason&&models.eden.reason){if(!reset())return;}else if(!running){try{const o=options();if(o.seed!==models.dla.options.seed)if(!reset())return;}catch(e){error(e);return;}}clearProbes();running=true;announce('Growing seed '+models.dla.options.seed);update();schedule();};
$('pause').onclick=()=>{running=false;cancelProbes();if(frame)cancelAnimationFrame(frame);frame=0;if(showProbe)updateProbe();$('status').textContent='Paused · seed '+models.dla.options.seed;announce($('status').textContent);update();};
for(const id of['seed','sticking','boundary','target'])$(id).addEventListener('change',()=>reset(true));
$('next').onclick=()=>{try{const o=options();$('seed').value=(o.seed+1)>>>0;if(reset()){$('grow').click();}}catch(e){error(e);}};
$('probe').onclick=()=>{if(running||probing||!canProbe())return;probeModels={dla:new Probe(models.dla,{seed:9811983,hits:1500}),eden:new Probe(models.eden,{seed:9811983,hits:1500})};probing=true;showProbe=true;$('probe-box').hidden=false;announce('Sampling equal-mass frozen clusters');update();schedule();};
$('show-age').onclick=()=>{cancelProbes();if(frame)cancelAnimationFrame(frame);frame=0;showProbe=false;$('probe-box').hidden=true;update();};
$('export').onclick=()=>{const obj={format:'erebos-growth-v1',exported:new Date().toISOString(),note:'Lattice toy. No physical clock or material calibration.',dla:models.dla.snapshot(),eden:models.eden.snapshot(),probes:Object.fromEntries(Object.entries(probeModels).map(([id,p])=>[id,p.summary()]))};const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='growth-seed-'+models.dla.options.seed+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
const summary=RECORDED.ensemble.summary;
$('ensemble-table').innerHTML=['near','far','tight'].map(boundary=>'<tr><th scope="row">'+boundary+'</th>'+['DLA p=1','DLA p=0.1','Eden'].map(choice=>{const s=summary.find(s=>s.boundary===boundary&&s.choice===choice).rg;return `<td>${s.median.toFixed(1)} <span class="fine">(${s.min.toFixed(1)}–${s.max.toFixed(1)})</span></td>`;}).join('')+'</tr>').join('');
$('ensemble-text').textContent='All 108 runs reached 1,200 cells. Across all 36 seed/circle pairs, DLA spread farther than Eden, and p = 0.1 spread less than p = 1. Changing circles changed DLA shapes; Eden ignores those circles. Its 36 runs repeat 12 distinct seed trajectories, not 36 independent shapes.';
reset(true);
/* Read-only diagnostics for reproducibility and actual browser QA. */
window.labState=()=>({running,probing,showProbe,framePending:frame!==0,options:models.dla.options,dla:models.dla.snapshot(),eden:models.eden.snapshot(),probes:Object.fromEntries(Object.entries(probeModels).map(([id,p])=>[id,p.summary()]))});
