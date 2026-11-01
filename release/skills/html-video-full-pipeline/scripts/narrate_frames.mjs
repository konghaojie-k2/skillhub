#!/usr/bin/env node
// narrate_frames.mjs — per-frame narration with audio/video sync for multi-frame
// projects. TTS each segment, ffprobe-measure it, re-pace every frame's
// durationSec to its narration length, concat into one narration.mp3, then wire
// it into the project soundtrack (preserving any existing music). This is what
// eliminates audio/video drift when narration segments vary in length.
//
// Usage (run from the html-video repo root):
//   node scripts/narrate_frames.mjs <projectId> <segments.json> [voice-id-override]
//
//   <segments.json>  array in frame order, each keyed to a graphNodeId:
//     [ { "id": "hook", "text": "..." }, { "id": "reading", "text": "..." }, ... ]
//
// Region-aware voice: China key (api.minimaxi.com) → male-qn-qingse / Chinese.

import { readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { join, dirname, isAbsolute } from 'node:path';
import { spawn } from 'node:child_process';

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

const [, , projectId, segmentsPath, voiceOverride] = process.argv;
if (!projectId || !segmentsPath) {
  console.error('Usage: node narrate_frames.mjs <projectId> <segments.json> [voice-id-override]');
  process.exit(2);
}
const projectRoot = findProjectRoot(process.cwd());
const segments = JSON.parse(readFileSync(isAbsolute(segmentsPath) ? segmentsPath : join(projectRoot, segmentsPath), 'utf8'));
if (!Array.isArray(segments) || segments.length === 0) { console.error('segments.json must be a non-empty array'); process.exit(2); }

// ---- resolve ffmpeg/ffprobe (PATH first, then Windows fallback) ----
function resolveBin(name) {
  const cands = [
    name,
    `C:/ffmpeg-8.1.1-essentials_build/bin/${name}.exe`,
    `C:/ffmpeg-7.1.1-essentials_build/bin/${name}.exe`,
    `C:/ffmpeg-6.1.1-essentials_build/bin/${name}.exe`,
    `C:/ffmpeg/bin/${name}.exe`,
  ];
  for (const c of cands) { if (c === name || existsSync(c)) return c; }
  return name;
}
const FFMPEG = resolveBin('ffmpeg');
const FFPROBE = resolveBin('ffprobe');

// ---- resolve creds ----
let creds = null;
try {
  const cfg = JSON.parse(readFileSync(join(projectRoot, '.html-video', 'media-config.json'), 'utf8'));
  if (cfg.minimax?.apiKey) creds = { apiKey: cfg.minimax.apiKey, baseUrl: cfg.minimax.baseUrl || 'https://api.minimax.io/v1' };
} catch {}
if (!creds) {
  const k = process.env.OD_MINIMAX_API_KEY || process.env.MINIMAX_API_KEY;
  if (k) creds = { apiKey: k, baseUrl: process.env.OD_MINIMAX_BASE_URL || process.env.MINIMAX_BASE_URL || 'https://api.minimax.io/v1' };
}
if (!creds) { console.error('No MiniMax credentials.'); process.exit(3); }
const isChina = creds.baseUrl.includes('minimaxi.com');
const voiceId = voiceOverride || (isChina ? 'male-qn-qingse' : 'English_Grace');
const languageBoost = isChina ? 'Chinese' : 'English';

const coreEntry = 'file://' + join(projectRoot, 'packages', 'core', 'dist', 'index.js').replace(/\\/g, '/');
const { generateTts, ProjectStore, AssetStore } = await import(coreEntry);

const tmpDir = join(projectRoot, '.html-video', 'assets', projectId, '_narr-clips');
mkdirSync(tmpDir, { recursive: true });

function ffprobeDuration(file) {
  return new Promise((resolve, reject) => {
    const p = spawn(FFPROBE, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file],
      { stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '', err = '';
    p.stdout.on('data', (d) => (out += d));
    p.stderr.on('data', (d) => (err += d));
    p.on('error', reject);
    p.on('close', (code) => (code === 0 ? resolve(parseFloat(out.trim())) : reject(new Error(`ffprobe exit ${code}: ${err}`))));
  });
}

// ---- Step 1: TTS each segment + measure ----
const clipPaths = [];
const durations = [];
for (let i = 0; i < segments.length; i++) {
  const s = segments[i];
  console.log(`[tts] ${i + 1}/${segments.length}  ${s.id}  (${s.text.length} chars)...`);
  const r = await generateTts({ text: s.text, voiceId, languageBoost, creds });
  const clipPath = join(tmpDir, `${String(i + 1).padStart(2, '0')}-${s.id}.mp3`);
  writeFileSync(clipPath, r.bytes);
  let dur;
  try { dur = await ffprobeDuration(clipPath); if (Number.isNaN(dur)) throw new Error('NaN'); }
  catch (e) { if (r.durationSec > 0) { dur = r.durationSec; console.log(`[tts]    ffprobe fail; API dur=${dur}`); } else throw e; }
  clipPaths.push(clipPath);
  durations.push({ id: s.id, dur });
  console.log(`[tts]    ${dur.toFixed(2)}s`);
}
const total = durations.reduce((a, d) => a + d.dur, 0);
console.log(`\n[plan] ${segments.length} clips, total ${total.toFixed(2)}s`);

// ---- Step 2: concat into one narration.mp3 ----
const listFile = join(tmpDir, 'list.txt');
writeFileSync(listFile, clipPaths.map((p) => `file '${p.replace(/\\/g, '/')}'`).join('\n'), 'utf8');
const outNarration = join(projectRoot, '.html-video', 'assets', projectId, 'narration.mp3');
await new Promise((resolve, reject) => {
  const p = spawn(FFMPEG, ['-y', '-f', 'concat', '-safe', '0', '-i', listFile, '-c', 'copy', outNarration], { stdio: 'inherit' });
  p.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg concat exit ${code}`))));
});
console.log(`[mux] concat -> ${outNarration}`);

// ---- Step 3: register asset, set soundtrack (preserve music), re-pace frames ----
const projects = new ProjectStore(projectRoot);
const assets = new AssetStore({ projectRoot });
const asset = await assets.addFileAsset(projectId, outNarration, [], `Per-frame narration (${segments.length} segments)`);
const project = await projects.load(projectId);
if (!project.assets.find((a) => a.id === asset.id)) project.assets.push(asset);
project.soundtrack = {
  ...(project.soundtrack ?? {}),
  narrationAssetId: asset.id,
  narrationVolumeDb: project.soundtrack?.narrationVolumeDb ?? 0,
  ...(project.soundtrack?.musicAssetId && { musicVolumeDb: project.soundtrack?.musicVolumeDb ?? -18 }),
};
const durById = Object.fromEntries(durations.map((d) => [d.id, d.dur]));
// floor 3s so short frames still breathe; +0.4s tail so audio isn't clipped.
project.frames = (project.frames ?? []).map((f) => ({
  ...f,
  durationSec: Math.max(3, Math.ceil((durById[f.graphNodeId] ?? f.durationSec) + 0.4)),
}));
await projects.save(project);
rmSync(tmpDir, { recursive: true, force: true });

const sum = project.frames.reduce((a, f) => a + f.durationSec, 0);
console.log(`[wire] narration asset=${asset.id}; frames re-paced; total video=${sum}s`);
project.frames.sort((a, b) => a.order - b.order).forEach((f) => console.log(`  ${f.order}  ${f.graphNodeId.padEnd(12)} ${f.durationSec}s`));
