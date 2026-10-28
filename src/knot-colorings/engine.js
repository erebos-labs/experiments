/* Exact, bounded Fox-coloring engine. Positive i: left strand passes over right. */
(function(root) {
  'use strict';
  function validate(n, word, q) {
    if (!Number.isInteger(n) || n < 1 || n > 4) throw new Error('Use 1 to 4 strands');
    if (!Array.isArray(word) || word.length > 16 || word.some(x => !Number.isInteger(x) || !x || Math.abs(x) >= n)) throw new Error('Invalid braid word');
    if (!Number.isInteger(q) || q < 2 || q > 31 || q ** n > 200000) throw new Error('Modulus or enumeration budget exceeded');
  }
  function step(values, crossing, q) {
    const i = Math.abs(crossing)-1, a = values[i], b = values[i+1];
    const mod = x => ((x % q)+q) % q;
    if (crossing > 0) { values[i] = mod(2*a-b); values[i+1] = a; }
    else { values[i] = b; values[i+1] = mod(2*b-a); }
  }
  function trace(colors, word, q) {
    validate(colors.length, word, q);
    if (colors.some(x => !Number.isInteger(x) || x < 0 || x >= q)) throw new Error('Invalid input colors');
    const values = colors.slice(), states = [values.slice()];
    for (const crossing of word) { step(values,crossing,q); states.push(values.slice()); }
    return states;
  }
  function propagate(colors, word, q) { return trace(colors,word,q).at(-1); }
  function enumerate(n, word, q) {
    validate(n,word,q);
    const out = [];
    for (let k=0; k < q ** n; k++) {
      let code=k; const top=Array(n), bottom=Array(n);
      for (let i=n-1; i>=0; i--) { top[i]=code % q; code=Math.floor(code/q); }
      for (let i=0; i<n; i++) bottom[i]=top[i];
      for (const crossing of word) step(bottom,crossing,q);
      if (top.every((v,i) => v === bottom[i])) out.push(top);
    }
    return out;
  }
  function components(n, word) {
    validate(n,word,2);
    const permutation = Array.from({length:n},(_,i) => i);
    for (const crossing of word) {
      const i = Math.abs(crossing)-1;
      [permutation[i],permutation[i+1]]=[permutation[i+1],permutation[i]];
    }
    const seen=new Set(), cycles=[];
    for (let start=0; start<n; start++) {
      if (seen.has(start)) continue;
      let j=start; const cycle=[];
      while (!seen.has(j)) { seen.add(j); cycle.push(j); j=permutation[j]; }
      cycles.push(cycle);
    }
    return cycles;
  }
  const palette=['#ae4435','#28687f','#596b31','#80508a','#965117','#4656a0','#79503b','#2e7060','#7c5366'];
  function renderBraid(n,word,q,colors) {
    validate(n,word,q);
    const states=trace(colors,word,q), yTop=86, stepY=48;
    if (!colors.every((value,i)=>value===states.at(-1)[i])) throw new Error('The coloring must close before drawing');
    const yBottom=yTop+Math.max(1,word.length)*stepY;
    const color = value => palette[value % palette.length];
    const x = i => 70+i*64;
    const line = (x1,y1,x2,y2,stroke,width=6) => `<path d="M${x1},${y1}L${x2},${y2}" fill="none" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round"/>`;
    let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 ${yBottom+82}" role="img" aria-labelledby="braid-title braid-description"><title id="braid-title">A valid modulo ${q} coloring of a closed braid</title><desc id="braid-description">${n} strands, ${word.length} crossings. Outside curves connect each bottom slot to the same top slot. A break in the line marks an underpass. Numbers identify colors.</desc>`;
    for (let i=0; i<n; i++) {
      const topCap=yTop-24-(n-1-i)*16, bottomCap=yBottom+24+(n-1-i)*16, right=350-18*i;
      svg+=`<path d="M${x(i)},${yTop}V${topCap}H${right}V${bottomCap}H${x(i)}V${yBottom}" fill="none" stroke="${color(colors[i])}" stroke-width="5" stroke-linejoin="round"/>`;
    }
    if (!word.length) for (let i=0;i<n;i++) svg+=line(x(i),yTop,x(i),yBottom,color(colors[i]));
    word.forEach((crossing,row) => {
      const i=Math.abs(crossing)-1, y0=yTop+row*stepY, y1=y0+stepY, midY=(y0+y1)/2, midX=(x(i)+x(i+1))/2;
      const before=states[row],after=states[row+1],positive=crossing>0;
      for (let j=0;j<n;j++) if (j !== i && j !== i+1) svg+=line(x(j),y0,x(j),y1,color(before[j]));
      const underStart=positive ? i+1 : i, underEnd=positive ? i : i+1;
      const overStart=positive ? i : i+1, overEnd=positive ? i+1 : i;
      svg+=line(x(underStart),y0,midX,midY,color(before[underStart]));
      svg+=line(midX,midY,x(underEnd),y1,color(after[underEnd]));
      svg+=line(x(overStart),y0,x(overEnd),y1,'#fdfbf5',14);
      svg+=line(x(overStart),y0,x(overEnd),y1,color(before[overStart]));
      svg+=`<text x="23" y="${midY+5}" text-anchor="middle" font-size="13" fill="#687470" font-family="system-ui,sans-serif">${row+1}</text>`;
    });
    for (let i=0;i<n;i++) for (const [value,y] of [[colors[i],yTop],[states.at(-1)[i],yBottom]]) {
      svg+=`<circle cx="${x(i)}" cy="${y}" r="12" fill="${color(value)}"/><text x="${x(i)}" y="${y+5}" text-anchor="middle" fill="white" font-size="15" font-weight="700" font-family="system-ui,sans-serif">${value}</text>`;
    }
    return svg+'</svg>';
  }
  const api={validate,trace,propagate,enumerate,components,renderBraid};
  if (typeof module !== 'undefined' && module.exports) module.exports=api;
  else root.KnotColors=api;
})(globalThis);
