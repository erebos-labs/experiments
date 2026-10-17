(() => {
  'use strict';
  const M = SoundModel, $ = id => document.getElementById(id);
  const state = { bearing: 30, yaw: 0, tolerance: 15, orbit: 0, gain: 0 };
  let context = null, source = null, master = null, generation = 0, pendingResume = null;
  const colors = { a: '#087c70', b: '#ad4b29', ink: '#192b2b', muted: '#526564', line: '#cbd4ce' };
  const signed = n => `${n < -0.05 ? '−' : n > 0.05 ? '+' : ''}${Math.abs(n).toFixed(1)}`;
  const angle = n => n === 0 ? '0° · forward' : `${Math.abs(n)}° ${n < 0 ? 'left' : 'right'}`;
  const worldAngle = n => Math.abs(n) < 1e-10 ? '0° · world front' : Math.abs(Math.abs(n)-180) < 1e-10 ? '180° · world back' : `${Math.abs(n)}° ${n < 0 ? 'left' : 'right'} of world front`;
  const arrival = n => Math.abs(n) < 0.05 ? 'simultaneous in this model' : `${n > 0 ? 'right' : 'left'} ear earlier`;
  const currentHalf = az => { const c = Math.cos(M.rad(az - state.yaw)); return Math.abs(c) < 1e-10 ? 'front/back boundary' : c > 0 ? 'currently head-front' : 'currently head-back'; };
  const text = (x, y, content, extra = '') => `<text x="${x}" y="${y}" fill="${colors.muted}" font-family="system-ui,sans-serif" ${/\bfont-size=/.test(extra) ? '' : 'font-size="14"'} ${extra}>${content}</text>`;
  const circle = (x, y, r, extra = '') => `<circle cx="${x}" cy="${y}" r="${r}" ${extra}/>`;
  const line = (x1, y1, x2, y2, extra = '') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" ${extra}/>`;
  const path = points => points.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(3)},${p[1].toFixed(3)}`).join(' ');
  function svg(id, title, description, body) {
    $(id).innerHTML = `<title>${title}</title><desc>${description}</desc>${body}`;
    $(id).setAttribute('aria-label', title + '. ' + description);
    $(id).removeAttribute('aria-labelledby');
  }
  function drawMap() {
    const cx = 320, cy = 240, radius = 166;
    const point = a => [cx + radius * Math.sin(M.rad(a)), cy - radius * Math.cos(M.rad(a))];
    const h = M.rad(state.yaw), a = point(state.bearing), b = point(M.mirror(state.bearing));
    const ears = [[cx - 40 * Math.cos(h), cy - 40 * Math.sin(h)], [cx + 40 * Math.cos(h), cy + 40 * Math.sin(h)]];
    let body = circle(cx, cy, radius, `fill="none" stroke="${colors.line}" stroke-dasharray="3 6"`);
    body += line(cx, 53, cx, 428, `stroke="${colors.line}"`) + line(120, cy, 520, cy, `stroke="${colors.line}"`);
    body += text(320, 28, 'WORLD FRONT · 0°', 'text-anchor="middle" font-size="12" letter-spacing="1"');
    body += text(320, 463, 'WORLD BACK · ±180°', 'text-anchor="middle" font-size="12" letter-spacing="1"');
    body += text(68, cy + 5, 'LEFT', 'text-anchor="middle" font-size="12"');
    body += text(572, cy + 5, 'RIGHT', 'text-anchor="middle" font-size="12"');
    for (const [p, color, label, bearing] of [[a, colors.a, 'A', state.bearing], [b, colors.b, 'B', M.mirror(state.bearing)]]) {
      for (const e of ears) body += line(...p, ...e, `stroke="${color}" stroke-width="1.6" opacity=".42"`);
      body += circle(...p, 12, `fill="${color}" stroke="#fffefa" stroke-width="3"`);
      body += text(p[0], p[1] + (label === 'A' ? -23 : 33), `${label} · ${worldAngle(bearing)}`, 'text-anchor="middle" font-weight="600"');
    }
    body += `<g transform="translate(${cx} ${cy}) rotate(${state.yaw})">`;
    body += circle(0, 0, 35, `fill="#e7eee8" stroke="${colors.ink}" stroke-width="1.5"`);
    body += `<path d="M-8,-34 L0,-49 L8,-34" fill="#e7eee8" stroke="${colors.ink}" stroke-width="1.5"/>`;
    body += line(-40, 0, 40, 0, `stroke="${colors.ink}" stroke-width="2"`);
    body += circle(-40, 0, 5, `fill="${colors.ink}"`) + circle(40, 0, 5, `fill="${colors.ink}"`);
    body += text(-49, 22, 'L', 'text-anchor="middle"') + text(49, 22, 'R', 'text-anchor="middle"');
    body += `</g>`;
    svg('map', 'Top view: two possible source directions', `A at ${state.bearing} degrees, B at ${M.mirror(state.bearing)} degrees, head turned ${state.yaw} degrees. Schematic, not to scale.`, body);
  }
  function drawCurves(a, b) {
    const x = h => 58 + (h + 45) / 90 * 554, y = us => 275 - (us + 550) / 1100 * 245;
    let body = '';
    for (const us of [-500, 0, 500]) body += line(58, y(us), 612, y(us), `stroke="${colors.line}"`) + text(47, y(us) + 4, `${us}`, 'text-anchor="end" font-size="12"');
    for (const h of [-45, 0, 45]) body += text(x(h), 303, `${h > 0 ? '+' : ''}${h}°`, 'text-anchor="middle" font-size="12"');
    body += text(58, 18, 'DELAY · μs', 'font-size="11" letter-spacing="1"') + text(612, 324, 'SIMULATED YAW', 'text-anchor="end" font-size="11" letter-spacing="1"');
    body += line(x(0), 30, x(0), 275, `stroke="${colors.line}" stroke-dasharray="3 4"`);
    for (const [az, color] of [[state.bearing, colors.a], [M.mirror(state.bearing), colors.b]]) {
      const points = []; for (let h = -45; h <= 45; h += 0.5) points.push([x(h), y(M.delay(az, h))]);
      body += `<path d="${path(points)}" fill="none" stroke="${color}" stroke-width="2.5"/>`;
    }
    body += line(x(state.yaw), 30, x(state.yaw), 275, `stroke="${colors.ink}" stroke-width="1"`);
    body += circle(x(state.yaw), y(a), 5, `fill="${colors.a}" stroke="#fffefa" stroke-width="1.5"`);
    body += circle(x(state.yaw), y(b), 5, `fill="${colors.b}" stroke="#fffefa" stroke-width="1.5"`);
    svg('curves', 'Calculated delay as the head turns', `Current A delay ${signed(a)} microseconds and B delay ${signed(b)} microseconds.`, body);
  }
  function drawCandidates() {
    const c = M.candidates(state.bearing, state.yaw, state.tolerance);
    const x = az => 58 + (az + 180) / 360 * 554, width = 554 / 1440 + 0.05;
    let body = text(58, 26, 'COMPATIBLE WORLD DIRECTIONS', 'font-size="11" letter-spacing="1"');
    body += text(58, 60, 'Initial measurement', 'font-size="13"') + text(58, 130, 'Initial + turned measurement', 'font-size="13"');
    body += `<rect x="58" y="74" width="554" height="25" fill="#f0f2ec"/><rect x="58" y="144" width="554" height="25" fill="#f0f2ec"/>`;
    for (const a of c.single) body += `<rect x="${x(a)}" y="74" width="${width}" height="25" fill="#b9c7bd"/>`;
    for (const a of c.both) body += `<rect x="${x(a)}" y="144" width="${width}" height="25" fill="${colors.a}"/>`;
    for (const [a, label] of [[-180,'back'],[-90,'left'],[0,'front'],[90,'right'],[180,'back']]) {
      body += line(x(a), 174, x(a), 180, `stroke="${colors.muted}"`) + text(x(a), 199, `${a}°`, 'text-anchor="middle" font-size="11"') + text(x(a), 221, label, 'text-anchor="middle" font-size="11"');
    }
    for (const [az, label, color] of [[state.bearing,'A',colors.a],[M.mirror(state.bearing),'B',colors.b]]) body += line(x(az), 70, x(az), 171, `stroke="${color}" stroke-width="1" stroke-dasharray="2 3"`) + text(x(az), 49, label, 'text-anchor="middle" font-size="13" font-weight="600"');
    svg('candidates', 'Grid directions compatible with the synthetic observations', `${c.single.length} initial directions and ${c.both.length} directions after both measurements, out of 1440 tested directions.`, body);
    $('candidate-summary').textContent = `${c.single.length} → ${c.both.length} compatible grid directions out of 1,440, using ±${state.tolerance} μs per measurement.`;
  }
  function drawCone() {
    const q = Math.sin(M.rad(state.bearing));
    const projection = v => [320 + 174 * v[0] + 64 * v[1], 185 + 52 * v[1] - 139 * v[2]];
    const origin = projection([0,0,0]);
    const ring = []; for (let t = 0; t <= 360; t += 2) ring.push(projection(M.cone(q,t)));
    let body = '';
    for (const [v,label] of [[[1.25,0,0],'right'],[[0,1.25,0],'front'],[[0,0,1.12],'up']]) {
      const end = projection(v), neg = projection(v.map(x => -x));
      body += line(...neg, ...end, `stroke="${colors.line}"`) + text(end[0] + 8, end[1] + 4, label, 'font-size="12"');
    }
    for (const plane of ['xy','xz','yz']) {
      const points=[];for(let d=0;d<=360;d+=3){const t=M.rad(d);points.push(projection(plane==='xy'?[Math.cos(t),Math.sin(t),0]:plane==='xz'?[Math.cos(t),0,Math.sin(t)]:[0,Math.cos(t),Math.sin(t)]));}
      body += `<path d="${path(points)}" fill="none" stroke="${colors.line}" stroke-dasharray="3 5"/>`;
    }
    for (const d of [0,60,120,180,240,300]) body += line(...origin,...projection(M.cone(q,d)), `stroke="${colors.a}" opacity=".14"`);
    body += `<path d="${path(ring)}" fill="none" stroke="${colors.a}" stroke-width="2.5"/>`;
    const v=M.cone(q,state.orbit), p=projection(v), mirror=projection([v[0],v[1],-v[2]]);
    body += line(...origin,...p,`stroke="${colors.a}" stroke-width="2"`) + circle(...origin,4,`fill="${colors.ink}"`);
    if(Math.abs(v[2])>0.03)body += circle(...mirror,7,`fill="#fffefa" stroke="${colors.b}" stroke-width="2"`) + text(mirror[0]+12,mirror[1]+4,'height mirror','font-size="12"');
    body += circle(...p,8,`fill="${colors.a}" stroke="#fffefa" stroke-width="2"`);
    body += text(20,340,`Fixed lateral component x = ${q.toFixed(3)}`,'font-size="12"');
    svg('cone','Equal-delay ring in a fixed oblique projection',`The selected direction has initial delay ${signed(M.delayVector(v))} microseconds; its height mirror has the same delay for every yaw.`,body);
    $('cone-readout').textContent = `Initial: ${signed(M.delayVector(v))} μs everywhere on this ring. At your ${state.yaw}° yaw: ${signed(M.delayVector(v,state.yaw))} μs. Above/below mirrors still match; elevation magnitude can be constrained.`;
  }
  function suspendIfIdle(audio = context) {
    if (audio && audio.state === 'running' && !source && pendingResume === null) void audio.suspend().catch(() => {});
  }
  function stop(resetGain = false, message = null) {
    generation++;
    pendingResume=null;
    if (source) {
      if (master && context) { master.gain.cancelScheduledValues(context.currentTime); master.gain.setValueAtTime(0, context.currentTime); }
      source.onended=null;try{source.stop();}catch{}source.disconnect();source=null;
      if(master){master.disconnect();master=null;}
    }
    if (resetGain) { state.gain=0;$('gain').value='0'; }
    suspendIfIdle();
    updateAudioControls();
    if (message) $('audio-state').textContent=message;
  }
  function updateAudioControls() {
    $('gain-value').textContent = state.gain===0 ? '0.000 · muted' : state.gain.toFixed(3);
    $('play-a').disabled = state.gain===0;
    $('play-b').disabled = state.gain===0;
    $('stop').disabled = state.gain===0 && !source;
  }
  async function play(which) {
    if (state.gain===0) return;
    stop(false);
    const token=++generation, az=which==='A'?state.bearing:M.mirror(state.bearing), tau=M.delay(az,state.yaw), gain=state.gain;
    pendingResume=token;
    let audio=null;
    try {
      const AudioCtor=window.AudioContext||window.webkitAudioContext;
      if (!AudioCtor) throw new Error('Web Audio is unavailable in this browser.');
      if(!context || context.state === 'closed')context=new AudioCtor();
      audio=context;
      await audio.resume();
      if(pendingResume===token)pendingResume=null;
      if(token!==generation||document.hidden||state.gain===0){suspendIfIdle(audio);return;}
      const data=M.stereo(tau,gain,context.sampleRate), buffer=context.createBuffer(2,data.left.length,data.sampleRate);
      buffer.copyToChannel(data.left,0);buffer.copyToChannel(data.right,1);
      source=context.createBufferSource();master=context.createGain();master.gain.value=1;
      source.buffer=buffer;source.connect(master);master.connect(context.destination);
      source.onended=()=>{if(token!==generation)return;source.disconnect();source=null;master.disconnect();master=null;suspendIfIdle(audio);updateAudioControls();$('audio-state').textContent=`Finished ${which}. No sound is playing. Digital amplitude remains ${state.gain.toFixed(3)} for the next press.`;};
      source.start();updateAudioControls();
      $('audio-state').textContent=`Playing ${which}: ${signed(tau)} μs; digital amplitude ${gain.toFixed(3)}; stops in ${data.duration.toFixed(2)} s.`;
    } catch(error) { if(pendingResume===token)pendingResume=null;if(token===generation)stop(true,`Audio unavailable: ${error.message}`);else suspendIfIdle(audio); }
  }
  function render() {
    const a=M.delay(state.bearing,state.yaw),b=M.delay(M.mirror(state.bearing),state.yaw),difference=Math.abs(a-b);
    $('bearing-value').textContent=angle(state.bearing);$('yaw-value').textContent=angle(state.yaw);
    $('tolerance-value').textContent=`±${state.tolerance} μs`;$('orbit-value').textContent=`${state.orbit}°`;
    $('delay-a').textContent=`${signed(a)} μs`;$('delay-b').textContent=`${signed(b)} μs`;
    $('arrival-a').textContent=arrival(a)+' · '+currentHalf(state.bearing);$('arrival-b').textContent=arrival(b)+' · '+currentHalf(M.mirror(state.bearing));
    $('verdict').textContent=difference<0.05?'Same delay. This cue alone cannot choose front or back.':`The delays differ by ${difference.toFixed(1)} μs. Two measurements can separate this horizontal pair if the source stays fixed and poses are known.`;
    drawMap();drawCurves(a,b);drawCandidates();drawCone();updateAudioControls();
  }
  for(const id of ['bearing','yaw','tolerance','orbit','gain'])$(id).addEventListener('input',()=>{
    stop(false,'Stopped after a control change. Press A or B to play the new cue.');state[id]=Number($(id).value);render();
    if(state.gain===0)$('audio-state').textContent='Muted. No sound is playing.';
  });
  $('turn').addEventListener('click',()=>{stop(false,'Stopped after a control change.');state.yaw=20;$('yaw').value='20';render();});
  $('reset').addEventListener('click',()=>{stop(true,'Reset to silence. No sound is playing.');Object.assign(state,{bearing:30,yaw:0,tolerance:15,orbit:0,gain:0});for(const id of Object.keys(state))$(id).value=state[id];render();});
  $('play-a').addEventListener('click',()=>play('A'));$('play-b').addEventListener('click',()=>play('B'));
  $('stop').addEventListener('click',()=>stop(true,'Muted. No sound is playing.'));
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop(true,'Muted because the tab was hidden.');});
  window.addEventListener('pagehide',()=>{stop(true);const audio=context;context=null;if(audio && audio.state!=='closed')void audio.close().catch(()=>{});});
  render();
})();
