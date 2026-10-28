(function(){
'use strict';
const M=globalThis.TalbotModel,$=id=>document.getElementById(id);
const els={width:$('width'),alpha:$('alpha'),chirp:$('chirp'),profile:$('profile'),distance:$('distance'),mixture:$('mixture')};
let state={width:.025,alpha:.01,chirp:0,profile:'pulse',t:1},cs=M.coefficients(),exactT=1;
const W=420,H=254,N=513;
const spatial=Array.from({length:65},(_,i)=>{const n=i-32;return Array.from({length:W},(_,x)=>M.cis(M.TAU*n*(-1+2*x/(W-1))));});
const colors=[[9,23,37],[18,108,121],[121,203,182],[243,200,117],[255,246,220]];
function color(v){const k=Math.max(0,Math.min(.999999,v))*(colors.length-1),j=Math.floor(k),f=k-j;return colors[j].map((a,i)=>Math.round(a+(colors[j+1][i]-a)*f));}
function read(){
 for(const id of ['chirp','profile']){
  const select=els[id],label=Array.from(select.options||[]).find(option=>option.value===select.value)?.textContent||select.value;
  $(id+'-current').textContent='Selected: '+label;select.title=label;
 }
 state={...state,width:Number(els.width.value),alpha:Number(els.alpha.value),chirp:Number(els.chirp.value),profile:els.profile.value,t:exactT};
 $('width-out').textContent=state.width.toFixed(3);$('alpha-out').textContent=state.alpha.toFixed(3);$('distance-out').textContent=state.t.toFixed(6).replace(/0+$/,'').replace(/\.$/,'')+' zR';
 cs=M.coefficients(state.width,32,state.chirp,state.profile);els.width.disabled=state.profile==='three';
}
function carpet(id,exact){
 const context=$(id).getContext('2d'),img=context.createImageData(W,H);
 const peak=cs.reduce((a,{c})=>a+Math.sqrt(M.norm2(c)),0)**2,den=Math.asinh(peak/2);
 for(let y=0;y<H;y++){
  const row=M.propagate(cs,y/(H-1),state.alpha,exact);
  for(let x=0;x<W;x++){
   let re=0,im=0;
   for(let k=0;k<65;k++){const c=row[k].c,p=spatial[k][x];re+=c[0]*p[0]-c[1]*p[1];im+=c[0]*p[1]+c[1]*p[0];}
   const rgb=color(Math.asinh((re*re+im*im)/2)/den),i=4*(y*W+x);img.data[i]=rgb[0];img.data[i+1]=rgb[1];img.data[i+2]=rgb[2];img.data[i+3]=255;
  }
 }
 context.putImageData(img,0,0);
}
function fraction(){for(const [p,q] of [[0,1],[1,8],[1,4],[1,3],[1,2],[1,1]])if(Math.abs(state.t-p/q)<1e-10)return [p,q];return null;}
function pct(f){return (100*Math.min(1,Math.max(0,f))).toFixed(3)+'%';}
function path(values,max){return values.map((v,i)=>`${(49+578*i/(N-1)).toFixed(2)},${(245-211*v/max).toFixed(2)}`).join(' ');}
function slice(){
 const a=M.propagate(cs,state.t,state.alpha,false),b=M.propagate(cs,state.t,state.alpha,true);
 const ia=[],ib=[],initial=[],mix=[],f=fraction();
 let max=0,delta=0;
 const kernel=f?M.replicas(...f):null;
 for(let i=0;i<N;i++){
  const x=-.5+i/(N-1),va=M.intensity(a,x),vb=M.intensity(b,x),v0=M.intensity(cs,x);
  ia.push(va);ib.push(vb);initial.push(v0);max=Math.max(max,va,vb,v0);
  if(f){const vm=kernel.reduce((sum,k,j)=>sum+M.norm2(k)*M.intensity(cs,x-j/f[1]),0);mix.push(vm);delta=Math.max(delta,Math.abs(vm-va));if(els.mixture.checked)max=Math.max(max,vm);}
 }
 max=Math.max(.1,max*1.08);
 let lines='';
 for(let i=0;i<=4;i++){const y=245-211*i/4;lines+=`<line x1="49" x2="627" y1="${y}" y2="${y}" stroke="#29404d"/><text x="40" y="${y+4}" text-anchor="end">${(max*i/4).toFixed(1)}</text>`;}
 for(let i=0;i<=4;i++){const x=49+578*i/4;lines+=`<text x="${x}" y="267" text-anchor="middle">${(-.5+i/4).toFixed(2)}</text>`;}
 lines+='<text x="338" y="287" text-anchor="middle">position x/d</text><text x="49" y="17">intensity · mean = 1</text>';
 for(const [values,stroke,dash] of [[initial,'#91a8ac','5 5'],[ia,'#61d0bd',''],[ib,'#f1b967','']])lines+=`<polyline points="${path(values,max)}" fill="none" stroke="${stroke}" stroke-width="2" stroke-dasharray="${dash}"/>`;
 const show=Boolean(f&&els.mixture.checked);if(show)lines+=`<polyline points="${path(mix,max)}" fill="none" stroke="#eb96ad" stroke-width="2" stroke-dasharray="2 5"/>`;
 $('slice-plot').innerHTML=lines;$('mixture-key').hidden=!show;
 $('f-para').textContent=pct(M.fidelity(cs,a));$('f-exact').textContent=pct(M.fidelity(cs,b));
 $('phase-gap').textContent=state.profile==='three'?'order absent':M.residualPhase(10,state.t,state.alpha).toFixed(3)+' rad';
 $('para-mark').style.top=(state.t*(H-1)/H*100)+'%';$('exact-mark').style.top=(state.t*(H-1)/H*100)+'%';
 document.querySelectorAll('[data-t]').forEach(btn=>btn.setAttribute('aria-pressed',Math.abs(Number(btn.dataset.t)-state.t)<1e-10?'true':'false'));
 els.mixture.disabled=!f;
 if(f){
  $('replica-tags').innerHTML=kernel.map((k,j)=>M.norm2(k)<1e-20?'':`<span class="tag">shift ${j}/${f[1]} d<br>|K|² ${M.norm2(k).toFixed(3)}<br>phase ${(Math.atan2(k[1],k[0])/Math.PI).toFixed(3)}π</span>`).join('');
  $('mixture-result').textContent=`At τ = ${f[0]}/${f[1]}, max |paraxial intensity − phase-free mixture| = ${delta<1e-10?delta.toExponential(2):delta.toFixed(4)} on 513 samples. ${delta<1e-10?'Agreement here is a useful control, not a general rule.':'Dropping copy phase changes this slice.'}`;
 }else{$('replica-tags').textContent='Select ⅛, ¼, ⅓ or ½ above to inspect the copy weights.';$('mixture-result').textContent='The copy decomposition shown here is for the paraxial branch at the named fractional presets.';}
 if(state.chirp!==0){
  const plus=M.propagate(M.coefficients(state.width,32,.06,state.profile),state.t),minus=M.propagate(M.coefficients(state.width,32,-.06,state.profile),state.t);
  $('twins-result').textContent=`Phase twins: identical input intensity, but current center intensities are ${M.intensity(plus,0).toFixed(3)} (+ phase) and ${M.intensity(minus,0).toFixed(3)} (− phase), using paraxial propagation.`;
 }else{$('twins-result').textContent='Try “Same brightness, hidden phase”, then switch + phase to − phase. The input brightness is identical; the later pattern need not be.';}
 $('status').textContent=state.t===1?'At the full return distance: compare the two lower edges and the field overlaps.':state.t===.5?'At half a return: the paraxial input field shifts sideways by d/2.':state.chirp!==0?'The ± phase inputs are complex conjugates with identical initial intensity.':'The same input spectrum propagates through both models.';
}
function render(rebuild=true){try{$('tuning-result').textContent='';read();if(rebuild){carpet('para-carpet',false);carpet('exact-carpet',true);}slice();$('error').textContent='';}catch(e){$('error').textContent=e.message;}}
function setT(t){exactT=Math.max(0,Math.min(1,t));els.distance.value=String(exactT);render(false);}
for(const name of ['width','alpha','chirp','profile'])els[name].addEventListener('change',()=>render(true));
for(const name of ['width','alpha'])els[name].addEventListener('input',()=>$(name+'-out').textContent=Number(els[name].value).toFixed(3));
els.distance.addEventListener('input',()=>setT(Number(els.distance.value)));els.mixture.addEventListener('change',()=>render(false));
document.querySelectorAll('[data-t]').forEach(btn=>btn.addEventListener('click',()=>setT(Number(btn.dataset.t))));
for(const id of ['para-carpet','exact-carpet'])$(id).addEventListener('click',e=>{const rect=$(id).getBoundingClientRect();setT((e.clientY-rect.top)/rect.height);});
$('retune').addEventListener('click',()=>{const r=M.findReturn(cs,state.alpha);setT(r.t);$('tuning-result').textContent=`Best found within 0.98 ≤ τ ≤ 1: τ = ${r.t.toFixed(9)}, field overlap ${pct(r.fidelity)}. A 257-point scan and local refinement; no unrestricted optimum claim.`;});
const scenarios={return:{width:.025,alpha:.01,chirp:0,t:1,mixture:false},thirds:{width:.12,alpha:.01,chirp:0,t:1/3,mixture:true},twins:{width:.025,alpha:.01,chirp:.06,t:.06,mixture:false},null:{width:.08,alpha:.01,chirp:0,t:.25,mixture:true}};
document.querySelectorAll('[data-scenario]').forEach(btn=>btn.addEventListener('click',()=>{const s=scenarios[btn.dataset.scenario];for(const k of ['width','alpha','chirp'])els[k].value=String(s[k]);els.profile.value='pulse';els.mixture.checked=s.mixture;exactT=s.t;els.distance.value=String(exactT);render(true);}));
render(true);
})();
