(function(){
  'use strict';
  const {MODELS,solve,harmInterval}=Braess;
  const $=id=>document.getElementById(id);
  const state={model:'teaching',demand:4,shortcut:false,policy:'selfish',paused:matchMedia('(prefers-reduced-motion: reduce)').matches};
  const num=(x,d=2)=>Number(x).toLocaleString('en-US',{maximumFractionDigits:d});
  const paths=['M57 187 L320 61 L583 187','M57 187 L320 313 L583 187','M57 187 L320 61 L320 313 L583 187'];
  const colors=['#007c75','#63518a','#9b6c00'];
  const ns='http://www.w3.org/2000/svg';
  function drawDots(result){
    $('dots').replaceChildren();
    if(state.paused||result.demand===0)return;
    result.flows.forEach((flow,i)=>{
      const count=Math.min(36,Math.round(flow/result.demand*36));
      for(let j=0;j<count;j++){
        const dot=document.createElementNS(ns,'circle');dot.setAttribute('r','3.1');dot.setAttribute('fill',colors[i]);
        const motion=document.createElementNS(ns,'animateMotion');
        motion.setAttribute('path',paths[i]);motion.setAttribute('dur','10s');motion.setAttribute('begin',`-${j*10/count}s`);motion.setAttribute('repeatCount','indefinite');motion.setAttribute('calcMode','paced');
        dot.append(motion);$('dots').append(dot);
      }
    });
  }
  function drawChart(m){
    const narrow=innerWidth<=760;
    const W=narrow?Math.max(280,Math.min(360,innerWidth-50)):1040,H=narrow?255:280,L=narrow?38:64,R=narrow?12:27,T=31,B=47,w=W-L-R,h=H-T-B;
    $('chart').setAttribute('viewBox',`0 0 ${W} ${H}`);
    $('chart').dataset.geometry=JSON.stringify({W,L,R});
    const [lo,hi]=harmInterval(m);
    const ymax=Math.ceil((m.b+(m.a+m.k)*m.max/2)/20)*20;
    const x=q=>L+q/m.max*w, y=t=>H-B-t/ymax*h;
    const line=(shortcut,policy)=>Array.from({length:241},(_,i)=>{
      const q=m.max*i/240;
      const t=q===0 ? (shortcut?m.s:m.b) : solve(m,q,shortcut,policy).mean;
      return `${i?'L':'M'}${x(q).toFixed(2)} ${y(t).toFixed(2)}`;
    }).join(' ');
    let html=`<rect x="${x(lo)}" y="${T}" width="${x(Math.min(hi,m.max))-x(lo)}" height="${h}" fill="#fae9df"/><text class="chart-text" x="${x((lo+Math.min(hi,m.max))/2)}" y="19" text-anchor="middle" style="fill:#87331f">${narrow?'Selfish harm':'Shortcut hurts at selfish equilibrium'}</text>`;
    for(let t=0;t<=ymax;t+=ymax/4) html+=`<line x1="${L}" x2="${W-R}" y1="${y(t)}" y2="${y(t)}" stroke="#d6ddd5" stroke-width="1"/><text class="chart-text" x="${L-12}" y="${y(t)+4}" text-anchor="end">${num(t,0)}</text>`;
    for(let q=0;q<=m.max;q+=m.max/4)html+=`<text class="chart-text" x="${x(q)}" y="${H-B+23}" text-anchor="middle">${num(q)}</text>`;
    html+=`<text class="chart-text" x="${L}" y="19">${narrow&&m.id==='original'?'t.u.':m.unit}</text><text class="chart-text" x="${W-R}" y="${H-5}" text-anchor="end">demand · flow units</text>`;
    html+=`<path class="chart-line" stroke="#203a3c" stroke-dasharray="7 5" d="${line(false,'selfish')}"/><path class="chart-line" stroke="#b7462d" d="${line(true,'selfish')}"/><path class="chart-line" stroke="#007c75" d="${line(true,'coordinated')}"/>`;
    html+=`<line x1="${x(state.demand)}" x2="${x(state.demand)}" y1="${T}" y2="${H-B}" stroke="#53686b" stroke-dasharray="3 5"/>`;
    for(const [s,p,c] of [[false,'selfish','#203a3c'],[true,'selfish','#b7462d'],[true,'coordinated','#007c75']]){
      const r=solve(m,state.demand,s,p);if(r.mean!==null)html+=`<circle cx="${x(state.demand)}" cy="${y(r.mean)}" r="5" fill="${c}" stroke="#fffefa" stroke-width="2"/>`;
    }
    $('chart-content').innerHTML=html;
    $('chart-desc').textContent=`${m.name}. The closed shortcut curve rises steadily. With selfish routing the shortcut worsens mean time for demand strictly between ${num(lo)} and ${num(hi)} flow units. Coordinated routing never exceeds the closed shortcut curve. Current demand ${num(state.demand)}.`;
    $('chart-note').textContent=`Shading: ${num(lo)} < demand < ${num(hi)}. Boundaries tie. At high demand the selfish flow abandons the shortcut. All three curves are analytic. At zero, the curves show limits, not an observed journey. Tap the plot to set demand.`;
  }
  function render(){
    const m=MODELS[state.model],q=state.demand;
    const current=solve(m,q,state.shortcut,state.policy),base=solve(m,q,false,'selfish');
    $('model').value=state.model;$('demand').max=m.max;$('demand').value=q;
    $('demand-value').value=num(q);$('max-demand').textContent=m.max;
    $('demand').setAttribute('aria-valuetext',`${num(q)} ${m.demandUnit}`);
    $('demand-unit').textContent=m.id==='teaching' ? `${num(q*1000,0)} modeled drivers in a fixed window. One flow unit = 1,000; not a measured road capacity.` : 'Abstract stationary flow, in the original paper’s arbitrary units. These units are not thousands of real cars.';
    $('model-caption').textContent=m.id==='teaching'?'Cornell chapter 8, rescaled to thousands. Shortcut: 0 minutes.':'Original affine costs, in abstract time units. Shortcut: 10 + its flow.';
    $('shortcut').setAttribute('aria-pressed',state.shortcut);
    $('shortcut-label').textContent=state.shortcut?'A → B shortcut is open':'Build the A → B shortcut';
    $('map-state').textContent=state.shortcut?'Shortcut open':'Shortcut closed';
    ['selfish','coordinated'].forEach(id=>$(id).setAttribute('aria-pressed',state.policy===id));
    $('policy-caption').textContent=state.policy==='selfish'?'Exact user equilibrium: no infinitesimal driver can switch to a quicker route.':'Exact minimum mean journey: a controller assigns flows to minimize total travel time.';
    $('motion').textContent=state.paused?'Animate dots':'Pause dots';$('motion').setAttribute('aria-pressed',state.paused);
    $('cost-head').textContent=`Time · ${m.unit}`;
    for(let i=0;i<5;i++){
      const closed=i===4&&!state.shortcut;
      $('e'+i).classList.toggle('active',!closed&&current.edges[i]>1e-10);
      $('e'+i).classList.toggle('closed',closed);
      $('et'+i).textContent=closed?'Closed':`${num(current.edgeTimes[i])} ${m.id==='original'?'t.u.':m.unit}`;
      $('ef'+i).textContent=closed?'no flow':`flow ${num(current.edges[i])}`;
    }
    $('shortcut-arrow').style.display=state.shortcut?'':'none';
    $('network-description').textContent=`${m.name}, demand ${num(q)}. Directed routes S to A to T, S to B to T, and ${state.shortcut?'open':'closed'} A to B shortcut. ${state.policy} routing. Road times ${current.edgeTimes.map(x=>num(x)).join(', ')} ${m.unit}; flows ${current.edges.map(x=>num(x)).join(', ')}. Detailed route allocations follow the map.`;
    for(let i=0;i<3;i++){
      $('f'+i).textContent=num(current.flows[i]);
      $('c'+i).textContent=current.costs[i]===null?'closed':num(current.costs[i]);
      $('f'+i).classList.toggle('unused',current.flows[i]<1e-10);
      $('c'+i).classList.toggle('unused',current.flows[i]<1e-10);
    }
    const metric=x=>x===null?'—':`${num(x)} <small>${m.unit}</small>`;
    $('mean').innerHTML=metric(current.mean);$('baseline').innerHTML=metric(base.mean);
    const d=$('delta');d.className='delta';
    if(q===0)d.textContent='No traffic, no journey average. All flows are zero.';
    else if(!state.shortcut)d.textContent='Shortcut closed. The traffic splits evenly over the two outer routes.';
    else{
      const diff=current.mean-base.mean;
      if(diff>1e-8){d.classList.add('hurt');d.textContent=`${num(diff)} ${m.unit} slower per driver (+${num(diff/base.mean*100,1)}%). The extra road hurts at this demand.`;}
      else if(diff< -1e-8){d.classList.add('help');d.textContent=`${num(-diff)} ${m.unit} faster on average (${num(-diff/base.mean*100,1)}% saved). The shortcut helps at this demand.`;}
      else d.textContent=`Same mean journey as before. ${current.flows[2]<1e-10?'The shortcut carries no flow.':'The shortcut carries flow, but there is no net benefit.'}`;
    }
    const lohi=harmInterval(m);
    $('lure').textContent=m.id==='teaching'?'At demand 4, the closed road gives 65 minutes. The empty shortcut route initially offers 40. Once all 4 units take it, both congestible roads carry the whole crowd: the new equilibrium is 80 minutes.':'At demand 6, the closed road gives 83 time units. An empty shortcut route offers 70. At the new equilibrium, 2 units use each route and every driver takes 92 time units.';
    $('escape').textContent=`At low demand the shortcut saves time. At demand ${num(lohi[1])} or more, selfish drivers avoid it. Under coordinated routing, adding an optional road can never raise the best mean: the controller can always keep the old allocation.`;
    $('model-detail').textContent=m.id==='teaching'?'Teaching costs: S→A and B→T take 10x minutes, where x is edge flow in thousands; S→B and A→T take 45 minutes regardless of flow; A→B takes 0. Demand range: 0–12 thousand modeled drivers. The zero-time road and zero free-flow time on congestible roads are deliberate simplifications.':'Original costs: S→A and B→T take 10x; S→B and A→T take 50+x; A→B takes 10+x. Values are abstract time units and x is abstract stationary flow. Demand range: 0–20. This preserves the original numerical example, while the coordinated objective below is explicitly total/mean time.';
    const errors=[Math.abs(current.flows.reduce((s,x)=>s+x,0)-q),Math.abs(current.edges[0]+current.edges[2]-q),Math.abs(current.edges[1]+current.edges[3]-q),Math.abs(current.edges[0]-current.edges[1]-current.edges[4]),Math.abs(current.edges[2]+current.edges[4]-current.edges[3])];
    $('conservation').textContent=`Largest mismatch: ${Math.max(...errors).toExponential(1)} flow units`;
    $('residual').textContent=`${(state.policy==='selfish'?current.regret:current.optimalResidual).toExponential(1)} ${m.unit}`;
    $('residual-caption').textContent=state.policy==='selfish'?'Equilibrium residual: largest used-route time minus the cheapest available route.':'Optimality residual: largest used-route marginal total cost minus the cheapest available marginal total cost.';
    $('incentive').textContent=q===0?'At zero demand, equilibrium and optimality conditions have no used routes to test.':state.policy==='selfish'?`No used stream has a faster alternative at these fixed edge flows (largest possible infinitesimal gain: ${num(current.regret,6)} ${m.unit}).`:`A driver assigned to the slowest used route could save up to ${num(current.regret)} ${m.unit} by switching alone. This personal incentive is why coordination may need enforcement or incentives. The optimized average is not a guarantee of equal journey times.`;
    drawDots(current);drawChart(m);
  }
  function presets(){
    const m=MODELS[state.model];$('presets').replaceChildren();
    const labels=m.id==='teaching'?['Low · 2','Classic · 4','Peak · 4.5','High · 10']:['Low · 2','Classic · 6','Mixed · 8','High · 20'];
    m.presets.forEach((q,i)=>{const b=document.createElement('button');b.textContent=labels[i];b.type='button';b.addEventListener('click',()=>{state.demand=q;render();});$('presets').append(b);});
  }
  $('model').addEventListener('change',()=>{state.model=$('model').value;state.demand=MODELS[state.model].initial;presets();render();});
  $('demand').addEventListener('input',()=>{state.demand=Number($('demand').value);render();});
  $('shortcut').addEventListener('click',()=>{state.shortcut=!state.shortcut;render();});
  ['selfish','coordinated'].forEach(id=>$(id).addEventListener('click',()=>{state.policy=id;render();}));
  $('motion').addEventListener('click',()=>{state.paused=!state.paused;render();});
  $('reset').addEventListener('click',()=>{Object.assign(state,{model:'teaching',demand:4,shortcut:false,policy:'selfish',paused:matchMedia('(prefers-reduced-motion: reduce)').matches});presets();render();});
  $('chart').addEventListener('click',event=>{
    const bounds=$('chart').getBoundingClientRect(),{W,L,R}=JSON.parse($('chart').dataset.geometry),vx=(event.clientX-bounds.left)/bounds.width*W;
    if(vx<L||vx>W-R)return;
    const m=MODELS[state.model];state.demand=Math.max(0,Math.min(m.max,Math.round((vx-L)/(W-L-R)*m.max*20)/20));render();
  });
  addEventListener('resize',()=>drawChart(MODELS[state.model]));
  presets();render();
})();
