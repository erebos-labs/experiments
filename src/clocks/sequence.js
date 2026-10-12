/* Musical derivative; the dimensionless phase model itself is unchanged. */
(function(root){'use strict';
const M=typeof module!=='undefined'?require('./model.js'):root.Clocks;
const PPQ=480, BEATS=32, NOTES=[50,57,62,65,69,62,42,46];
function crossings(a,b,start,dt){
 const out=[]; if(b<=a)return out;
 for(let k=Math.floor(a/M.TAU)+1;k<=Math.floor(b/M.TAU);k++)out.push(start+dt*(k*M.TAU-a)/(b-a));
 return out;
}
function build({topology='ring',quantize=false,kick=true,bpm=130,dt=.025}={}){
 if(!['ring','open','complete'].includes(topology)||bpm<80||bpm>180||dt<.001||dt>.05)throw Error('Invalid configuration');
 const edge=M.edges(32,topology,1), end=BEATS*M.TAU, sec=60/bpm;
 let theta=M.initial(32,'wave',7,1,.12),t=0,events=[],frames=[{beat:0,theta:theta.slice()}],serial=0;
 while(t<end-1e-10){
  const h=Math.min(dt,end-t), next=M.step(theta,edge,1,h);
  for(let voice=0;voice<8;voice++){
   const clock=voice*4;
   for(const modelTime of crossings(theta[clock],next[clock],t,h)){
    const rawBeat=modelTime/M.TAU, beat=quantize?Math.round(rawBeat*4)/4:rawBeat;
    if(beat>=0&&beat<BEATS)events.push({id:serial++,beat,rawBeat,time:beat*sec,voice,clock,note:NOTES[voice],channel:voice<6?voice:9,velocity:voice<6?52:38,duration:voice<6?.22:.065,kind:voice<6?'pluck':'hat'});
   }
  }
  t+=h;theta=next;
  if(Math.floor(t/.3)>Math.floor((t-h)/.3)||t>=end-1e-10)frames.push({beat:t/M.TAU,theta:theta.slice()});
 }
 if(kick)for(let beat=0;beat<BEATS;beat++)events.push({id:serial++,beat,rawBeat:beat,time:beat*sec,voice:8,clock:null,note:36,channel:9,velocity:65,duration:.22,kind:'kick'});
 events.sort((a,b)=>a.time-b.time||a.id-b.id);
 return {events,frames,bpm,topology,quantize,kick,beats:BEATS,duration:BEATS*sec,ppq:PPQ,final:M.metrics(theta,edge),maxShiftSeconds:Math.max(0,...events.map(e=>Math.abs(e.beat-e.rawBeat)*sec))};
}
function vlq(n){if(!Number.isInteger(n)||n<0||n>0x0fffffff)throw Error('Invalid MIDI delta');let b=[n&127];while(n>>>=7)b.unshift((n&127)|128);return b;}
function midi(seq){
 const tempo=Math.round(60000000/seq.bpm), end=seq.beats*PPQ;
 const list=[{tick:0,order:0,data:[255,81,3,(tempo>>>16)&255,(tempo>>>8)&255,tempo&255]},{tick:0,order:1,data:[255,88,4,4,2,24,8]}];
 for(const e of seq.events){
  const on=Math.round(e.beat*PPQ),off=Math.min(end,on+Math.max(1,Math.round(e.duration*seq.bpm/60*PPQ)));
  if(off<=on)continue;
  list.push({tick:on,order:3,data:[144|e.channel,e.note,e.velocity]},{tick:off,order:2,data:[128|e.channel,e.note,0]});
 }
 list.sort((a,b)=>a.tick-b.tick||a.order-b.order);
 let data=[],last=0;for(const e of list){data.push(...vlq(e.tick-last),...e.data);last=e.tick;}
 data.push(...vlq(end-last),255,47,0);
 const be32=n=>[(n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255];
 return new Uint8Array([77,84,104,100,0,0,0,6,0,0,0,1,PPQ>>>8,PPQ&255,77,84,114,107,...be32(data.length),...data]);
}
/* Clock is the audio timeline, never animation frames. One bounded pass.
   Cancel future scheduled voices before calling pause. Late events are skipped. */
class Transport{
 constructor(seq){this.seq=seq;this.reset();}
 reset(){this.running=false;this.pos=0;this.cursor=0;this.sent=new Map();this.skipped=0;}
 start(now){if(this.pos>=this.seq.duration)this.reset();this.anchor=now+.06-this.pos;this.running=true;this.cursor=0;}
 position(now){return this.running?Math.max(0,Math.min(this.seq.duration,now-this.anchor)):this.pos;}
 pause(now){this.pos=this.position(now);this.running=false;for(const [id,time]of this.sent)if(time>now)this.sent.delete(id);}
 tick(now){
  if(!this.running)return [];
  const out=[];
  while(this.cursor<this.seq.events.length){const e=this.seq.events[this.cursor],at=this.anchor+e.time;
   if(at>now+.12)break;this.cursor++;
   if(this.sent.has(e.id))continue;
   if(at<now+.003){if(e.time>=this.pos)this.skipped++;continue;}
   this.sent.set(e.id,at);out.push({event:e,at});
  }
  if(now>=this.anchor+this.seq.duration+.3){this.pos=this.seq.duration;this.running=false;}
  return out;
 }
}
function peakVoices(seq){let x=[];for(const e of seq.events)x.push([e.time,1],[e.time+e.duration,-1]);x.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);let n=0,max=0;for(const [,d]of x){n+=d;max=Math.max(max,n);}return max;}
const api={build,crossings,midi,vlq,Transport,peakVoices,PPQ,BEATS};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ClockMusic=api;
})(typeof globalThis!=='undefined'?globalThis:this);
