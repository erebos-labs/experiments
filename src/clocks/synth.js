(function(root){'use strict';
/* Every voice is generated, bounded, dry, and finite. No samples or feedback. */
function voice(ctx,bus,e,at){
 const source=ctx.createOscillator(),gain=ctx.createGain(), nodes=[source,gain];
 source.type=e.kind==='pluck'?'triangle':'sine';
 if(e.kind==='kick'){source.frequency.setValueAtTime(118,at);source.frequency.exponentialRampToValueAtTime(46,at+.08);}
 else source.frequency.setValueAtTime(e.kind==='hat'?6100+e.voice*240:440*2**((e.note-69)/12),at);
 const amplitude=e.kind==='kick'?.24:e.kind==='hat'?.027:.055;
 gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(amplitude*e.velocity/65,at+.003);
 gain.gain.exponentialRampToValueAtTime(.00001,at+e.duration-.005);gain.gain.linearRampToValueAtTime(0,at+e.duration);
 source.connect(gain);gain.connect(bus);source.start(at);source.stop(at+e.duration);
 const handle={at,end:at+e.duration,cancel(now){gain.gain.cancelScheduledValues(now);gain.gain.setValueAtTime(0,now);try{source.stop(now);}catch(_){}nodes.forEach(n=>n.disconnect());}};
 source.onended=()=>nodes.forEach(n=>n.disconnect());return handle;
}
function wav(buffer){
 const samples=buffer.getChannelData(0), ab=new ArrayBuffer(44+samples.length*2),v=new DataView(ab);
 const str=(offset,s)=>{for(let i=0;i<s.length;i++)v.setUint8(offset+i,s.charCodeAt(i));};
 str(0,'RIFF');v.setUint32(4,ab.byteLength-8,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,buffer.sampleRate,true);v.setUint32(28,buffer.sampleRate*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,samples.length*2,true);
 let peak=0,energy=0;for(let i=0;i<samples.length;i++){const s=samples[i];if(!Number.isFinite(s)||Math.abs(s)>=1)throw Error('Render contains nonfinite/clipped samples');peak=Math.max(peak,Math.abs(s));energy+=s*s;v.setInt16(44+i*2,Math.round(s*32767),true);}
 return {bytes:new Uint8Array(ab),peak,rms:Math.sqrt(energy/samples.length)};
}
async function render(seq){const ctx=new OfflineAudioContext(1,Math.ceil((seq.duration+.3)*44100),44100),bus=ctx.createGain();bus.gain.value=.42;bus.connect(ctx.destination);for(const e of seq.events)voice(ctx,bus,e,e.time);return wav(await ctx.startRendering());}
root.ClockSynth={voice,wav,render};
})(globalThis);
