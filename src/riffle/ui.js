"use strict";
(() => {
  const data = JSON.parse(document.getElementById("experiment-data").textContent);
  const byId = id => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";
  const colors = {deck_tv:"#bc4b31", visible_descents_tv:"#197368", top_card_tv:"#5756a8", separation:"#8b6b23"};
  let k = 5, example = 0;
  function svgNode(parent, tag, attrs = {}, text) {
    const child = document.createElementNS(NS, tag);
    for (const [name, value] of Object.entries(attrs)) child.setAttribute(name, value);
    if (text !== undefined) child.textContent = text;
    parent.appendChild(child); return child;
  }
  function frame(id, height, xlabel, ylabel, ymax, xticks) {
    const svg = byId(id), width = Math.max(250, svg.clientWidth);
    svg.replaceChildren(); svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    const p = {l:52,r:16,t:14,b:43}, w=width-p.l-p.r, h=height-p.t-p.b;
    const x = v => p.l + v / xticks.at(-1) * w, y = v => p.t + h * (1-v/ymax);
    for (let i=0; i<=4; i++) {
      const value = i*ymax/4;
      svgNode(svg,"line",{x1:p.l,x2:width-p.r,y1:y(value),y2:y(value),class:"grid"});
      svgNode(svg,"text",{x:p.l-8,y:y(value)+4,"text-anchor":"end"}, ymax===1 ? value.toFixed(2) : value.toFixed(2));
    }
    for (const value of xticks) svgNode(svg,"text",{x:x(value),y:height-p.b+18,"text-anchor":"middle"},value);
    svgNode(svg,"line",{x1:p.l,x2:width-p.r,y1:y(0),y2:y(0),class:"axis"});
    svgNode(svg,"text",{x:p.l+w/2,y:height-3,"text-anchor":"middle"},xlabel);
    svgNode(svg,"text",{x:13,y:p.t+h/2,transform:`rotate(-90,13,${p.t+h/2})`,"text-anchor":"middle"},ylabel);
    return {svg,x,y,width,height,w,h,p};
  }
  function drawMixing() {
    const small = byId("mixing-plot").clientWidth < 480;
    const f = frame("mixing-plot",small?260:290,"Number of ideal riffles","Distance to uniform",1,small?[0,4,8,14]:[0,2,4,6,8,10,12,14]);
    const keys = ["deck_tv","visible_descents_tv","top_card_tv"];
    if (byId("show-separation").checked) keys.push("separation");
    svgNode(f.svg,"line",{x1:f.x(k),x2:f.x(k),y1:f.y(0),y2:f.y(1),stroke:"#6b7b74","stroke-dasharray":"3 4"});
    for (const key of keys) {
      const path = data.rows.map((r,i)=>`${i?"L":"M"}${f.x(r.k)},${f.y(r[key])}`).join(" ");
      svgNode(f.svg,"path",{d:path,fill:"none",stroke:colors[key],"stroke-width":key==="deck_tv"?2.8:2,"stroke-dasharray":key==="separation"?"5 3":key==="top_card_tv"?"2 3":"none"});
      svgNode(f.svg,"circle",{cx:f.x(k),cy:f.y(data.rows[k][key]),r:4.5,fill:colors[key],stroke:"#f6f5ef","stroke-width":1.5});
    }
  }
  function histogram(id, probs, color) {
    const current=data.rows[k];
    const ymax=Math.max(.2,Math.ceil(20*Math.max(...current.visible_descents_probability,...current.inverse_descents_probability,...current.uniform_probability))/20);
    const f=frame(id,245,"Number of downward steps","Probability",ymax,[0,13,26,39,51]);
    // Both facets share a y scale at the selected shuffle count.
    const barWidth=f.w/52*.86;
    data.rows[k].uniform_probability.forEach((v,i)=>svgNode(f.svg,"rect",{x:f.x(i)-barWidth/2,y:f.y(v),width:barWidth,height:f.y(0)-f.y(v),class:"uniform"}));
    const path=probs.map((v,i)=>`${i?"L":"M"}${f.x(i)},${f.y(v)}`).join(" ");
    svgNode(f.svg,"path",{d:path,fill:"none",stroke:color,"stroke-width":2.2});
    svgNode(f.svg,"text",{x:f.width-f.p.r,y:26,"text-anchor":"end",fill:color},`peak ${Math.max(...probs).toFixed(3)}`);
  }
  function sampleDeck() {
    let seed = (20261015 + k*7919 + example*104729) >>> 0;
    const random=()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;};
    const labels=Array.from({length:52},()=>Math.floor(random()*2**k));
    const inv=Array.from({length:52},(_,i)=>i).sort((i,j)=>labels[i]-labels[j] || i-j);
    const deck=Array(52); inv.forEach((card,pos)=>deck[card]=pos);
    const desc = d => d.slice(1).reduce((n,v,i)=>n+(d[i]>v),0);
    byId("sample-deck").replaceChildren(...deck.map(v=>{
      const card=document.createElement("span");card.className="card";
      card.dataset.band=Math.floor(v/13); card.textContent=v+1;return card;
    }));
    byId("sample-counts").textContent=`${desc(deck)} neighbor descents · ${desc(inv)} inverse descents · sample ${example+1}`;
  }
  function update() {
    const row=data.rows[k];
    byId("shuffle-count").textContent=k;
    byId("shuffles").value=k;
    byId("deck-value").textContent=row.deck_tv.toFixed(3);
    byId("visible-value").textContent=row.visible_descents_tv.toFixed(3);
    byId("top-value").textContent=row.top_card_tv.toFixed(3);
    document.querySelectorAll("button[data-k]").forEach(b=>b.setAttribute("aria-pressed",Number(b.dataset.k)===k));
    const ev=row.optimal_event;
    byId("event-detail").textContent=`An optimal test asks whether there are at most ${ev.inverse_descents_at_most} inverse descents. This happens with probability ${(100*ev.under_shuffle).toFixed(2)}% after these riffles and ${(100*ev.under_uniform).toFixed(2)}% under uniform shuffling. The gap is ${(100*row.deck_tv).toFixed(2)} percentage points.`;
    byId("visible-mean").textContent=`mean ${row.visible_mean.toFixed(2)}`;
    byId("hidden-mean").textContent=`mean ${row.hidden_mean.toFixed(2)}`;
    const cond=data.typical_visible_condition.find(r=>r.k===k);
    byId("conditional-detail").textContent=cond?.possible ? `Keep only decks with 25 or 26 neighbor descents. This occurs ${(100*cond.event_probability_shuffled).toFixed(2)}% of the time after ${k} riffles, versus 36.81% under uniform shuffling. Even within this ordinary-looking subset, whole-deck TV is ${cond.conditional_deck_tv.toFixed(3)}.` : k===0 ? "The unshuffled deck has no descents. The subset with 25 or 26 neighbor descents is impossible at zero riffles." : "The conditional calculation was recorded for 1–12 riffles; move back to that range to inspect it.";
    const r7=data.rows[7];
    byId("rare-detail").textContent=`At seven riffles the exact starting order is ${Math.round(r7.identity_likelihood_ratio).toLocaleString()} times as likely as under uniform shuffling, while the reverse order is only ${r7.reverse_order_likelihood_ratio.toExponential(3)} times as likely. These individual orders are extremely rare in absolute terms. That is why separation can be ${r7.separation.toFixed(6)} while whole-deck TV is only 0.334.`;
    drawMixing(); histogram("visible-plot",row.visible_descents_probability,colors.visible_descents_tv);
    histogram("hidden-plot",row.inverse_descents_probability,colors.deck_tv);sampleDeck();
  }
  byId("shuffles").addEventListener("input",e=>{k=Number(e.target.value);example=0;update();});
  document.querySelectorAll("button[data-k]").forEach(b=>b.addEventListener("click",()=>{k=Number(b.dataset.k);example=0;update();}));
  byId("show-separation").addEventListener("change",drawMixing);
  byId("new-example").addEventListener("click",()=>{example++;sampleDeck();});
  const table=byId("cut-table");
  for(const [label,rows] of [["Binomial cut",data.small_gsr],["Exact halfway cut",data.cut_half],["Uniform cut size",data.cut_uniform]]){
    const tr=document.createElement("tr");const name=document.createElement("td"),val=document.createElement("td");
    name.textContent=label;val.textContent=rows.find(r=>r.deck_tv<=.1)?.k??">12";tr.append(name,val);table.appendChild(tr);
  }
  window.addEventListener("resize",()=>{drawMixing();histogram("visible-plot",data.rows[k].visible_descents_probability,colors.visible_descents_tv);histogram("hidden-plot",data.rows[k].inverse_descents_probability,colors.deck_tv);});
  update();
})();
