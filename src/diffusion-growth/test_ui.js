'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const p=__dirname;const elements=new Map(),frames=new Map();let next=0,blob=null;const anchors=[],delayed=[],revoked=[];
const noop=()=>{};function element(id){if(elements.has(id))return elements.get(id);const e={id,value:'',disabled:false,hidden:false,width:640,height:640,innerHTML:'',listeners:{},attributes:{},statusChanges:0,getContext:()=>new Proxy({},{get:()=>noop,set:()=>true}),addEventListener(type,f){this.listeners[type]=f;},setAttribute(n,v){this.attributes[n]=v},getAttribute(n){return this.attributes[n]},click(){if(this.onclick)this.onclick()},set textContent(v){this.text=String(v);this.statusChanges++},get textContent(){return this.text||''}};elements.set(id,e);return e;}
for(const m of fs.readFileSync(path.join(p,'template.html'),'utf8').matchAll(/id="([^"]+)"/g))element(m[1]);for(const [k,v]of Object.entries({seed:'1981',sticking:'1',boundary:'near',target:'1200'}))element(k).value=v;
const template=fs.readFileSync(path.join(p,'template.html'),'utf8');
for(const match of template.matchAll(/<select id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)){
 element(match[1]).options=[...match[2].matchAll(/<option[^>]*value="([^"]+)"[^>]*>([^<]*)<\/option>/g)].map(m=>({value:m[1],textContent:m[2]}));
}
const samples=JSON.parse(fs.readFileSync(path.join(p,'data/samples.json'))),ensemble=JSON.parse(fs.readFileSync(path.join(p,'data/ensemble.json')));const ctx={console,Blob,Date,Math,Map,Set,Uint8Array,document:{getElementById:element,createElement:tag=>{assert.equal(tag,'a');const a={clicks:0,click(){this.clicks++}};anchors.push(a);return a}},requestAnimationFrame:f=>{frames.set(++next,f);return next},cancelAnimationFrame:i=>frames.delete(i),setTimeout:(fn,ms)=>{delayed.push({fn,ms});},URL:{createObjectURL:b=>{blob=b;return'blob:local-test'},revokeObjectURL:url=>revoked.push(url)},RECORDED:{samples:Array.isArray(samples)?samples:samples.samples,ensemble:{summary:ensemble.summary}}};ctx.window=ctx;ctx.globalThis=ctx;vm.createContext(ctx);const evaluate=s=>vm.runInContext(s,ctx,{timeout:5000});evaluate(fs.readFileSync(path.join(p,'model.js'),'utf8'));evaluate(fs.readFileSync(path.join(p,'ui.js'),'utf8'));
function frame(){const callbacks=[...frames.values()];frames.clear();for(const f of callbacks)f();}
(async()=>{
 assert.equal(element('boundary-current').textContent,'Selected: Near · R+8 / 2R+24');
 assert.equal(element('target-current').textContent,'Selected: 1,200 cells');
 for(const value of ['far','tight','near']){element('boundary').value=value;element('boundary').listeners.change();const selected=element('boundary').options.find(o=>o.value===value);assert.equal(element('boundary-current').textContent,'Selected: '+selected.textContent);}
 for(const value of ['0.1','1']){element('sticking').value=value;element('sticking').listeners.change();assert.equal(element('sticking-current').textContent,'Selected: '+element('sticking').options.find(o=>o.value===value).textContent);}

 assert.equal(evaluate('canProbe()'),true);assert.equal(element('probe').disabled,false);
 const initial=evaluate('JSON.stringify([models.dla.points,models.eden.points])');
 // Live export is explicitly partial and includes the requested target.
 element('probe').click();element('export').click();const live=JSON.parse(await blob.text());
 assert.equal(blob.type,'application/json');assert.equal(anchors.length,1);assert.equal(anchors[0].href,'blob:local-test');assert.equal(anchors[0].download,'growth-seed-1981.json');assert.equal(anchors[0].clicks,1);
 assert.equal(live.format,'erebos-growth-v1');assert.equal(new Date(live.exported).toISOString(),live.exported);
 const expected=JSON.parse(JSON.stringify(ctx.labState()));assert.deepEqual(live.dla,expected.dla);assert.deepEqual(live.eden,expected.eden);assert.deepEqual(live.probes,expected.probes);

 for(const p of Object.values(live.probes)){assert.equal(p.status,'partial');assert.equal(p.complete,false);assert.equal(p.target,1500);assert.equal(p.reason,null);}
 frame();const partialHits=evaluate('({dla:probeModels.dla.hits,eden:probeModels.eden.hits})');
 assert(partialHits.dla>0&&partialHits.eden>0);
 element('show-age').click();element('export').click();const cancelled=JSON.parse(await blob.text());
 for(const [id,p] of Object.entries(cancelled.probes)){assert.equal(p.reason,'cancelled');assert.equal(p.status,'cancelled');assert.equal(p.complete,false);assert.equal(p.target,1500);assert.equal(p.hits,partialHits[id]);assert(p.hits<p.target);}
 assert.equal(evaluate('probing'),false);assert.equal(evaluate('frame'),0);assert.equal(frames.size,0);
 assert.equal(evaluate('JSON.stringify([models.dla.points,models.eden.points])'),initial);
 // Cancellation before any callback is also unambiguous; Pause uses the same path.
 element('probe').click();element('show-age').click();element('export').click();const zero=JSON.parse(await blob.text());
 for(const p of Object.values(zero.probes)){assert.equal(p.hits,0);assert.equal(p.reason,'cancelled');assert.equal(p.complete,false);}
 element('probe').click();frame();element('pause').click();element('export').click();const paused=JSON.parse(await blob.text());
 for(const p of Object.values(paused.probes)){assert.equal(p.status,'cancelled');assert.equal(p.reason,'cancelled');assert.equal(p.complete,false);assert.equal(p.target,1500);}
 assert.equal(evaluate('JSON.stringify([models.dla.points,models.eden.points])'),initial);
 assert.ok(element('probe-masses').textContent.includes('1,200'));
 element('grow').click();const announced=element('announcements').statusChanges;frame();frame();
 assert.equal(element('announcements').statusChanges,announced,'Frame progress must not flood the live region');
 element('pause').click();const before=evaluate('({dla:models.dla.points.length,eden:models.eden.points.length,disabled:$("probe").disabled,probes:Object.keys(probeModels).length})');
 assert.equal(before.disabled,true);assert.equal(before.probes,0);
 element('probe').click();assert.equal(evaluate('Object.keys(probeModels).length'),0,'Handler must reject partial/unequal clusters even if called directly');
 element('export').click();const exported=JSON.parse(await blob.text());assert.deepEqual(exported.probes,{});
 element('seed').value='1981';element('seed').listeners.change();assert.equal(evaluate('canProbe()'),true);
 element('probe').click();let steps=0;while(evaluate('probing')){if(steps++>1000)throw Error('Probe exceeded deterministic test budget');frame();}
 const complete=evaluate('({dla:probeModels.dla.hits,eden:probeModels.eden.hits,frame:frame!==0})');
 assert.equal(complete.dla,1500);assert.equal(complete.eden,1500);assert.equal(complete.frame,false);
 element('show-age').click();assert.equal(element('age-early').hidden,false);
 element('export').click();const finished=JSON.parse(await blob.text());
 for(const p of Object.values(finished.probes)){assert.equal(p.status,'complete');assert.equal(p.complete,true);assert.equal(p.reason,'target');assert.equal(p.hits,p.target);assert.equal(p.target,1500);}
 assert.equal(frames.size,0);
 assert.equal(anchors.length,delayed.length);for(const a of anchors){assert.equal(a.clicks,1);assert.equal(a.download,'growth-seed-1981.json');assert.equal(a.href,'blob:local-test');}
 for(const scheduled of delayed){assert.equal(scheduled.ms,1000);scheduled.fn();}assert.equal(revoked.length,anchors.length);assert(revoked.every(url=>url==='blob:local-test'));
 console.log(JSON.stringify({status:'PASS',groups:10,downloadTransport:{format:live.format,mime:'application/json',fileName:anchors[0].download,clicksPerAction:1,revokedURLs:revoked.length,browserDownload:'not observed by this harness'},method:'Actual model/UI code with stub DOM and manual animation callbacks; not browser rendering or screen-reader behavior.',partialMasses:before,probeHits:complete,probeCallbacks:steps,exportStates:{partial:live.probes.dla.status,cancelled:cancelled.probes.dla.status,completed:finished.probes.dla.status},checks:['live export declares target and partial status','Return to age retains labelled cancelled counts and stops frames','zero-hit and Pause cancellations explicit','completed export survives Return to age','equal-completed-mass gate and direct-handler rejection','growth invalidates probe exports','milestone live updates only','bounded equal-mass probe completion/legend restore']}));
})().catch(e=>{console.error(e);process.exitCode=1});
