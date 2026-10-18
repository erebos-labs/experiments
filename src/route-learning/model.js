/* Day-to-day route learning on the same three-route Braess toy models. */
(function (root) {
  'use strict';

  const MODELS = Object.freeze({
    teaching: Object.freeze({
      id: 'teaching', name: 'Teaching model', a: 10, b: 45, k: 0, s: 0, h: 0,
      max: 12, initial: 4, unit: 'min'
    }),
    original: Object.freeze({
      id: 'original', name: 'Braess’s original model', a: 10, b: 50, k: 1, s: 10, h: 1,
      max: 20, initial: 6, unit: 'time units'
    })
  });

  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

  function validate(model, demand, flows) {
    if (!model || !Number.isFinite(demand) || demand < 0) {
      throw new RangeError('Model and nonnegative finite demand are required');
    }
    if (!Array.isArray(flows) || flows.length !== 3 || flows.some(x => !Number.isFinite(x) || x < 0)) {
      throw new RangeError('Three nonnegative finite route flows are required');
    }
    const total = flows.reduce((sum, x) => sum + x, 0);
    if (Math.abs(total - demand) > 1e-8 * Math.max(1, demand)) {
      throw new RangeError('Route flows must sum to demand');
    }
  }

  function measure(model, demand, flows) {
    validate(model, demand, flows);
    const [upper, lower, cross] = flows.map(x => Math.max(0, x));
    const {a, b, k, s, h} = model;
    const edges = [upper + cross, upper, lower, lower + cross, cross];
    const edgeTimes = [
      a * edges[0], b + k * edges[1], b + k * edges[2], a * edges[3], s + h * edges[4]
    ];
    const costs = [
      edgeTimes[0] + edgeTimes[1],
      edgeTimes[2] + edgeTimes[3],
      edgeTimes[0] + edgeTimes[4] + edgeTimes[3]
    ];
    const cheapest = Math.min(...costs);
    const totalTime = upper * costs[0] + lower * costs[1] + cross * costs[2];
    const regret = demand === 0 ? 0 : Math.max(0, ...[upper, lower, cross].map((flow, i) => (
      flow > 1e-10 ? costs[i] - cheapest : 0
    )));
    if (![...edges, ...edgeTimes, ...costs, totalTime, regret].every(Number.isFinite)
        || (demand > 0 && !Number.isFinite(totalTime / demand))) {
      throw new RangeError('Derived traffic arithmetic exceeds finite numeric range');
    }
    return {
      flows: [upper, lower, cross], edges, edgeTimes, costs, demand,
      totalTime, mean: demand === 0 ? null : totalTime / demand, regret
    };
  }

  function exactEquilibrium(model, demand) {
    if (!model || !Number.isFinite(demand) || demand < 0) {
      throw new RangeError('Model and nonnegative finite demand are required');
    }
    const {a, b, k, s, h} = model;
    const cross = clamp((2 * (b - s) - (a - k) * demand) / (a + k + 2 * h), 0, demand);
    const side = (demand - cross) / 2;
    return measure(model, demand, [side, side, cross]);
  }

  function preShortcutSplit(demand) {
    if (!Number.isFinite(demand) || demand < 0) throw new RangeError('Invalid demand');
    return [demand / 2, demand / 2, 0];
  }

  function perturbedEquilibrium(model, demand) {
    const flows = exactEquilibrium(model, demand).flows.slice();
    if (demand === 0) return flows;
    const donor = flows.indexOf(Math.max(...flows));
    const receiver = (donor + 1) % flows.length;
    const delta = Math.min(0.03 * demand, flows[donor] / 2);
    flows[donor] -= delta;
    flows[receiver] += delta;
    return flows;
  }

  function fastestTarget(costs, demand, currentFlows, tieTolerance = 1e-9) {
    if (!Array.isArray(costs) || costs.length !== 3 || costs.some(x => !Number.isFinite(x))) {
      throw new RangeError('Three finite route costs are required');
    }
    if (!Array.isArray(currentFlows) || currentFlows.length !== 3 || currentFlows.some(x => !Number.isFinite(x) || x < 0)) {
      throw new RangeError('Three nonnegative current flows are required');
    }
    if (!Number.isFinite(demand) || demand < 0 || !Number.isFinite(tieTolerance) || tieTolerance < 0) {
      throw new RangeError('Invalid demand or tie tolerance');
    }
    const best = Math.min(...costs);
    const tolerance = tieTolerance * Math.max(1, Math.abs(best));
    const winners = costs.map((cost, i) => Math.abs(cost - best) <= tolerance ? i : -1).filter(i => i >= 0);
    const winningFlow = winners.reduce((sum, i) => sum + currentFlows[i], 0);
    if (winningFlow > 0) {
      return costs.map((_, i) => winners.includes(i) ? demand * currentFlows[i] / winningFlow : 0);
    }
    const share = winners.length ? demand / winners.length : 0;
    return costs.map((_, i) => winners.includes(i) ? share : 0);
  }

  function nextDay(model, demand, flows, mode, step = 0.18, tieTolerance = 1e-9) {
    const current = measure(model, demand, flows);
    if (!['synchronous', 'gradual'].includes(mode)) throw new RangeError('Unknown update mode');
    if (!Number.isFinite(step) || step <= 0 || step > 1) throw new RangeError('Step must be in (0, 1]');
    const target = fastestTarget(current.costs, demand, current.flows, tieTolerance);
    const alpha = mode === 'synchronous' ? 1 : step;
    const updated = current.flows.map((flow, i) => (1 - alpha) * flow + alpha * target[i]);
    const mismatch = demand - updated.reduce((sum, x) => sum + x, 0);
    updated[updated.indexOf(Math.max(...updated))] += mismatch;
    return {state: measure(model, demand, updated), target, alpha};
  }

  function simulate(model, demand, initialFlows, options = {}) {
    const days = options.days ?? 40;
    const mode = options.mode ?? 'synchronous';
    const step = options.step ?? 0.18;
    const tieTolerance = options.tieTolerance ?? 1e-9;
    if (!Number.isInteger(days) || days < 0 || days > 2000) throw new RangeError('Days must be an integer from 0 to 2000');
    const states = [measure(model, demand, initialFlows)];
    const targets = [];
    for (let day = 0; day < days; day += 1) {
      const result = nextDay(model, demand, states[states.length - 1].flows, mode, step, tieTolerance);
      targets.push(result.target);
      states.push(result.state);
    }
    return {mode, step: mode === 'synchronous' ? 1 : step, tieTolerance, states, targets};
  }

  function lateWindowSpan(trace, routeIndex = 2) {
    if (!trace || !Array.isArray(trace.states) || trace.states.length > 2001
        || !Number.isInteger(routeIndex) || routeIndex < 0 || routeIndex > 2) {
      throw new RangeError('A trace of at most 2001 states and route index 0..2 is required');
    }
    let low = Infinity, high = -Infinity;
    for (let i = Math.floor(trace.states.length / 2); i < trace.states.length; i += 1) {
      const value = trace.states[i]?.flows?.[routeIndex];
      if (!Number.isFinite(value)) throw new RangeError('Trace flows must be finite');
      low = Math.min(low, value); high = Math.max(high, value);
    }
    return low === Infinity ? 0 : high - low;
  }
  // Compatibility alias; a range does not establish oscillation.
  const oscillationRange = lateWindowSpan;

  const api = {
    MODELS, measure, exactEquilibrium, preShortcutSplit, perturbedEquilibrium,
    fastestTarget, nextDay, simulate, lateWindowSpan, oscillationRange
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RouteLearning = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
