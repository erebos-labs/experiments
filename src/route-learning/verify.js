'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const B = require('./model.js');

let cases = 0;
let statesChecked = 0;
let maxConservationError = 0;
let minimumFlow = Infinity;
let maxStationaryFixedPointError = 0;

function checkState(state, demand) {
  const mismatch = Math.abs(state.flows.reduce((sum, x) => sum + x, 0) - demand);
  maxConservationError = Math.max(maxConservationError, mismatch);
  minimumFlow = Math.min(minimumFlow, ...state.flows);
  assert.ok(mismatch < 1e-8 * Math.max(1, demand));
  assert.ok(state.flows.every(x => x >= -1e-12 && Number.isFinite(x)));
  assert.ok(state.costs.every(Number.isFinite));
  assert.equal(state.mean === null, demand === 0);
  statesChecked += 1;
}

for (const model of Object.values(B.MODELS)) {
  for (let i = 0; i <= 100; i += 1) {
    const demand = model.max * i / 100;
    const equilibrium = B.exactEquilibrium(model, demand);
    checkState(equilibrium, demand);

    for (const mode of ['synchronous', 'gradual']) {
      const fixed = B.nextDay(model, demand, equilibrium.flows, mode, 0.18).state;
      const error = Math.max(...fixed.flows.map((x, j) => Math.abs(x - equilibrium.flows[j])));
      maxStationaryFixedPointError = Math.max(maxStationaryFixedPointError, error);
      assert.ok(error < 1e-8, {model: model.id, demand, mode, equilibrium, fixed});
    }

    for (const initial of [
      B.preShortcutSplit(demand),
      B.perturbedEquilibrium(model, demand),
      equilibrium.flows
    ]) {
      for (const config of [
        {mode: 'synchronous', step: 1},
        {mode: 'gradual', step: 0.05},
        {mode: 'gradual', step: 0.18},
        {mode: 'gradual', step: 0.5}
      ]) {
        const trace = B.simulate(model, demand, initial, {days: 120, ...config});
        trace.states.forEach(point => checkState(point, demand));
        cases += 1;
      }
    }
  }
}

const original = B.MODELS.original;
const teaching = B.MODELS.teaching;
assert.equal(B.exactEquilibrium(teaching, 4).mean, 80);
assert.deepEqual(B.exactEquilibrium(original, 6).flows, [2, 2, 2]);
assert.equal(B.exactEquilibrium(original, 6).mean, 92);
assert.deepEqual(B.exactEquilibrium(original, 20).flows, [10, 10, 0]);

const initial = B.preShortcutSplit(6);
const sync = B.simulate(original, 6, initial, {days: 40, mode: 'synchronous'});
assert.deepEqual(sync.states[0].flows, [3, 3, 0]);
assert.deepEqual(sync.states[1].flows, [0, 0, 6]);
assert.deepEqual(sync.states[2].flows, [3, 3, 0]);
const gradual18 = B.simulate(original, 6, initial, {days: 400, mode: 'gradual', step: 0.18});
const gradual05 = B.simulate(original, 6, initial, {days: 400, mode: 'gradual', step: 0.05});
const syncRange = B.oscillationRange(sync);
const gradual18Range = B.oscillationRange(gradual18);
const gradual05Range = B.oscillationRange(gradual05);
assert.equal(syncRange, 6);
assert.ok(gradual18Range > 0 && gradual18Range < syncRange);
assert.ok(gradual05Range > 0 && gradual05Range < gradual18Range);

for (const mode of ['synchronous', 'gradual']) {
  const zero = B.simulate(original, 0, [0, 0, 0], {days: 20, mode, step: 0.18});
  zero.states.forEach(point => {
    assert.deepEqual(point.flows, [0, 0, 0]);
    assert.equal(point.mean, null);
  });
}

for (const fn of [
  () => B.simulate(original, 1, [1, 0, 0], {days: -1}),
  () => B.nextDay(original, 1, [1, 0, 0], 'gradual', 0),
  () => B.nextDay(original, 1, [1, 0, 0], 'unknown', 0.1),
  () => B.measure(original, 2, [1, 0, 0])
]) assert.throws(fn, RangeError);

const summary = {
  status: 'PASS',
  cases,
  statesChecked,
  demandGridPointsPerModel: 101,
  horizons: {broadSweep: 120, oscillationProbe: 400},
  maxConservationError,
  minimumFlow,
  maxStationaryFixedPointError,
  canonicalOscillation: {
    model: 'original', demand: 6, initial: [3, 3, 0],
    synchronousShortcutRange: syncRange,
    gradualShortcutRangeAt018: gradual18Range,
    gradualShortcutRangeAt005: gradual05Range
  },
  checks: [
    'nonnegativity and finite values',
    'demand conservation',
    'zero-demand behavior',
    'every sampled exact Wardrop allocation is fixed by both update rules',
    'source numerical cases',
    'canonical synchronous two-cycle',
    'smaller constant steps reduce canonical late-window oscillation range',
    'explicit invalid-call checks reject their enumerated inputs; arithmetic overflow is tested separately'
  ],
  limitations: 'Deterministic finite sweeps over two toy models; not empirical calibration or a proof for other networks.'
};

const output = path.join(__dirname, 'output', 'model-tests.json');
fs.mkdirSync(path.dirname(output), {recursive: true});
fs.writeFileSync(output, `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
