/* Standalone, exact arithmetic. No libraries, requests, storage, or randomness. */
'use strict';
function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b){[a,b]=[b,a%b];}return a;}
function rat(n,d=1n){n=BigInt(n);d=BigInt(d);if(!d)throw Error('Zero denominator');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return {n:n/g,d:d/g};}
const plus=(a,b)=>rat(a.n*b.d+b.n*a.d,a.d*b.d);
const minus=(a,b)=>rat(a.n*b.d-b.n*a.d,a.d*b.d);
const times=(a,b)=>rat(a.n*b.n,a.d*b.d);
const over=(a,b)=>rat(a.n*b.d,a.d*b.n);
const exact=a=>a.d===1n?String(a.n):`${a.n}/${a.d}`;
const decimal=a=>Number(a.n)/Number(a.d);
const percent=a=>(decimal(a)*100).toFixed(2)+'%';
function validate(a,b,h,d){
  if(!/^[HT]{3}$/.test(a)||!/^[HT]{3}$/.test(b)||a===b)throw Error('Choose two distinct three-flip patterns.');
  if(!Number.isInteger(h)||!Number.isInteger(d)||h<=0||h>=d)throw Error('Coin probability must be between zero and one.');
}
function wordProbability(w,h,d){
  const heads=[...w].filter(x=>x==='H').length,tails=w.length-heads;
  return rat(BigInt(h)**BigInt(heads)*BigInt(d-h)**BigInt(tails),BigInt(d)**BigInt(w.length));
}
function overlap(a,b,h,d){
  let value=rat(0);
  for(let k=1;k<=Math.min(a.length,b.length);k++)if(a.slice(-k)===b.slice(0,k)){
    const p=wordProbability(b.slice(0,k),h,d);value=plus(value,rat(p.d,p.n));
  }
  return value;
}
function race(a,b,h=10,d=20){
  validate(a,b,h,d);
  const aa=overlap(a,a,h,d),ab=overlap(a,b,h,d),ba=overlap(b,a,h,d),bb=overlap(b,b,h,d);
  const denominator=plus(minus(aa,ab),minus(bb,ba));
  const pb=over(minus(aa,ab),denominator);
  return {a:minus(rat(1),pb),b:pb,meanA:aa,meanB:bb,
    mean:over(minus(times(aa,bb),times(ab,ba)),denominator),overlaps:[aa,ab,ba,bb]};
}
function fixed(a,b,n,h=10,d=20){
  validate(a,b,h,d);
  if(!Number.isInteger(n)||n<3||n>100)throw Error('Use a fixed horizon from 3 to 100 flips.');
  let live=new Map([['|0',1n]]);
  for(let t=0;t<n;t++){
    const next=new Map();
    for(const [key,mass] of live){
      const [tail,deltaText]=key.split('|'),delta=Number(deltaText);
      for(const [symbol,weight] of [['H',h],['T',d-h]]){
        const s=tail+symbol,change=Number(s.endsWith(a))-Number(s.endsWith(b));
        const following=s.slice(-2)+'|'+(delta+change);
        next.set(following,(next.get(following)||0n)+mass*BigInt(weight));
      }
    }
    live=next;
  }
  let am=0n,bm=0n,tie=0n;
  for(const [key,mass] of live){const delta=Number(key.split('|')[1]);if(delta>0)am+=mass;else if(delta<0)bm+=mass;else tie+=mass;}
  const denominator=BigInt(d)**BigInt(n);
  return {a:rat(am,denominator),tie:rat(tie,denominator),b:rat(bm,denominator)};
}
function inspectSequence(raw,a,b){
  const s=raw.toUpperCase().replace(/\s/g,'');
  if(s.length>200||/[^HT]/.test(s))throw Error('Use up to 200 H/T letters; spaces are allowed.');
  const hitsA=[],hitsB=[];let first=null;
  for(let i=0;i<=s.length-3;i++){
    const word=s.slice(i,i+3);
    if(word===a){hitsA.push(i+3);if(!first)first={winner:'A',end:i+3};}
    if(word===b){hitsB.push(i+3);if(!first)first={winner:'B',end:i+3};}
  }
  return {sequence:s,hitsA,hitsB,first};
}
function initialize(){
  const id=x=>document.getElementById(x),a=id('pattern-a'),b=id('pattern-b'),p=id('heads'),n=id('horizon');
  const choices=['HHH','HHT','HTH','HTT','THH','THT','TTH','TTT'];
  for(const select of [a,b])for(const pattern of choices){const option=document.createElement('option');option.value=option.textContent=pattern;select.append(option);}
  a.value='HHT';b.value='THH';
  function bars(target,items){
    target.replaceChildren();
    for(const [label,value,cls] of items){
      const segment=document.createElement('div');segment.className='segment '+cls;
      segment.style.width=(100*decimal(value))+'%';segment.setAttribute('aria-hidden','true');target.append(segment);
    }
    target.setAttribute('aria-label',items.map(([label,q])=>label+' '+percent(q)).join('; '));
  }
  function renderSequence(){
    try{
      const result=inspectSequence(id('flips').value,a.value,b.value);
      id('sequence-error').textContent='';
      id('sequence-race').textContent=result.first?`First arrival: ${result.first.winner==='A'?a.value:b.value} at flip ${result.first.end}.`:'First arrival: neither pattern has appeared.';
      id('sequence-count').textContent=`Whole sequence: ${a.value} ${result.hitsA.length}, ${b.value} ${result.hitsB.length}.`;
      id('sequence-view').replaceChildren();
      [...result.sequence].forEach((letter,i)=>{
        const cell=document.createElement('span');cell.textContent=letter;
        if(result.first&&i>=result.first.end-3&&i<result.first.end)cell.className=result.first.winner==='A'?'highlight-a':'highlight-b';
        id('sequence-view').append(cell);
      });
      const special=a.value==='HHT'&&b.value==='THH'&&result.sequence.length>=3;
      id('boundary').textContent=special?`Count difference = first pair HH (${Number(result.sequence.startsWith('HH'))}) − last pair HH (${Number(result.sequence.endsWith('HH'))}) = ${result.hitsA.length-result.hitsB.length}.`:'';
    }catch(error){id('sequence-error').textContent=error.message;id('sequence-view').replaceChildren();id('sequence-race').textContent='';id('sequence-count').textContent='';id('boundary').textContent='';}
  }
  function render(){
    try{
      const h=Number(p.value),horizon=Number(n.value),r=race(a.value,b.value,h),f=fixed(a.value,b.value,horizon,h);
      id('error').textContent='';
      for(const option of a.options)option.disabled=option.value===b.value;
      for(const option of b.options)option.disabled=option.value===a.value;
      id('heads-value').textContent=(h*5)+'%';id('horizon-value').textContent=horizon;
      for(const el of document.querySelectorAll('[data-pattern-a]'))el.textContent=a.value;
      for(const el of document.querySelectorAll('[data-pattern-b]'))el.textContent=b.value;
      bars(id('race-bar'),[[a.value,r.a,'a'],[b.value,r.b,'b']]);
      bars(id('count-bar'),[[a.value,f.a,'a'],['Tie',f.tie,'tie'],[b.value,f.b,'b']]);
      id('race-a').textContent=percent(r.a);id('race-b').textContent=percent(r.b);
      id('count-a').textContent=percent(f.a);id('count-b').textContent=percent(f.b);id('count-tie').textContent=percent(f.tie);
      id('mean-a').textContent=decimal(r.meanA).toFixed(3);id('mean-b').textContent=decimal(r.meanB).toFixed(3);
      id('race-mean').textContent=decimal(r.mean).toFixed(3);
      id('exact-results').textContent=`First arrival: A ${exact(r.a)}, B ${exact(r.b)}\nFixed horizon: A more ${exact(f.a)}, tie ${exact(f.tie)}, B more ${exact(f.b)}\nMean flips alone: A ${exact(r.meanA)}, B ${exact(r.meanB)}\nMean flips to first arrival: ${exact(r.mean)}\nWeighted overlaps AA, AB, BA, BB: ${r.overlaps.map(exact).join(', ')}`;
      id('special-note').textContent=a.value==='HHT'&&b.value==='THH'?
        'For this pair, HHT arrives first exactly when the first two flips are HH. With a fixed horizon of at least four flips, the score difference depends only on the first and last pairs.':
        'Every overlapping window scores a point in the fixed-horizon game. First-arrival probabilities refer to an uncapped race from empty history.';
      renderSequence();
    }catch(error){id('error').textContent=error.message;}
  }
  for(const control of [a,b,p,n])control.addEventListener('input',render);
  id('flips').addEventListener('input',renderSequence);
  render();
}
if(typeof module!=='undefined')module.exports={rat,plus,minus,times,over,exact,decimal,race,fixed,inspectSequence};
if(typeof document!=='undefined')initialize();
