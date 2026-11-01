# MiniMax audio API reference

The skill calls into `@html-video/core` (already built at `packages/core/dist/`). The two functions you need:

## resolveMinimaxCredentials

```ts
import { resolveMinimaxCredentials } from '@html-video/core';

const creds = resolveMinimaxCredentials();
// { apiKey: string, baseUrl: string } | null
```

**Reads from env only** (NOT from `.html-video/media-config.json`):
- `OD_MINIMAX_API_KEY` → `MINIMAX_API_KEY`
- `OD_MINIMAX_BASE_URL` → `MINIMAX_BASE_URL` → `https://api.minimax.io/v1`

The Studio UI persists keys to `.html-video/media-config.json`, and `MediaConfigStore` (in `@html-video/cli`) is what reads it. If you're scripting outside the Studio flow, either:
1. Set the env var in the same shell
2. Or read the file yourself and pass `creds` explicitly to the generators (this is what the skill's wrapper scripts do)

## generateTts

```ts
import { generateTts } from '@html-video/core';

const result = await generateTts({
  text: string,                    // required, 1-2 sentences typically
  voiceId?: string,                // default: 'male-qn-qingse' (China) — pick regional
  languageBoost?: string,          // 'Chinese' | 'English' | 'auto' — helps prosody
  speed?: number,                  // default 1.0
  vol?: number,                    // default 1.0
  pitch?: number,                  // default 0
  creds: { apiKey, baseUrl },      // required
  signal?: AbortSignal,            // optional, for cancellation
});
// returns: { bytes: Buffer, ext: '.mp3', providerNote: string, durationSec?: number }
```

**Throws** `HtmlVideoError('render-failed', ...)` on:
- 401: bad key
- 2054: voice id not exist in this region
- 4xx/5xx with non-zero `base_resp.status_code`
- network timeout (120s)

**Common voices**:
- China: `male-qn-qingse`, `female-shaonv`, `male-qn-jingying`
- International: `English_Grace`, `English_Passion`, `English_Rachel`

## generateMusic

```ts
import { generateMusic } from '@html-video/core';

const result = await generateMusic({
  prompt: string,            // required, style description in English
  instrumental: boolean,     // music-1.5 ignores this and requires 'lyrics' field
  creds: { apiKey, baseUrl },
});
// returns: { bytes: Buffer, ext: '.mp3', providerNote: string }
```

**Model**: hardcoded `music-1.5` (synchronous, ~50s). The newer `music-2.6` hangs indefinitely for our key — do not switch.

**Takes ~50s** synchronously. Plan UI accordingly (show a "generating music..." spinner).

**Output**: ~50s of MP3 at 256kbps/44.1kHz. File size typically 1.5-2.5 MB.

## Useful prompt patterns

For music:
- `"cinematic electronic, confident build, modern editorial, 80bpm, no vocals"`
- `"ambient piano, hopeful, gentle arpeggios, 70bpm"`
- `"lo-fi hip hop, study beats, mellow, 85bpm"`
- `"orchestral strings, dramatic, building tension, 100bpm"`

For narration:
- Keep it short (1-2 sentences) — long narration is hard to time against the visual
- Write it to match the visual beats: opening line ≈ big title; closing line ≈ final state
- For multi-frame templates, ask Studio's `draft-narration` API to auto-generate per-frame lines

## Wiring audio into a project (critical — avoids silent videos)

`generateTts` / `generateMusic` only return bytes. Writing the MP3 to
`.html-video/assets/<id>/` is **not enough** — `project-render` mux resolves
audio strictly from `project.soundtrack` (the asset IDs) plus `project.assets`
(the registered asset records). There is **no auto-discovery** of MP3 files on
disk. If either is missing, `applySoundtrack` silently returns and you get a
**video with no audio** — yet the render still reports `status: "rendered"`.

Two pitfalls that both produce a silent video:
1. **Asset not registered.** `AssetStore.addFileAsset()` writes the file but does
   NOT add it to `project.assets`. You must push the returned asset into
   `project.assets` and `projects.save()` — OR use the higher-level
   `ProjectOrchestrator.addFileAsset()` which does both. (Same-name methods,
   different behavior — easy to grab the wrong one.)
2. **Soundtrack not set.** You must set `project.soundtrack.narrationAssetId` /
   `.musicAssetId` to the registered asset IDs.

The skill's `generate_narration.mjs`, `generate_bgm.mjs`, and `narrate_frames.mjs`
all do both steps. Always finish with `verify_output.sh <mp4> --require-audio`
to assert the audio actually landed.

## Mux behavior in `project-render`

When a project has `narrationAssetId` and/or `musicAssetId` set in its soundtrack, `project-render` automatically:
1. Renders the visual to a silent MP4
2. Muxes in the audio with these defaults:
   - `musicVolumeDb = -18` (well below voice)
   - `narrationVolumeDb = 0`
   - `afade=t=in:st=0:d=0.5` on music (0.5s fade in)
   - `afade=t=out:st=50:d=1.5` on music (1.5s fade out)
   - `-shortest` (truncate to video length)
3. Encodes audio to AAC 192kbps stereo

You can override the volumes in the Studio's soundtrack panel, or by setting `soundtrack.musicVolumeDb` / `narrationVolumeDb` on the project object directly.
