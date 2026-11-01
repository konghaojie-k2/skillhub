#!/usr/bin/env node
// generate_bgm.mjs — MiniMax music-1.5 wrapper for html-video.
// Usage: node generate_bgm.mjs "<style prompt>" <project-id>
// Takes ~50s. Writes .html-video/assets/<project-id>/bgm.mp3 AND wires it into
// the project: registers the asset and sets project.soundtrack.musicAssetId
// (preserving any existing narration). Without this wiring the export-time mux
// silently drops the music — see references/audio-api.md.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const projectRoot = process.cwd();
const [, , prompt, projectId] = process.argv;
if (!prompt || !projectId) {
  console.error('Usage: node generate_bgm.mjs "<style prompt>" <project-id>');
  console.error('Example: node generate_bgm.mjs "cinematic electronic 80bpm, no vocals" proj_abc123');
  process.exit(2);
}

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

const coreEntry = 'file://' + join(projectRoot, 'packages', 'core', 'dist', 'index.js').replace(/\\/g, '/');
const { generateMusic, ProjectStore, AssetStore } = await import(coreEntry);

console.log(`[bgm] prompt: "${prompt}"  (music-1.5, synchronous ~50s wait)`);
const music = await generateMusic({ prompt, instrumental: true, creds });

const outDir = join(projectRoot, '.html-video', 'assets', projectId);
mkdirSync(outDir, { recursive: true });
const outPath = join(outDir, 'bgm.mp3');
writeFileSync(outPath, music.bytes);
console.log(`[bgm] wrote ${music.bytes.length} bytes -> ${outPath}`);

// ---- Wire into the project (register asset + set soundtrack) ----
const projects = new ProjectStore(projectRoot);
const assets = new AssetStore({ projectRoot });
const asset = await assets.addFileAsset(projectId, outPath, [], 'Background music');
const project = await projects.load(projectId);
if (!project.assets.find((a) => a.id === asset.id)) project.assets.push(asset);
project.soundtrack = {
  ...(project.soundtrack ?? {}),
  musicAssetId: asset.id,
  musicVolumeDb: project.soundtrack?.musicVolumeDb ?? -18,
  ...(project.soundtrack?.narrationAssetId && { narrationVolumeDb: project.soundtrack?.narrationVolumeDb ?? 0 }),
};
await projects.save(project);
console.log(`[wire] music asset=${asset.id} registered; soundtrack.musicAssetId set (-18dB duck)`);
