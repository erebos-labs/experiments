'use strict';
(()=>{
const O=window.Optics,$=id=>document.getElementById(id);
const inputs=['pairs','error','kind','mode','substrate','seed'];
let cache=null,selected=600,frame=0,lastPlot=null,scalingCache=null;
const pct=x=>x>0&&100*x<.0005?'<0.001%':(100*x).toFixed(3)+'%';
const signed=x=>(x>=0?'+':'')+x.toFixed(3);
const smallR=x=>x<1e-5?x.toExponential(2):pct(x);
function parameters(){
 const seedText=$('seed').value.trim();if(seedText==='')throw Error('Enter a whole-number seed from 0 to 4294967295.');
 const p={m:Number($('pairs').value),error:Number($('error').value)/100,kind:$('kind').value,mode:$('mode').value,seed:Number(seedText),ns:Number($('substrate').value)};
 if(!Number.isInteger(p.seed)||p.seed<0||p.seed>0xffffffff)throw Error('Enter a whole-number seed from 0 to 4294967295.');return p;
}
function markCustom(){document.querySelectorAll('[data-preset]').forEach(x=>x.setAttribute('aria-pressed','false'));}
function queueRebuild(){markCustom();if(frame)cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{frame=0;rebuild();});}
function rebuild(){
 try{
  const params=parameters(),[ordinary,cavity]=O.stacks(params.m,params.error,params.mode,params.seed,1,params.kind);
  const p=O.peak(cavity,1,params.ns),width=O.fwhm(cavity,p.wavelength,p.T,1,params.ns);
  cache={...params,ordinary,cavity,p,width,shift:O.predictedShift(params.m,params.error,params.mode,params.seed),weights:O.sensitivity(params.m)};
  $('pairsOut').textContent=params.m;$('layerCount').textContent=(4*params.m)+' layers in total';$('errorOut').textContent=(100*params.error).toFixed(1)+'%';
  $('modeNote').textContent={independent:'A deterministic random pattern, scaled by the error slider.',mirrored:'Each layer and its reflection partner share the same signed error.',common:'One signed fractional change, shared by every layer.'}[params.mode];
  $('dimensions').textContent=cavity.reduce((s,x)=>s+x.d,0).toFixed(1)+' nm · both stacks';
  for(const [id,layers] of [['ordinaryLayers',ordinary],['cavityLayers',cavity]]){
   $(id).replaceChildren(...layers.map(x=>{const el=document.createElement('span');el.className='chunk '+(x.label==='H'?'high':'low');el.style.flexGrow=x.d;el.style.flexBasis='0';el.textContent=x.label;el.title=`Chunk ${x.token+1}: ${x.label}, n=${x.n.toFixed(5)}, thickness=${x.d.toFixed(4)} nm`;return el;}));
  }
  $('inventory').textContent=`The same ${4*params.m} chunks appear in both rows. Every chunk keeps its actual index and thickness when it moves. H and L name the nominal index families (2.3 and 1.45).`;
  $('errorMessage').textContent='';update();if($('scalingDetails').open)drawScaling();
 }catch(err){$('errorMessage').textContent=err.message+' Last valid stack remains displayed.';}
}
function syncWavelength(w){
 if(!Number.isFinite(w)||w<480||w>720){$('errorMessage').textContent='Choose a wavelength from 480 to 720 nm.';return;}
 selected=w;$('wavelength').value=w;$('wavelengthNumber').value=w.toFixed(9).replace(/0+$/,'').replace(/\.$/,'');
 $('wavelength').setAttribute('aria-valuetext',w.toFixed(6)+' nanometers');$('errorMessage').textContent='';update();if($('scalingDetails').open)drawScaling();
}
function canvasSetup(canvas){
 const rect=canvas.getBoundingClientRect(),w=rect.width,h=rect.height,dpr=Math.min(window.devicePixelRatio||1,2);
 if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
 const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);ctx.font='11px -apple-system, sans-serif';return {ctx,w,h};
}
function axes(ctx,w,h,xlo,xhi,ymax,yLabel,xLabel){
 const box={l:45,r:w-15,t:18,b:h-34};
 ctx.lineWidth=1;ctx.textBaseline='middle';
 for(let i=0;i<=4;i++){
  const y=box.b-(box.b-box.t)*i/4;
  ctx.strokeStyle='#e0e5db';ctx.beginPath();ctx.moveTo(box.l,y);ctx.lineTo(box.r,y);ctx.stroke();
  ctx.fillStyle='#6b7a72';ctx.textAlign='right';const val=ymax*i/4;ctx.fillText(ymax===1?String(Math.round(100*val)):val<10?val.toFixed(1):Math.round(val).toLocaleString('en'),box.l-8,y);
 }
 for(let i=0;i<=4;i++){
  const x=box.l+(box.r-box.l)*i/4,val=xlo+(xhi-xlo)*i/4;
  ctx.fillStyle='#6b7a72';ctx.textAlign=i===4?'right':i===0?'left':'center';ctx.fillText((xhi-xlo)<10?val.toFixed(2):val.toFixed(0),x,box.b+15);
 }
 ctx.textAlign='left';ctx.fillStyle='#61716e';ctx.fillText(yLabel,box.l,6);
 ctx.textAlign='center';ctx.fillText(xLabel,(box.l+box.r)/2,h-3);return box;
}
function curve(ctx,points,x,y,color,dash=[],width=2){
 ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.beginPath();points.forEach((p,i)=>{if(i===0)ctx.moveTo(x(p[0]),y(p[1]));else ctx.lineTo(x(p[0]),y(p[1]));});ctx.stroke();ctx.setLineDash([]);
}
function drawSpectrum(){
 if(!cache)return;const {ctx,w,h}=canvasSetup($('spectrum')),{p,width,cavity,ordinary,ns}=cache;
 let lo=480,hi=720;
 if($('zoom').checked){const half=Math.max(1.5,Math.min(90,(width||15)*5));lo=Math.max(480,p.wavelength-half);hi=Math.min(720,p.wavelength+half);}
 const box=axes(ctx,w,h,lo,hi,1,'Transmission %','Vacuum wavelength · nm'),x=v=>box.l+(v-lo)/(hi-lo)*(box.r-box.l),y=v=>box.b-v*(box.b-box.t);
 const fw=Number($('linewidth').value);
 ctx.save();ctx.beginPath();ctx.rect(box.l,box.t,box.r-box.l,box.b-box.t);ctx.clip();
 if(fw>0){ctx.fillStyle='#c6b58e55';ctx.fillRect(x(selected-fw/2),box.t,x(selected+fw/2)-x(selected-fw/2),box.b-box.t);}
 let ws=Array.from({length:701},(_,i)=>lo+(hi-lo)*i/700);
 if(width!==null)for(let i=-180;i<=180;i++)ws.push(p.wavelength+i*width/24);
 ws.push(p.wavelength,selected);ws=[...new Set(ws.filter(w=>w>=lo&&w<=hi))].sort((a,b)=>a-b);
 curve(ctx,ws.map(w=>[w,O.solve(ordinary,w,1,ns).T]),x,y,'#b7533e',[5,4],1.6);
 curve(ctx,ws.map(w=>[w,O.solve(cavity,w,1,ns).T]),x,y,'#087969',[],2.2);
 if(selected>=lo&&selected<=hi){ctx.strokeStyle='#3e514b';ctx.lineWidth=1;ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(x(selected),box.t);ctx.lineTo(x(selected),box.b);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#087969';ctx.beginPath();ctx.arc(x(selected),y(O.solve(cavity,selected,1,ns).T),4,0,2*Math.PI);ctx.fill();}
 if(p.wavelength>=lo&&p.wavelength<=hi){ctx.strokeStyle='#a46a15';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x(p.wavelength),y(p.T)+1,4.5,0,2*Math.PI);ctx.stroke();}
 ctx.restore();lastPlot={lo,hi,box};
 $('spectrumCaption').textContent=`${$('zoom').checked?'Peak view':'Overview'} · central mode FWHM ${width===null?'not bracketed':width.toFixed(4)+' nm'}. Gold ring: refined peak. Shaded band: incident spectrum FWHM. Click to select a wavelength.`;
}
function drawField(){
 if(!cache)return;const {ctx,w,h}=canvasSetup($('field')),{cavity,ns}=cache,f=O.fieldProfile(cavity,selected,1,ns,32),max=Math.max(...f.map(x=>x.E2)),length=cavity.reduce((s,x)=>s+x.d,0),ymax=Math.max(1,max*1.08);
 const box=axes(ctx,w,h,0,length,ymax,'Relative |E|²','Position in the stack · nm'),x=v=>box.l+v/length*(box.r-box.l),y=v=>box.b-v/ymax*(box.b-box.t);
 let pos=0;for(const layer of cavity){ctx.fillStyle=layer.label==='H'?'#557b7920':'#d6dfce42';ctx.fillRect(x(pos),box.t,x(pos+layer.d)-x(pos),box.b-box.t);pos+=layer.d;}
 curve(ctx,f.map(p=>[p.x,p.E2]),x,y,'#087969',[],1.9);
 const T=O.solve(cavity,selected,1,ns).T,fluxerr=Math.max(...f.map(x=>Math.abs(x.flux-T)));
 $('fieldScale').textContent='Peak |E|²: '+max.toFixed(max<10?3:1)+' × incoming';
 $('fieldMeta').textContent=`Monochromatic field at ${selected.toFixed(4)} nm. Net forward power = ${pct(T)} of incoming power throughout the stack; computed flux variation ≤ ${fluxerr.toExponential(1)}.`;
}
function storyText(band){
 const {error,kind,mode,p,ns,width}=cache,fw=Number($('linewidth').value),atPeak=Math.abs(selected-p.wavelength)<1e-6;
 if(p.at_boundary)return 'The best point in the 540–660 nm search is at its boundary. The central resonance is not certified as resolved.';
 if(fw>0)return `One wavelength at the selected center transmits ${pct(O.solve(cache.cavity,selected,1,ns).T)}; the chosen Gaussian spectrum transmits ${pct(band.T)} in total. The tracked central mode at ${p.wavelength.toFixed(3)} nm has width ${width===null?'unresolved':width.toFixed(3)+' nm'}; the incident spectrum is ${fw.toFixed(1)} nm wide.`;
 if(ns!==1)return `The layer ordering can be symmetric while its surroundings are different. At 600 nm the ideal reordered stack transmits 96%, rather than 100%, into n = 1.5. The reported peak uses the current errors and surroundings.`;
 if(error===0)return `At the design wavelength, reversing the second half opens a resonant window using exactly the same layers. Add errors to see whether the window moves, narrows or gets lower.`;
 if(mode==='mirrored')return `Mirror-paired errors preserve the layer symmetry. This bounded example ${atPeak?'is retuned to':'has a peak at'} ${p.wavelength.toFixed(4)} nm, with reflected power ${smallR(p.R)}. Symmetry does not keep the peak fixed at 600 nm.`;
 if(mode==='common')return `A shared fractional ${kind==='thickness'?'thickness':'index'} change shifts all optical phases together. In this ideal family a full-transmission wavelength survives; the original wavelength can still reflect most of the light.`;
 return `${atPeak?'Retuned.':'Try retuning.'} The central peak moved ${signed(p.wavelength-600)} nm. Its remaining reflected power is ${smallR(p.R)}. ${kind==='thickness'?'Small thickness errors mainly detune this special quarter-wave family; retuned reflected power begins at fourth order.':'Index errors also disturb interface matching; generic small-error retuned reflected power begins at second order.'}`;
}
function update(){
 if(!cache)return;const {ordinary,cavity,ns,p,error,kind,mode,shift}=cache;
 const a=O.solve(ordinary,selected,1,ns),b=O.solve(cavity,selected,1,ns),fw=Number($('linewidth').value),band=O.bandAverage(cavity,selected,fw,1,ns,p);
 $('wavelengthOut').textContent=selected.toFixed(4)+' nm';$('ordinaryT').textContent=pct(a.T);$('cavityT').textContent=pct(b.T);$('peakT').textContent=pct(p.T);$('peakW').textContent=`at ${p.wavelength.toFixed(5)} nm · R ${smallR(p.R)}`;
 $('linewidthOut').textContent=fw.toFixed(1)+' nm';$('bandT').textContent=pct(band.T);$('bandNote').textContent=fw===0?'A single wavelength at the selected center.':`Gaussian power spectrum · ${fw.toFixed(1)} nm FWHM · centered at ${selected.toFixed(3)} nm.`;
 $('story').textContent=storyText(band)+(band.capped?' Integration reached its depth cap; use the numerical report rather than assuming convergence.':'');
 const linear=(error>0&&ns===1)?` First-order shift prediction: ${signed(shift)} nm; computed shift: ${signed(p.wavelength-600)} nm.`:'';
 $('numerics').textContent=`At the selected wavelength, |R + T − 1| = ${b.balance_error.toExponential(2)}. The main model is checked against independent Fresnel recursion, analytic slabs, quarter-wave mirrors, reciprocal transmission and field continuity. Independent tests include mirrored and common errors, unequal surroundings, invalid inputs and a dense-grid check of spectral integration.${linear}`;
 drawSpectrum();drawField();
}
function drawScaling(){
 if(!cache||!$('scalingDetails').open)return;
 const key=[cache.m,cache.mode,cache.seed,cache.ns].join('|');
 if(!scalingCache||scalingCache.key!==key)scalingCache={key,series:O.scalingSeries(cache.m,cache.mode,cache.seed,cache.ns)};
 const {series}=scalingCache,{ctx,w,h}=canvasSetup($('scaling'));
 const nonzero=series.flatMap(s=>s.points.map(p=>p.R)).filter(r=>r>1e-22),loX=Math.log10(.0005),hiX=Math.log10(.064);
 let loY=nonzero.length?Math.max(-24,4*Math.floor((Math.floor(Math.log10(Math.min(...nonzero)))-1)/4)):-24,hiY=0;
 const box={l:51,r:w-15,t:18,b:h-35},x=v=>box.l+(Math.log10(v)-loX)/(hiX-loX)*(box.r-box.l),y=v=>box.b-(Math.log10(Math.max(v,10**loY))-loY)/(hiY-loY)*(box.b-box.t);
 ctx.font='11px -apple-system,sans-serif';ctx.lineWidth=1;
 for(let i=0;i<=4;i++){const pow=loY+(hiY-loY)*i/4,yy=box.b-(box.b-box.t)*i/4;ctx.strokeStyle='#e0e5db';ctx.beginPath();ctx.moveTo(box.l,yy);ctx.lineTo(box.r,yy);ctx.stroke();ctx.fillStyle='#61716e';ctx.textAlign='right';ctx.fillText('1e'+pow.toFixed(0),box.l-8,yy+3);}
 for(const e of [.0005,.002,.008,.064]){ctx.fillStyle='#61716e';ctx.textAlign=e===.064?'right':e===.0005?'left':'center';ctx.fillText((100*e).toFixed(e===.0005?2:1)+'%',x(e),box.b+16);}
 ctx.textAlign='left';ctx.fillText('Reflected power fraction',box.l,8);ctx.textAlign='center';ctx.fillText('Error amplitude · logarithmic',(box.l+box.r)/2,h-2);
 for(const s of series){const color=s.kind==='thickness'?'#087969':'#b7533e';curve(ctx,s.points.map(p=>[p.error,p.R]),x,y,color,s.kind==='index'?[5,4]:[],2);for(const p of s.points){ctx.fillStyle=color;ctx.beginPath();ctx.arc(x(p.error),y(p.R),3,0,Math.PI*2);ctx.fill();}}
 let note='';
 if(cache.ns!==1)note='The surroundings are unequal, so there is nonzero baseline reflection. This view does not apply a zero-baseline quartic or quadratic fit.';
 else if(cache.mode!=='independent')note='This paired or shared-error control retains a near-zero-reflection resonance in the tested range. Values below the display floor are clipped; fitting near-zero roundoff would not measure a physical power law.';
 else note=series.map(s=>`${s.kind==='thickness'?'Thickness':'Index'} fitted small-error slope: ${s.slope===null?'unresolved near numerical precision':s.slope.toFixed(4)}`).join(' · ')+'. Both series use the selected seed and are retuned at every error amplitude.';
 $('scalingNote').textContent=note;
}
$('scalingDetails').addEventListener('toggle',drawScaling);
const defaults={pairs:4,error:0,kind:'thickness',mode:'independent',substrate:1,seed:7,linewidth:0};
function preset(name){
 const p={...defaults};let w=600,zoom=false;
 if(name==='shift'){p.pairs=6;p.error=5;}
 if(name==='index'){p.pairs=6;p.error=5;p.kind='index';}
 if(name==='broad'){p.pairs=8;p.linewidth=1;zoom=true;}
 for(const [key,v]of Object.entries(p))$(key).value=v;
 selected=w;$('wavelength').value=w;$('wavelengthNumber').value=w;$('zoom').checked=zoom;
 document.querySelectorAll('[data-preset]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.preset===name)));
 rebuild();
}
inputs.forEach(id=>$(id).addEventListener('input',queueRebuild));
$('seed').addEventListener('input',()=>{if(!$('seed').value.trim())$('errorMessage').textContent='Enter a whole-number seed from 0 to 4294967295.';});
$('nextSeed').addEventListener('click',()=>{let s=Number($('seed').value);if(!Number.isInteger(s)||s<0||s>0xffffffff)s=7;$('seed').value=(s+2654435769)>>>0;markCustom();rebuild();});
$('wavelength').addEventListener('input',()=>syncWavelength(Number($('wavelength').value)));
$('wavelengthNumber').addEventListener('input',()=>{if(!$('wavelengthNumber').value.trim()){$('errorMessage').textContent='Enter a wavelength from 480 to 720 nm.';return;}syncWavelength(Number($('wavelengthNumber').value));});
$('linewidth').addEventListener('input',()=>{markCustom();update();});$('zoom').addEventListener('change',drawSpectrum);
$('retune').addEventListener('click',()=>syncWavelength(cache.p.wavelength));$('design').addEventListener('click',()=>syncWavelength(600));$('reset').addEventListener('click',()=>preset('open'));
$('spectrum').addEventListener('click',event=>{if(!lastPlot)return;const rect=$('spectrum').getBoundingClientRect(),px=event.clientX-rect.left,{lo,hi,box}=lastPlot;if(px<box.l||px>box.r)return;syncWavelength(lo+(hi-lo)*(px-box.l)/(box.r-box.l));});
for(const button of document.querySelectorAll('[data-preset]'))button.addEventListener('click',()=>preset(button.dataset.preset));
let resizeFrame=0;new ResizeObserver(()=>{if(resizeFrame)cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{resizeFrame=0;drawSpectrum();drawField();drawScaling();});}).observe($('spectrum'));
rebuild();
})();
