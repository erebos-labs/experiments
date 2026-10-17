/* Two unobstructed point receivers; far-field plane waves, no HRTF. */
(function (root) {
  'use strict';
  const C = 343, D = 0.18, MAX_US = 1e6 * D / C;
  const rad = d => d * Math.PI / 180;
  const deg = r => r * 180 / Math.PI;
  const wrap = d => ((d + 180) % 360 + 360) % 360 - 180;
  function direction(azimuth, elevation = 0) {
    const a = rad(azimuth), e = rad(elevation);
    return [Math.sin(a) * Math.cos(e), Math.cos(a) * Math.cos(e), Math.sin(e)];
  }
  function delayVector(v, yaw = 0, baselineTilt = 0) {
    // baselineTilt tilts the receiver baseline upward (a roll-like rotation), not pitch.
    // Standard yaw-only receiver axis is [cos(yaw), -sin(yaw), 0].
    const y = rad(yaw), p = rad(baselineTilt);
    return MAX_US * (v[0] * Math.cos(y) * Math.cos(p) - v[1] * Math.sin(y) * Math.cos(p) + v[2] * Math.sin(p));
  }
  function delay(azimuth, yaw = 0, elevation = 0) {
    return delayVector(direction(azimuth, elevation), yaw);
  }
  function mirror(azimuth) { return wrap(180 - azimuth); }
  function exactDelay(azimuth, yaw = 0, range = 2, elevation = 0) {
    if (!(range > D / 2)) throw new RangeError('range must exceed half the receiver separation');
    const v = direction(azimuth, elevation), h = rad(yaw);
    const right = [D / 2 * Math.cos(h), -D / 2 * Math.sin(h), 0];
    const distance = sign => Math.hypot(...v.map((x, i) => range * x - sign * right[i]));
    return 1e6 * (distance(-1) - distance(1)) / C;
  }
  function candidates(azimuth, yaw, tolerance = 15, step = 0.25) {
    // These are deterministic consistency sets, not probabilities or perceptual thresholds.
    if (![azimuth, yaw, tolerance, step].every(Number.isFinite) || tolerance < 0 || step < 0.025 || step > 360) throw new RangeError('finite inputs and a grid step from 0.025 to 360 degrees required');
    const first = delay(azimuth), second = delay(azimuth, yaw), single = [], both = [];
    const count = Math.ceil(360 / step); // At most 14,400 samples, independent of floating-point progress.
    for (let i = 0; i < count; i++) {
      const a = -180 + i * step;
      if (a >= 180 - step * 1e-8) break;
      const pass = Math.abs(delay(a) - first) <= tolerance + 1e-9;
      if (pass) single.push(a);
      if (pass && Math.abs(delay(a, yaw) - second) <= tolerance + 1e-9) both.push(a);
    }
    return { single, both, first, second, step, tolerance };
  }
  function reconstruct(first, second, yaw) {
    const h = rad(yaw), s = Math.sin(h);
    if (Math.abs(s) < 1e-12) return null;
    const x = first / MAX_US;
    const y = (x * Math.cos(h) - second / MAX_US) / s;
    return { azimuth: wrap(deg(Math.atan2(x, y))), x, y, norm: Math.hypot(x, y) };
  }
  function cone(q, around) {
    const r = Math.sqrt(Math.max(0, 1 - q * q)), a = rad(around);
    return [q, r * Math.cos(a), r * Math.sin(a)];
  }
  function envelope(t, duration = 2.5) {
    if (t < 0 || t >= duration) return 0;
    const fade = 0.025;
    const gate = Math.min(1, t / fade, (duration - t) / fade);
    // A smooth on/off pattern makes the shifted waveform inspectable at the onset.
    const pulse = t % 0.5;
    const p = pulse < 0.36 ? Math.min(1, pulse / fade, (0.36 - pulse) / fade) : 0;
    return Math.sin(Math.PI / 2 * Math.max(0, gate)) ** 2 * Math.sin(Math.PI / 2 * Math.max(0, p)) ** 2;
  }
  function signal(t, duration = 2.5) {
    if (t < 0 || t >= duration) return 0;
    return envelope(t, duration) * (
      0.34 * Math.sin(2 * Math.PI * 220 * t) +
      0.28 * Math.sin(2 * Math.PI * 330 * t + 0.7) +
      0.22 * Math.sin(2 * Math.PI * 440 * t + 1.3) +
      0.16 * Math.sin(2 * Math.PI * 550 * t + 2.1)
    );
  }
  function stereo(tauUs, gain = 0, sampleRate = 48000, duration = 2.5) {
    if (!Number.isFinite(tauUs) || Math.abs(tauUs) > MAX_US + 1e-6) throw new RangeError('delay outside model');
    if (!Number.isFinite(gain) || gain < 0 || gain > 0.04) throw new RangeError('gain outside conservative digital bound');
    if (!Number.isInteger(sampleRate) || sampleRate < 8000 || sampleRate > 192000 || !Number.isFinite(duration) || duration < 0.1 || duration > 3) throw new RangeError('bounded synthesis only');
    const tau = tauUs * 1e-6, leftDelay = 0.02 + Math.max(tau, 0), rightDelay = 0.02 + Math.max(-tau, 0);
    const n = Math.ceil((duration + 0.021) * sampleRate), left = new Float32Array(n), right = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      left[i] = gain * signal(i / sampleRate - leftDelay, duration);
      right[i] = gain * signal(i / sampleRate - rightDelay, duration);
    }
    return { left, right, sampleRate, duration: n / sampleRate, leftDelay, rightDelay, gain, tauUs };
  }
  const api = { C, D, MAX_US, rad, deg, wrap, direction, delayVector, delay, mirror, exactDelay, candidates, reconstruct, cone, signal, envelope, stereo };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.SoundModel = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
