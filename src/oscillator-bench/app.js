(()=>{
  'use strict';
  const M=window.OscillatorModel,$=id=>document.getElementById(id);
  const colors=['#ad512c','#246b72'],grid='#dddcd2',muted='#68736b';
  let k=.5,samples=[],t=0,playing=!matchMedia('(prefers-reduced-motion: reduce)').matches,last=0;
  const canvases=['orbits','signal','amplitude'].map($);
  function ctx(canvas){
    const {width,height}=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);
    if(canvas.width!==Math.round(width*d)||canvas.height!==Math.round(height*d)){canvas.width=Math.round(width*d);canvas.height=Math.round(height*d);}
    const c=canvas.getContext('2d');c.setTransform(d,0,0,d,0,0);c.clearRect(0,0,width,height);
    c.font='10px -apple-system, sans-serif';c.lineWidth=1;return {c,w:width,h:height};
  }
  function stateAt(time){return samples[Math.min(samples.length-1,Math.max(0,Math.round(time/.05)))].z;}
  function format(v){return v<.001?(v===0?'0':v.toExponential(1)):v.toFixed(3);}
  function line(c,points,color,width=1.5){if(!points.length)return;c.beginPath();c.moveTo(...points[0]);for(let i=1;i<points.length;i++)c.lineTo(...points[i]);c.strokeStyle=color;c.lineWidth=width;c.stroke();}
  function orbits(z){
    const {c,w,h}=ctx($('orbits')),r=Math.min(w/5.1,88),cy=h/2+2;
    [w*.25,w*.75].forEach((cx,i)=>{
      c.strokeStyle=grid;c.lineWidth=1;c.beginPath();c.arc(cx,cy,r,0,2*Math.PI);c.stroke();
      c.setLineDash([2,4]);c.beginPath();c.moveTo(cx-r-12,cy);c.lineTo(cx+r+12,cy);c.moveTo(cx,cy-r-12);c.lineTo(cx,cy+r+12);c.stroke();c.setLineDash([]);
      c.fillStyle=muted;c.textAlign='center';c.fillText(i===0?'A':'B',cx,cy-r-22);
      c.fillStyle='#899188';c.fillText('reference amplitude = 1',cx,cy+r+23);
      const recent=samples.filter(s=>s.t>=Math.max(0,t-2)&&s.t<=t);
      c.globalAlpha=.5;line(c,recent.map(s=>[cx+r*s.z[i*2],cy-r*s.z[i*2+1]]),colors[i],1.8);c.globalAlpha=1;
      const x=cx+r*z[i*2],y=cy-r*z[i*2+1];
      line(c,[[cx,cy],[x,y]],colors[i],1.3);c.fillStyle=colors[i];c.beginPath();c.arc(x,y,4.5,0,Math.PI*2);c.fill();
    });
    const l=w*.25+r+18,rr=w*.75-r-18;
    if(rr>l){c.setLineDash([3,4]);line(c,[[l,cy],[rr,cy]],'#a5afa0');c.setLineDash([]);}
  }
  function plot(canvas,kind){
    const {c,w,h}=ctx(canvas),left=32,right=10,top=12,bottom=24,pw=w-left-right,ph=h-top-bottom;
    const start=kind==='signal'?Math.max(0,t-20):0,end=kind==='signal'?Math.max(20,t):120;
    const yMin=kind==='signal'?-1.2:0,yMax=1.2;
    const X=time=>left+(time-start)/(end-start)*pw,Y=v=>top+(yMax-v)/(yMax-yMin)*ph;
    c.fillStyle=muted;c.textAlign='right';
    for(const y of kind==='signal'?[-1,0,1]:[0,.5,1]){line(c,[[left,Y(y)],[w-right,Y(y)]],grid,.8);c.fillText(String(y),left-7,Y(y)+3);}
    c.textAlign='center';for(let j=0;j<=4;j++){const time=start+(end-start)*j/4;c.fillText(time.toFixed(0),X(time),h-6);}
    for(let i=0;i<2;i++){
      const data=samples.filter(s=>s.t>=start&&s.t<=Math.min(t,end));
      c.save();c.beginPath();c.rect(left,top,pw,ph);c.clip();
      line(c,data.map(s=>[X(s.t),Y(kind==='signal'?s.z[i*2]:M.radii(s.z)[i])]),colors[i],1.6);c.restore();
    }
    if(kind==='amplitude'){c.setLineDash([3,3]);line(c,[[X(t),top],[X(t),h-bottom]],'#8b9688',1);c.setLineDash([]);}
  }
  function prediction(){
    const g=M.growth(k),boundary=Math.abs(k-1)<1e-9||Math.abs(k-5)<1e-9;
    $('predictionTitle').textContent=boundary?'At a boundary':g<0?'Stable rest':'Unstable rest';
    $('predictionCopy').textContent=boundary?'The linear growth rate is zero. Slow nonlinear decay and finite-run limits matter here.':g<0?'Small disturbances around zero decay in this model. Watch the amplitudes shrink as time passes.':k<1?'The quiet state cannot hold a small disturbance. These weakly coupled rhythms continue to drift.':'The quiet state cannot hold a small disturbance. The oscillators approach a shared rhythm with a phase offset.';
    $('marker').style.left=`${100*k/8}%`;
  }
  function render(){
    const z=stateAt(t),r=M.radii(z),p=M.phase(z);
    $('clock').textContent=`t = ${t.toFixed(2)}`;$('timeValue').textContent=`${t.toFixed(1)} / 120`;$('time').value=String(t);
    $('ampA').textContent=format(r[0]);$('ampB').textContent=format(r[1]);
    $('phase').textContent=p===null?'Undefined':`${(p*180/Math.PI).toFixed(1)}°`;
    $('phase').style.fontSize=p===null?'17px':'';
    $('phaseHint').textContent=p===null?'amplitude below 10⁻⁶':'angle between the rhythms';
    $('play').textContent=playing?'Pause':'Play';
    $('playState').textContent=t>=120?'End of the bounded run · reset or explore another coupling':playing?'Playing · 120 model-time units per run':'Paused · drag the time slider to inspect the run';
    orbits(z);plot($('signal'),'signal');plot($('amplitude'),'amplitude');
  }
  function restart(nextK=k,autoplay=playing){
    k=Math.max(0,Math.min(8,nextK));samples=M.trajectory(k);t=0;playing=autoplay;last=0;
    $('coupling').value=String(k);$('kValue').textContent=k.toFixed(2);
    document.querySelectorAll('[data-k]').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.k)===k)));
    prediction();render();
  }
  $('coupling').addEventListener('input',event=>restart(Number(event.target.value)));
  document.querySelectorAll('[data-k]').forEach(button=>button.addEventListener('click',()=>{restart(Number(button.dataset.k),!matchMedia('(prefers-reduced-motion: reduce)').matches);}));
  function flushCoupling(){const next=Number($('coupling').value);if(next!==k)restart(next,false);}
  $('play').addEventListener('click',()=>{flushCoupling();if(t>=120)t=0;playing=!playing;last=0;render();});
  $('reset').addEventListener('click',()=>{flushCoupling();restart(k,false);});
  $('outcome').addEventListener('click',()=>{flushCoupling();t=120;playing=false;render();});
  $('time').addEventListener('input',event=>{const next=Number(event.target.value);flushCoupling();t=next;playing=false;render();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){playing=false;last=0;render();}});
  new ResizeObserver(()=>render()).observe($('orbits'));
  function frame(now){
    if(playing){if(last)t=Math.min(120,t+Math.min((now-last)/1000,.1)*Number($('speed').value));if(t>=120)playing=false;render();}
    last=now;requestAnimationFrame(frame);
  }
  restart();requestAnimationFrame(frame);
})();
