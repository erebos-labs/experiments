#!/usr/bin/env node
"use strict";

// Execute the actual inline page script against bounded DOM/canvas stubs.
// This checks computational UI behavior without claiming a browser-engine test.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "src", "spinning-disk", "index.html"), "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1);

function parseAttributes(raw) {
  const attrs = {};
  let i = raw.search(/\s/);
  if (i < 0) return attrs;
  while (i < raw.length) {
    while (/\s/.test(raw[i] ?? "")) i += 1;
    if (i >= raw.length || raw[i] === "/" || raw[i] === ">") break;
    const start = i;
    while (i < raw.length && !/[\s=/>]/.test(raw[i])) i += 1;
    const name = raw.slice(start, i).toLowerCase();
    while (/\s/.test(raw[i] ?? "")) i += 1;
    let value = "";
    if (raw[i] === "=") {
      i += 1;
      while (/\s/.test(raw[i] ?? "")) i += 1;
      if (raw[i] === '"' || raw[i] === "'") {
        const quote = raw[i++];
        const valueStart = i;
        while (i < raw.length && raw[i] !== quote) i += 1;
        value = raw.slice(valueStart, i);
        if (raw[i] === quote) i += 1;
      } else {
        const valueStart = i;
        while (i < raw.length && !/[\s>]/.test(raw[i])) i += 1;
        value = raw.slice(valueStart, i);
      }
    }
    if (name) attrs[name] = value;
  }
  return attrs;
}

function tagEnd(source, start) {
  let quote = null;
  for (let i = start; i < source.length; i += 1) {
    const char = source[i];
    if (quote) {
      if (char === quote) quote = null;
    } else if (char === '"' || char === "'") {
      quote = char;
    } else if (char === ">") {
      return i;
    }
  }
  throw new Error("unterminated HTML tag");
}

function parseTags(source) {
  const tokens = [];
  let cursor = 0;
  while (cursor < source.length) {
    const open = source.indexOf("<", cursor);
    if (open < 0) break;
    if (source.startsWith("<!--", open)) {
      const close = source.indexOf("-->", open + 4);
      cursor = close < 0 ? source.length : close + 3;
      continue;
    }
    const end = tagEnd(source, open + 1);
    const raw = source.slice(open + 1, end).trim();
    if (!raw || raw.startsWith("!") || raw.startsWith("?")) {
      cursor = end + 1;
      continue;
    }
    const closing = raw.startsWith("/");
    const nameMatch = raw.slice(closing ? 1 : 0).match(/^([A-Za-z][\w:-]*)/);
    if (!nameMatch) {
      cursor = end + 1;
      continue;
    }
    const tag = nameMatch[1].toLowerCase();
    tokens.push({ kind: closing ? "end" : "start", tag, attrs: closing ? {} : parseAttributes(raw) });
    if (!closing && (tag === "script" || tag === "style")) {
      const lower = source.toLowerCase();
      const closeStart = lower.indexOf(`</${tag}`, end + 1);
      if (closeStart < 0) throw new Error(`missing </${tag}>`);
      const closeEnd = tagEnd(source, closeStart + 2 + tag.length);
      tokens.push({ kind: "end", tag, attrs: {} });
      cursor = closeEnd + 1;
    } else {
      cursor = end + 1;
    }
  }
  return tokens;
}

function elementManifest(source) {
  const manifest = new Map();
  let activeSelect = null;
  for (const token of parseTags(source)) {
    if (token.kind === "end") {
      if (token.tag === "select") activeSelect = null;
      continue;
    }
    const id = token.attrs.id;
    if (id) {
      assert(!manifest.has(id), `duplicate HTML ID: ${id}`);
      manifest.set(id, { tag: token.tag, attrs: token.attrs, defaultValue: undefined });
    }
    if (token.tag === "select") activeSelect = id || null;
    if (token.tag === "option" && activeSelect) {
      const select = manifest.get(activeSelect);
      if (select.defaultValue === undefined || Object.hasOwn(token.attrs, "selected")) {
        select.defaultValue = token.attrs.value ?? "";
      }
    }
  }
  return manifest;
}

