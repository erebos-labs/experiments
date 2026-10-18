(function () {
  'use strict';
  const {
    MODELS, exactEquilibrium, preShortcutSplit, perturbedEquilibrium, simulate, lateWindowSpan
  } = RouteLearning;
  const $ = id => document.getElementById(id);
  const routeNames = ['S → A → T', 'S → B → T', 'S → A → B → T'];
  const state = {model: 'original', demand: 6, step: 0.18, days: 40, start: 'pre', day: 0, timer: null};
  const num = (x, digits = 2) => Number(x).toLocaleString('en-US', {maximumFractionDigits: digits});

  function initialFlows(model) {
    if (state.start === 'equilibrium') return exactEquilibrium(model, state.demand).flows;
    if (state.start === 'perturbed') return perturbedEquilibrium(model, state.demand);
    return preShortcutSplit(state.demand);
  }

  function traces() {
    const model = MODELS[state.model];
    const initial = initialFlows(model);
    return {
      model,
      equilibrium: exactEquilibrium(model, state.demand),
      sync: simulate(model, state.demand, initial, {days: state.days, mode: 'synchronous'}),
      gradual: simulate(model, state.demand, initial, {days: state.days, mode: 'gradual', step: state.step})
    };
  }

  function pathFor(trace, x, y) {
    return trace.states.map((point, i) => `${i ? 'L' : 'M'}${x(i).toFixed(2)} ${y(point.flows[2]).toFixed(2)}`).join(' ');
  }

  function drawChart(data) {
    const W = 820, H = 340, L = 52, R = 20, T = 25, B = 45;
    const w = W - L - R, h = H - T - B;
    const ymax = Math.max(1, state.demand);
    const x = day => L + day / Math.max(1, state.days) * w;
    const y = flow => T + h - flow / ymax * h;
    let html = '';
    for (let i = 0; i <= 4; i += 1) {
      const flow = ymax * i / 4;
      html += `<line class="grid-line" x1="${L}" x2="${W - R}" y1="${y(flow)}" y2="${y(flow)}"/><text class="axis-text" x="${L - 9}" y="${y(flow) + 4}" text-anchor="end">${num(flow)}</text>`;
    }
    for (let i = 0; i <= 4; i += 1) {
      const day = Math.round(state.days * i / 4);
      html += `<text class="axis-text" x="${x(day)}" y="${H - 15}" text-anchor="middle">${day}</text>`;
    }
    html += `<text class="axis-text" x="${L}" y="14">flow</text><text class="axis-text" x="${W - R}" y="${H - 4}" text-anchor="end">day</text>`;
    html += `<line class="reference-line" x1="${L}" x2="${W - R}" y1="${y(data.equilibrium.flows[2])}" y2="${y(data.equilibrium.flows[2])}"/>`;
    html += `<path class="trace sync" d="${pathFor(data.sync, x, y)}"/><path class="trace gradual" d="${pathFor(data.gradual, x, y)}"/>`;
    html += `<line class="selector-line" x1="${x(state.day)}" x2="${x(state.day)}" y1="${T}" y2="${H - B}"/>`;
    html += `<circle class="point" cx="${x(state.day)}" cy="${y(data.sync.states[state.day].flows[2])}" r="5" fill="#b74c35"/><circle class="point" cx="${x(state.day)}" cy="${y(data.gradual.states[state.day].flows[2])}" r="5" fill="#087c74"/>`;
    $('chart-content').innerHTML = html;
    $('chart-desc').textContent = `${data.model.name}; fixed demand ${num(state.demand)}. Shortcut-route flow over ${state.days} day-to-day updates. The solid synchronous trace uses a full step; the dashed gradual trace uses ${num(state.step * 100, 0)} percent. The exact stationary equilibrium shortcut flow is ${num(data.equilibrium.flows[2])}. Selected day ${state.day}.`;
  }

  function drawBars(id, point) {
    $(id).innerHTML = point.flows.map((flow, i) => `<div class="bar-row"><span>${routeNames[i]}</span><span class="bar-track"><span class="bar-fill" style="width:${state.demand === 0 ? 0 : flow / state.demand * 100}%"></span></span><span class="bar-value">${num(flow)}</span></div>`).join('');
  }

  function metric(value, unit) {
    return value === null ? '—' : `${num(value)} <small>${unit}</small>`;
  }

  function render() {
    const data = traces();
    state.day = Math.min(state.day, state.days);
    $('model').value = state.model;
    $('demand').max = data.model.max;
    $('demand').value = state.demand;
    $('demand-out').value = num(state.demand);
    $('step').value = state.step;
    $('step-out').value = `${num(state.step * 100, 0)}%`;
    $('start').value = state.start;
    $('horizon').value = String(state.days);
    $('day').max = state.days;
    $('day').value = state.day;
    $('day-label').textContent = state.day;
    $('gradual-kicker').textContent = `${num(state.step * 100, 0)}% reconsider`;
    $('demand-caption').textContent = data.model.id === 'original' ? 'Abstract flow units; original affine costs. Not a count of real vehicles.' : 'One flow unit represents one thousand modeled drivers in the teaching rescaling.';
    drawChart(data);
    const syncPoint = data.sync.states[state.day], gradualPoint = data.gradual.states[state.day];
    drawBars('sync-bars', syncPoint); drawBars('gradual-bars', gradualPoint);
    $('sync-mean').innerHTML = metric(syncPoint.mean, data.model.unit);
    $('gradual-mean').innerHTML = metric(gradualPoint.mean, data.model.unit);
    $('sync-regret').innerHTML = metric(syncPoint.regret, data.model.unit);
    $('gradual-regret').innerHTML = metric(gradualPoint.regret, data.model.unit);
    $('sync-range').textContent = num(lateWindowSpan(data.sync));
    $('gradual-range').textContent = num(lateWindowSpan(data.gradual));
    $('reference-copy').textContent = state.demand === 0
      ? 'Zero demand: every route flow is zero, and no mean journey time is defined.'
      : `At demand ${num(state.demand)}, the exact equilibrium route flows are ${data.equilibrium.flows.map(x => num(x)).join(' / ')}, all used routes are cheapest, and mean time is ${num(data.equilibrium.mean)} ${data.model.unit}. This fixed point is computed analytically, not reached by silently replacing either learning trace.`;
    $('lockstep-copy').textContent = `Over the latter half of this ${state.days}-day window, shortcut flow spans ${num(lateWindowSpan(data.sync))} units under synchronous switching. At the original six-unit example, the pre-shortcut split and all-shortcut allocation alternate exactly.`;
    $('step-copy').textContent = `With α = ${num(state.step, 2)}, the same late-window shortcut span is ${num(lateWindowSpan(data.gradual))} units. The synchronous span is ${num(lateWindowSpan(data.sync))} units. A span can include a monotonic transient; it is not evidence of oscillation or convergence.`;
  }

  function stop() {
    if (state.timer !== null) clearInterval(state.timer);
    state.timer = null; $('play').textContent = 'Play'; $('play').setAttribute('aria-pressed', 'false');
  }

  $('model').addEventListener('change', () => {
    stop(); state.model = $('model').value; state.demand = MODELS[state.model].initial; state.day = 0; render();
  });
  $('demand').addEventListener('input', () => { stop(); state.demand = Number($('demand').value); state.day = 0; render(); });
  $('step').addEventListener('input', () => { stop(); state.step = Number($('step').value); render(); });
  $('start').addEventListener('change', () => { stop(); state.start = $('start').value; state.day = 0; render(); });
  $('horizon').addEventListener('change', () => { stop(); state.days = Number($('horizon').value); state.day = Math.min(state.day, state.days); render(); });
  $('day').addEventListener('input', () => { stop(); state.day = Number($('day').value); render(); });
  $('reset').addEventListener('click', () => { stop(); Object.assign(state, {model: 'original', demand: 6, step: 0.18, days: 40, start: 'pre', day: 0}); render(); });
  $('next').addEventListener('click', () => { stop(); state.day = state.day >= state.days ? 0 : state.day + 1; render(); });
  $('play').addEventListener('click', () => {
    if (state.timer !== null) { stop(); return; }
    $('play').textContent = 'Pause'; $('play').setAttribute('aria-pressed', 'true');
    state.timer = setInterval(() => {
      if (state.day >= state.days) { stop(); return; }
      state.day += 1; render();
    }, 550);
  });
  addEventListener('pagehide', stop);
  render();
})();
