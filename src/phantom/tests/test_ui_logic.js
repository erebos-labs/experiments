// A deliberately small event/DOM/WebAudio mock. No browser, rendering engine, or audio device.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const M=require('../src/model.js'),root=path.resolve(__dirname,'../src'),out=path.resolve(__dirname,'../results');
fs.mkdirSync(out,{recursive:true});
const html=fs.readFileSync(path.join(root,'page.html'),'utf8'),ui=fs.readFileSync(path.join(root,'ui.js'),'utf8');
function setup({pending=false,noAudio=false,reject=false}={}){
 const elements=new Map(),events={},windowEvents={},stats={contexts:0,started:0,stopped:0,disconnected:0,sources:[],gains:[],buffers:[],audio:[]};
 for(const match of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)){
  const tag=match[0],id=match[1],value=(tag.match(/\bvalue="([^"]*)"/)||[])[1]??'';
  elements.set(id,{id,value,disabled:/\bdisabled\b/.test(tag),textContent:'',innerHTML:'',attributes:{},handlers:{},addEventListener(name,fn){this.handlers[name]=fn},setAttribute(n,v){this.attributes[n]=v},removeAttribute(n){delete this.attributes[n]}});
 }
 const resumes=[];
 class FakeContext{
  constructor(){stats.contexts++;this.sampleRate=48000;this.currentTime=0;this.destination={};this.state='suspended';stats.audio.push(this);}
  resume(){if(reject)return Promise.reject(new Error('mock resume denied'));const p=pending?new Promise((resolve,reject)=>resumes.push({resolve,reject})):Promise.resolve();return p.then(()=>{if(this.state==='closed')throw new Error('closed');this.state='running';});}
  suspend(){this.state='suspended';return Promise.resolve();}
  close(){this.state='closed';return Promise.resolve();}
  createBuffer(channels,length,sampleRate){assert.equal(channels,2);const data=[];const b={length,sampleRate,data,copyToChannel(values,c){data[c]=new Float32Array(values)}};stats.buffers.push(b);return b;}
  createGain(){const g={gain:{value:1,cancelScheduledValues(){},setValueAtTime(v){this.value=v}},connect(){},disconnect(){stats.disconnected++}};stats.gains.push(g);return g;}
  createBufferSource(){const s={onended:null,buffer:null,connect(){},disconnect(){stats.disconnected++},start(){stats.started++;},stop(){stats.stopped++;}};stats.sources.push(s);return s;}
 }
 const document={hidden:false,getElementById(id){assert.ok(elements.has(id),`missing #${id}`);return elements.get(id)},addEventListener(n,fn){events[n]=fn}};
 const window={addEventListener(n,fn){windowEvents[n]=fn}};if(!noAudio)window.AudioContext=FakeContext;
 const sandbox={SoundModel:M,document,window,console,Float32Array};vm.runInNewContext(ui,sandbox,{filename:'ui.js',timeout:2000});
 return {elements,stats,document,events,windowEvents,resolve:(i=0)=>resumes[i]?.resolve(),reject:(i=0)=>resumes[i]?.reject(new Error('late resume rejection')),set(id,value){elements.get(id).value=String(value);elements.get(id).handlers.input()},click(id){return elements.get(id).handlers.click()},get:id=>elements.get(id)};
}
const results=[];
async function check(name,fn){const t=performance.now();const details=await fn();results.push({name,status:'PASS',ms:performance.now()-t,details});}
(async()=>{
 await check('initial load stays silent with disabled play controls',()=>{const s=setup();assert.equal(s.stats.contexts,0);assert.ok(s.get('play-a').disabled);assert.ok(s.get('play-b').disabled);assert.match(s.get('gain-value').textContent,/muted/);assert.match(s.get('verdict').textContent,/Same delay/);return {audio_contexts:0,play_disabled:true};});
 await check('primary turn and reset change calculated UI state and reset gain',()=>{const s=setup();s.click('turn');assert.equal(s.get('yaw').value,'20');assert.match(s.get('delay-a').textContent,/91.1/);assert.match(s.get('delay-b').textContent,/402.0/);assert.match(s.get('candidate-summary').textContent,/30 → 13/);s.set('gain',0.025);assert.equal(s.get('play-a').disabled,false);assert.equal(s.stats.contexts,0);s.click('reset');assert.equal(Number(s.get('yaw').value),0);assert.equal(Number(s.get('gain').value),0);assert.ok(s.get('play-a').disabled);assert.match(s.get('verdict').textContent,/Same delay/);return {turn_delays_us:[91.1,402.0],candidate_grid_counts:[30,13]};});
 await check('finite playback starts only after gain + explicit play, then onended cleans up',async()=>{const s=setup();await s.click('play-a');assert.equal(s.stats.contexts,0);s.set('gain',0.02);await s.click('play-a');assert.equal(s.stats.contexts,1);assert.equal(s.stats.started,1);assert.equal(s.stats.buffers[0].length,121008);assert.equal(s.stats.sources[0].buffer,s.stats.buffers[0]);s.stats.sources[0].onended();assert.match(s.get('audio-state').textContent,/No sound is playing/);return {mock_contexts:1,mock_starts:1,samples_per_channel:121008,actual_audio_played:false};});
 await check('new playback stops prior source; stop button mutes and disables play',async()=>{const s=setup();s.set('gain',0.02);await s.click('play-a');await s.click('play-b');assert.equal(s.stats.started,2);assert.equal(s.stats.stopped,1);s.click('stop');assert.equal(s.stats.stopped,2);assert.equal(Number(s.get('gain').value),0);assert.ok(s.get('play-a').disabled);assert.equal(s.stats.gains.at(-1).gain.value,0);return {only_one_active_mock_source:true,stop_resets_gain:true};});
 await check('control changes stop source, visibility change resets gain, pagehide stops',async()=>{const s=setup();s.set('gain',0.015);await s.click('play-a');s.set('bearing',-30);assert.equal(s.stats.stopped,1);assert.match(s.get('delay-a').textContent,/−262.4/);await s.click('play-b');s.document.hidden=true;s.events.visibilitychange();assert.equal(s.stats.stopped,2);assert.equal(Number(s.get('gain').value),0);assert.match(s.get('audio-state').textContent,/tab was hidden/);s.document.hidden=false;s.set('gain',0.015);await s.click('play-a');s.windowEvents.pagehide();assert.equal(s.stats.stopped,3);return {control_stop:true,hidden_tab_mute:true,pagehide_stop:true};});
 await check('stop invalidates a pending audio resume; no late surprise playback',async()=>{const s=setup({pending:true});s.set('gain',0.02);const p=s.click('play-a');s.click('stop');s.resolve();await p;assert.equal(s.stats.started,0);assert.equal(Number(s.get('gain').value),0);assert.equal(s.stats.audio[0].state,'suspended');return {mock_contexts:s.stats.contexts,mock_starts:0};});
 await check('idle context suspends, page exit closes, restored page creates a new context',async()=>{const s=setup();s.set('gain',0.02);await s.click('play-a');assert.equal(s.stats.audio[0].state,'running');s.stats.sources[0].onended();assert.equal(s.stats.audio[0].state,'suspended');await s.click('play-b');s.document.hidden=true;s.events.visibilitychange();assert.equal(s.stats.audio[0].state,'suspended');s.document.hidden=false;s.set('gain',0.02);await s.click('play-a');s.windowEvents.pagehide();assert.equal(s.stats.audio[0].state,'closed');s.set('gain',0.02);await s.click('play-a');assert.equal(s.stats.contexts,2);assert.equal(s.stats.audio[1].state,'running');return {idle_and_hidden_suspended:true,pagehide_closed:true,restored_context_created:true};});
 await check('stale resume rejection cannot mute a newer pending play',async()=>{const s=setup({pending:true});s.set('gain',0.02);const a=s.click('play-a'),b=s.click('play-b');s.reject(0);await a;assert.equal(Number(s.get('gain').value),0.02);s.resolve(1);await b;assert.equal(s.stats.started,1);assert.equal(s.stats.audio[0].state,'running');return {late_rejection_ignored:true,newer_play_survives:true};});
 await check('stale resume completion does not suspend a newer pending play',async()=>{const s=setup({pending:true});s.set('gain',0.02);const a=s.click('play-a'),b=s.click('play-b');s.resolve(0);await a;assert.equal(s.stats.started,0);assert.equal(s.stats.audio[0].state,'running');s.resolve(1);await b;assert.equal(s.stats.started,1);assert.equal(s.stats.audio[0].state,'running');return {newer_pending_resume_preserved:true};});
 await check('page exit closes a pending resume without late playback',async()=>{const s=setup({pending:true});s.set('gain',0.02);const p=s.click('play-a');s.windowEvents.pagehide();assert.equal(s.stats.audio[0].state,'closed');s.resolve();await p;assert.equal(s.stats.started,0);assert.equal(Number(s.get('gain').value),0);return {closed_pending_context:true,mock_starts:0};});
 await check('unsupported API and rejected resume return to silence',async()=>{for(const opts of [{noAudio:true},{reject:true}]){const s=setup(opts);s.set('gain',0.02);await s.click('play-a');assert.match(s.get('audio-state').textContent,/Audio unavailable/);assert.equal(Number(s.get('gain').value),0);assert.ok(s.get('play-a').disabled);assert.equal(s.stats.started,0);}return {error_paths:2,starts:0};});
 await check('boundary controls produce finite vector geometry; export representative SVG markup',()=>{
 const s=setup();let states=0;
 for(const bearing of [-80,0,80])for(const yaw of [-45,0,45])for(const orbit of [0,90,180,270,360]){
  s.set('bearing',bearing);s.set('yaw',yaw);s.set('orbit',orbit);
  for(const id of ['map','curves','candidates','cone'])assert.ok(!/NaN|Infinity|undefined/.test(s.get(id).innerHTML),`${id} invalid`);
  states++;
 }
 s.click('reset');
 const exported=[];
 for(const yaw of [0,20]){s.set('yaw',yaw);s.set('orbit',60);for(const [id,viewBox]of [['map','0 0 640 480'],['curves','0 0 640 330'],['candidates','0 0 640 240'],['cone','0 0 640 365']]){
  const name=`vector-${id}-yaw${yaw}.svg`;fs.writeFileSync(path.join(out,name),`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" role="img">${s.get(id).innerHTML}</svg>\n`);exported.push(name);
 }}return {boundary_states:states,exported,rendered_browser:false};
 });
 const report={at_utc:new Date().toISOString(),status:'PASS',kind:'logic-only event harness; small DOM and WebAudio mocks',tests:results,not_verified:['browser DOM semantics','actual CSS layout or responsive rendering','actual AudioContext scheduling','device channel order or sound pressure','human perception']};
 fs.writeFileSync(path.join(out,'ui-logic-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
