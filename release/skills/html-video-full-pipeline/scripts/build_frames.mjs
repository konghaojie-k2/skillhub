#!/usr/bin/env node
// build_frames.mjs — multi-frame builder. Writes a ContentGraph + per-frame
// HTMLs onto a project via the @html-video/core orchestrator (the CLI is
// single-frame only; this is the multi-frame path).
//
// Usage (run from the html-video repo root):
//   node scripts/build_frames.mjs <projectId> <framesDir> [graphSpec.json]
//
//   <framesDir>     directory of NN-<nodeId>.html files (e.g. 01-hook.html).
//                   The number sets order; the <nodeId> must match a graph node.
//   [graphSpec.json] optional. Shape:
//   {
//     "intent": "product-intro",
//     "synopsis": "one-paragraph thesis",
//     "defaultDurationSec": 5,
//     "nodes": [ { "id":"hook", "label":"Hook", "text":"...", "frameIntent":"statement", "durationSec":5 }, ... ],
//     "images": { "__IMG_1__": "C:/abs/path/1.png" }   // markers inlined as base64 data URIs
//   }
//   If omitted, nodes are derived from the frame filenames (kind=text, empty
//   text, defaultDurationSec=5) and sequence edges are chained in file order.
//
// Per-frame narration sync (narrate_frames.mjs) re-paces each frame afterward,
// so the durations here are placeholders.

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname, isAbsolute } from 'node:path';

function findProjectRoot(start) {
  let cur = start;
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(cur, 'pnpm-workspace.yaml')) && existsSync(join(cur, '.html-video'))) return cur;
    const parent = dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }
  throw new Error(`Could not find html-video project root from ${start}`);
}

const [, , projectId, framesDirArg, graphSpecPath] = process.argv;
if (!projectId || !framesDirArg) {
  console.error('Usage: node build_frames.mjs <projectId> <framesDir> [graphSpec.json]');
  process.exit(2);
}
const projectRoot = findProjectRoot(process.cwd());
const framesDir = isAbsolute(framesDirArg) ? framesDirArg : join(projectRoot, framesDirArg);

const coreEntry = 'file://' + join(projectRoot, 'packages', 'core', 'dist', 'index.js').replace(/\\/g, '/');
const hfEntry = 'file://' + join(projectRoot, 'packages', 'adapter-hyperframes', 'dist', 'index.js').replace(/\\/g, '/');
const { ProjectOrchestrator, ProjectStore, TemplateRegistry, EngineRegistry, AssetStore } = await import(coreEntry);
const hfAdapter = (await import(hfEntry)).default;

// ---- discover frame files (NN-<nodeId>.html) ----
const files = readdirSync(framesDir).filter((f) => /^\d+-.+\.html$/.test(f)).sort();
if (files.length === 0) { console.error(`No NN-<nodeId>.html files in ${framesDir}`); process.exit(2); }
const fileNodeIds = files.map((f) => f.replace(/^\d+-/, '').replace(/\.html$/, ''));

// ---- build the content graph ----
const spec = graphSpecPath ? JSON.parse(readFileSync(graphSpecPath, 'utf8')) : {};
const defDur = spec.defaultDurationSec ?? 5;
const specById = Object.fromEntries((spec.nodes ?? []).map((n) => [n.id, n]));
const nodes = fileNodeIds.map((id) => {
  const s = specById[id] ?? {};
  return {
    id,
    kind: s.kind ?? 'text',
    label: s.label ?? id,
    text: s.text ?? '',
    durationSec: s.durationSec ?? defDur,
    frameIntent: s.frameIntent ?? 'statement',
  };
});
const edges = nodes.slice(0, -1).map((n, i) => ({ from: n.id, to: nodes[i + 1].id, kind: 'sequence', reason: 'narrative order' }));
const graph = {
  schemaVersion: 1,
  intent: spec.intent ?? 'product-intro',
  synopsis: spec.synopsis ?? '',
  nodes,
  edges,
};

// ---- image markers → base64 data URIs ----
const images = spec.images ?? {};
function dataUri(file) {
  const p = isAbsolute(file) ? file : join(projectRoot, file);
  const b = readFileSync(p);
  const ext = (p.split('.').pop() || 'png').toLowerCase();
  const mime = ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : ext === 'webp' ? 'image/webp' : 'image/png';
  return `data:${mime};base64,${b.toString('base64')}`;
}

const engines = new EngineRegistry(); engines.register(hfAdapter);
const templates = new TemplateRegistry(); await templates.scan(join(projectRoot, 'templates'));
const projects = new ProjectStore(projectRoot);
const assets = new AssetStore({ projectRoot });
const orch = new ProjectOrchestrator({ projectRoot, engines, templates, projects, assets });

const { graphPath } = await orch.writeContentGraph(projectId, graph);
console.log(`[graph] wrote ${graphPath} (${nodes.length} nodes)`);

for (const fname of files) {
  const nodeId = fname.replace(/^\d+-/, '').replace(/\.html$/, '');
  let html = readFileSync(join(framesDir, fname), 'utf8');
  for (const [marker, file] of Object.entries(images)) {
    if (html.includes(marker)) html = html.split(marker).join(dataUri(file));
  }
  const { frame } = await orch.writeFrameHtml(projectId, nodeId, html);
  console.log(`[frame] ${nodeId} -> order=${frame.order} dur=${frame.durationSec}s`);
}

const final = await orch.load(projectId);
console.log(`[done] project status=${final.status} frames=${final.frames?.length}`);