const requiredTags = {
  plot: "canvas", fitPlot: "canvas",
  mass: "input", radius: "input", density: "input", mu: "input", time: "input",
  windowMin: "input", noise: "input", offset: "input",
  trueN: "select", sampling: "select", fitMode: "select",
  massOut: "output", gapAngle: "b", fitN: "b", fitTf: "b", fitRms: "b",
};
function validateRequired(manifest) {
  for (const [id, expectedTag] of Object.entries(requiredTags)) {
    const spec = manifest.get(id);
    assert(spec, `missing required element: ${id}`);
    assert.equal(spec.tag, expectedTag, `${id} must be <${expectedTag}>`);
  }
  for (const id of ["mass", "radius", "density", "mu", "time", "windowMin", "noise", "offset"]) {
    const spec = manifest.get(id);
    assert.equal(spec.attrs.type, "range", `${id} must be a range input`);
    assert.notEqual(spec.attrs.value, undefined, `${id} must declare its default value`);
  }
  for (const id of ["trueN", "sampling", "fitMode"]) {
    assert.notEqual(manifest.get(id).defaultValue, undefined, `${id} must contain an option`);
  }
}

const manifest = elementManifest(html);
validateRequired(manifest);

const ghostManifest = elementManifest(`
  <div id="real"></div><!-- <input id="ghost-comment"> -->
  <script>const example = 'id="ghost-script"';</script>
`);
assert(ghostManifest.has("real"));
assert(!ghostManifest.has("ghost-comment"));
assert(!ghostManifest.has("ghost-script"));
assert.throws(
  () => validateRequired(elementManifest(html.replace('id="massOut"', 'data-id="massOut"'))),
  /missing required element: massOut/,
);
assert.throws(
  () => validateRequired(elementManifest(html.replace('<canvas id="plot"', '<div id="plot"'))),
  /plot must be <canvas>/,
);

const elements = new Map();
const context2d = new Proxy({}, {
  get(target, property) {
    if (!(property in target)) target[property] = () => {};
    return target[property];
  },
  set(target, property, value) { target[property] = value; return true; },
});
function element(id) {
  const spec = manifest.get(id);
  if (!spec) return null;
  if (!elements.has(id)) {
    const canvas = spec.tag === "canvas";
    const stub = {
      id,
      value: spec.defaultValue ?? spec.attrs.value ?? "",
      textContent: "",
      disabled: Object.hasOwn(spec.attrs, "disabled"),
      style: {},
      width: 0,
      height: 0,
      clientWidth: canvas ? (id === "plot" ? 688 : 612) : 120,
      clientHeight: canvas ? (id === "plot" ? 410 : 250) : 24,
      events: {},
      addEventListener(type, callback) { this.events[type] = callback; },
    };
    if (canvas) stub.getContext = (kind) => { assert.equal(kind, "2d"); return context2d; };
    elements.set(id, stub);
  }
  return elements.get(id);
}
const pageEvents = {};
const context = {
  console,
  Math,
  document: { getElementById: element },
  devicePixelRatio: 2,
  addEventListener(type, callback) { pageEvents[type] = callback; },
};
vm.createContext(context);
vm.runInContext(scripts[0][1], context, { filename: "spinning-disk-inline.js" });

assert.equal(element("massOut").textContent, "445 g");
assert.equal(element("gapAngle").textContent, "0.45°");
assert.equal(element("fitN").textContent, "0.444");
assert.equal(element("fitTf").textContent, "-0.07 ms");
assert.equal(element("fitRms").textContent, "0.0179");
assert.equal(element("offset").disabled, true);
assert.equal(element("plot").width, 1376);
assert.equal(element("fitPlot").width, 1224);

element("trueN").value = "0.5";
element("fitMode").value = "shifted";
element("offset").value = "-0.9";
element("mass").value = "800";
context.update();
context.fitUpdate();

assert.equal(element("massOut").textContent, "800 g");
assert.equal(element("crossAngle").textContent, "0.81°");
assert.equal(element("offset").disabled, false);
assert.equal(element("offsetOut").textContent, "-0.9 ms");
assert.equal(element("fitN").textContent, "0.475");
assert.equal(element("fitCloser").textContent, "1/2");
assert.equal(typeof pageEvents.resize, "function");

console.log("PASS spinning-disk inline JS: default render, DPR canvas sizing, model update, exponent/mode/offset controls, and dependent readouts");
