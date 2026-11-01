#!/usr/bin/env node
// generate_narration.mjs — MiniMax TTS wrapper for html-video (single segment).
// Usage: node generate_narration.mjs "<text>" <project-id> [voice-id-override]
// Region detection: if .html-video/media-config.json has api.minimaxi.com → Chinese voice.
//
// Writes .html-video/assets/<project-id>/narration.mp3 AND wires it into the
// project: registers the asset in project.assets and sets project.soundtrack
// .narrationAssetId (preserving any existing music). Without this wiring the
// export-time mux silently produces a SILENT video — see references/audio-api.md.
// For multi-frame projects with per-frame sync, use narrate_frames.mjs instead.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const projectRoot = process.cwd();
const [, , text, projectId, voiceOverride] = process.argv;
if (!text || !projectId) {
  console.error('Usage: node generate_narration.mjs "<text>" <project-id> [voice-id-override]');
  process.exit(2);
}

// Resolve creds: config file > env
let creds = null;
try {
  const cfg = JSON.parse(readFileSync(join(projectRoot, '.html-video', 'media-config.json'), 'utf8'));
  if (cfg.minimax?.apiKey) creds = { apiKey: cfg.minimax.apiKey, baseUrl: cfg.minimax.baseUrl || 'https://api.minimax.io/v1' };
} catch {}
if (!creds) {
  const k = process.env.OD_MINIMAX_API_KEY || process.env.MINIMAX_API_KEY;
  if (k) creds = { apiKey: k, baseUrl: process.env.OD_MINIMAX_BASE_URL || process.env.MINIMAX_BASE_URL || 'https://api.minimax.io/v1' };
}
if (!creds) {
  console.error('No MiniMax credentials. Configure in .html-video/media-config.json or set OD_MINIMAX_API_KEY env.');
  process.exit(3);
}

const isChina = creds.baseUrl.includes('minimaxi.com');
const voiceId = voiceOverride || (isChina ? 'male-qn-qingse' : 'English_Grace');
const languageBoost = isChina ? 'Chinese' : 'English';

const coreEntry = 'file://' + join(projectRoot, 'packages', 'core', 'dist', 'index.js').replace(/\\/g, '/');
const { generateTts, ProjectStore, AssetStore } = await import(coreEntry);

console.log(`[tts] baseUrl=${creds.baseUrl} voice=${voiceId} lang=${languageBoost} chars=${text.length}`);
const tts = await generateTts({ text, voiceId, languageBoost, creds });

const outDir = join(projectRoot, '.html-video', 'assets', projectId);
mkdirSync(outDir, { recursive: true });
const outPath = join(outDir, 'narration.mp3');
writeFileSync(outPath, tts.bytes);
console.log(`[tts] wrote ${tts.bytes.length} bytes -> ${outPath}`);
if (tts.durationSec) console.log(`[tts] duration: ${tts.durationSec}s`);

// ---- Wire into the project (register asset + set soundtrack) ----
const projects = new ProjectStore(projectRoot);
const assets = new AssetStore({ projectRoot });
const asset = await assets.addFileAsset(projectId, outPath, [], 'Narration (single segment)');
const project = await projects.load(projectId);
if (!project.assets.find((a) => a.id === asset.id)) project.assets.push(asset);
project.soundtrack = {
  ...(project.soundtrack ?? {}),
  narrationAssetId: asset.id,
  narrationVolumeDb: project.soundtrack?.narrationVolumeDb ?? 0,
  ...(project.soundtrack?.musicAssetId && { musicVolumeDb: project.soundtrack?.musicVolumeDb ?? -18 }),
};
await projects.save(project);
console.log(`[wire] narration asset=${asset.id} registered; soundtrack.narrationAssetId set`);
