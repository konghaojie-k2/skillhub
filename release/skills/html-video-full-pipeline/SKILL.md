---
name: html-video-full-pipeline
description: End-to-end video creation workflow for the html-video project — turn a natural-language video idea into a complete MP4 with narration + background music. Use when the user is in the html-video repo (has pnpm-workspace.yaml + templates/) and wants to render a video clip: choose a template, fill in variables, generate AI narration via MiniMax TTS, generate AI background music via MiniMax music-1.5, render with Playwright/Chromium, and mux the audio with ffmpeg. Triggers on requests like "make a video about X", "render this idea into a clip", "用 html-video 做一段视频", or any task that needs the full template→HTML→screen-record→audio-mux pipeline. Pre-requisites: Node 20+, pnpm, ffmpeg on Windows (commonly unpacked at C:\ffmpeg-*-essentials_build\bin), Playwright Chromium (auto-bundled with the workspace), and a MiniMax API key (configured in .html-video/media-config.json via the Studio UI or set as OD_MINIMAX_API_KEY env).
---

# html-video-full-pipeline

End-to-end orchestration: **idea → template → HTML → screen-recording → AI narration → AI music → muxed MP4**.

The user is in the html-video repo. The job is to take a natural-language description of a video they want and produce a finished `.mp4` file with:
- animated HTML (from one of the 22+ templates in `templates/`)
- spoken narration (MiniMax TTS)
- background music (MiniMax music-1.5)
- all three mixed into a single H.264 + AAC MP4

## When to use

Use this skill when:
- User is in the html-video repo and asks to "make a video", "render this", "做一段视频"
- User has an idea/description and wants a finished clip
- User wants to iterate on a previous video (change text, swap template, re-render)

Do **not** use this skill for:
- Editing the html-video codebase itself (template authoring, adapter code, CLI changes)
- Studio UI work
- Anything that doesn't end in a video file

## Interactive-by-default

This skill runs in **6 stages**, each with a hard pause for user confirmation. Do not run all stages in one shot unless the user explicitly says so.

Stages:

| # | Stage | What it does | User confirms |
|---|---|---|---|
| 1 | `env` | Run pre-flight checks | env is OK |
| 2 | `template` | Search templates, pick one, inspect schema | template + variables |
| 3 | `project` | Create project + bind template + set variables | project config is right |
| 4 | `narration` | TTS the script | narration sounds right |
| 5 | `music` | Pick a music style (or accept a prompt), generate, audition | music is right |
| 6 | `render` | Render MP4 + verify | final output is good |

### Confirm keywords

After each stage, wait for the user to type one of:
- `y` / `yes` — proceed
- `n` / `no` — abort (user wants to fix something themselves)
- `redo` — re-run just this stage
- `skip` — skip this stage (only valid for narration/music)
- `q` / `quit` — exit immediately

If the user invoked this skill in a non-interactive way (e.g. `claude -p`), the default is `yes` for env/template/project, `skip` for narration/music, and `yes` for render. Use `--yes` flag if available, or document the non-interactive assumption to the user before running.

## Stage 1 · env (Discover environment)

Run `bash scripts/check_env.sh` (bash) to verify the environment is ready. It checks:
1. Node version ≥ 20
2. pnpm available
3. ffmpeg resolvable (PATH or Windows fallback `C:\ffmpeg-*-essentials_build\bin\ffmpeg.exe`)
4. Playwright Chromium present (under `%LOCALAPPDATA%\ms-playwright\`)
5. MiniMax API key configured (in `.html-video/media-config.json` OR `OD_MINIMAX_API_KEY` env)

**Success**: All five checks pass. If they don't, consult `references/troubleshooting.md` and fix before continuing.

After success, **pause and confirm with user**:
> Environment looks good. Continue to template selection? (y/n/redo)

## Stage 2 · template (Choose + plan)

Run the search and inspect the schema:

```bash
node packages/cli/dist/bin.js search-templates --intent "<user's idea, in 5-15 words>" --top 3
node packages/cli/dist/bin.js inspect-template <chosen-id>
```

Pick the top match. If the score is 0 and the user is flexible, ask which of the 3 they prefer. If unsure, default to `frame-bold-signal` (works for almost any "section divider / statement" use case).

**Show the user**:
- Top 3 template results with scores
- Your recommended pick
- The template's required input fields (from inspect)

**Pause and confirm with user**:
> Picked `<id>`. Required fields: [...]. Continue to project creation? (y/n/redo to see other options)

## Stage 3 · project (Create + bind + set vars)

Create the project, bind the template, and set the variables:

```bash
node packages/cli/dist/bin.js project-create --name "<short label for the video>"
node packages/cli/dist/bin.js project-set-template <project-id> --template <chosen-id>
```

Capture the `project_id`. Then write a JSON file with the template's required + optional fields, and:

```bash
node packages/cli/dist/bin.js project-set-vars <project-id> --vars-file /tmp/vars.json
```

If the user gave text in Chinese and the template is English-only (e.g. `frame-bold-signal`), translate key fields. If the template has `headline` as an array, distribute the user's message across up to 3 lines.

**Success**: Response echoes the variables back. If any required field is missing, the CLI will reject — add the field and retry.

**Show the user** the final vars JSON, then **pause**:
> Project `<project-id>` ready. Vars: {...}. Continue to narration? (y/n/redo)

### Multi-frame projects (content-graph + per-frame HTML)

The single-template path above is for one composition. For a **multi-frame video**
(a sequence of distinct full-screen frames — hook → body → outro), skip the
template binding and build the frames directly. The CLI is single-frame only, so
this path uses `scripts/build_frames.mjs`, which goes through the
`@html-video/core` orchestrator (`writeContentGraph` + `writeFrameHtml`).

1. Author one HTML file per frame in a directory, named `NN-<nodeId>.html`
   (e.g. `01-hook.html`, `02-body.html`, `03-outro.html`). The number sets
   order; `<nodeId>` keys the frame to a content-graph node. Each file is a
   self-contained 1920×1080 document. To embed screenshots/images robustly,
   put a marker like `__IMG_1__` in `src` and map it in the graph spec —
   `build_frames.mjs` inlines the file as a base64 data URI so the rendered
   HTML is path-independent.
2. Optionally write a `graphSpec.json` (intent, synopsis, per-node label/text/
   frameIntent/durationSec, and an `images` map). If omitted, nodes are derived
   from the filenames with placeholder durations.
3. Build:

```bash
node packages/cli/dist/bin.js project-create --name "<label>"
node scripts/build_frames.mjs <project-id> <framesDir> [graphSpec.json]
```

Durations here are placeholders — Stage 4's per-frame narration re-paces each
frame to its narration length. **Pause** and show the frame list + node count.


## Stage 4 · narration (Generate TTS, audition)

Before generating, **show the user the exact narration script** (compose 1-2 sentences that fit the template's `duration_sec`). Wait for confirmation:

> I'll send this to TTS: "<narration>". Proceed? (y/n/redo to rewrite)

Then run:

```bash
node scripts/generate_narration.mjs "<narration text, 1-2 sentences>" <project-id>
```

The script:
1. Reads MiniMax creds from `.html-video/media-config.json` (China region → voice `male-qn-qingse`; international → voice `English_Grace`)
2. Calls `generateTts()` from `@html-video/core`
3. Saves the MP3 to `.html-video/assets/<project-id>/narration.mp3`
4. **Registers the asset in `project.assets` and sets `project.soundtrack.narrationAssetId`** (preserving any existing music). This wiring is required — `applySoundtrack` resolves audio strictly from `project.soundtrack` + `project.assets`; there is no auto-discovery, so an MP3 left on disk alone yields a **silent** video.
5. Prints the duration in seconds

**Success**: File exists at the path above, ≥ 5KB, duration matches expected (text length / ~15 chars-per-second).

**Region gotcha** (common failure): If the key is China-region (`api.minimaxi.com`), `English_*` voice ids fail with error 2054 "voice id not exist". The script handles this — let it pick the right voice, do not override manually.

#### Multi-frame: per-frame narration with A/V sync

For multi-frame projects, narrate **per frame** so each frame's on-screen
duration matches its spoken line (no audio/video drift). Write a `segments.json`
array in frame order, each item keyed to a `graphNodeId`:

```json
[ { "id": "hook", "text": "..." }, { "id": "body", "text": "..." } ]
```

Then:

```bash
node scripts/narrate_frames.mjs <project-id> segments.json
```

It TTS-es each segment, ffprobe-measures it, **re-paces every frame's
`durationSec`** to its narration length (floor 3s, +0.4s tail), concats into one
`narration.mp3`, registers the asset, and sets `soundtrack.narrationAssetId`
(preserving music). Show the per-frame duration table, then **pause**.

After success, **show the file path + duration** and **pause**:
> Narration generated: `<path>` (Xs). Listen to it, then continue to music? (y/n/redo/skip)

`skip` is valid here — the user can render without narration if they just want a music+visual video.

## Stage 5 · music (Pick style, generate, audition)

Before generating, **offer 2-3 style options** based on the template + intent. Examples:

- `cinematic electronic, 80bpm, no vocals, optimistic build`
- `warm lo-fi cafe, soft piano, dusty vinyl, no drums`
- `minimal ambient room tone, no melody, very quiet background`

Or let the user supply a custom prompt. Then **pause** to pick:

> Pick a music style:
> 1. cinematic electronic
> 2. lo-fi cafe
> 3. custom (type your prompt)
>
> Choose (1/2/3):

Once chosen, generate:

```bash
node scripts/generate_bgm.mjs "<style prompt>" <project-id>
```

The script:
1. Calls `generateMusic({ prompt, instrumental: true, creds })` from `@html-video/core`
2. Saves MP3 to `.html-video/assets/<project-id>/bgm.mp3`
3. **Registers the asset and sets `project.soundtrack.musicAssetId`** at -18dB (preserving any existing narration) — same wiring requirement as narration
4. **Takes ~50s** synchronously — this is normal, music-2.6 is faster but hangs on our key

**Success**: File exists, ≥ 1MB (a 50s instrumental clip is typically 1.5-2.5MB at 256kbps).

After success, **show the file path + size** and **pause**:
> Music generated: `<path>` (X KB, ~Xs). Continue to render? (y/n/redo/skip)

`skip` is valid here — render visual-only.

## Stage 6 · render (Render MP4 + verify)

```bash
node packages/cli/dist/bin.js project-render <project-id>
bash scripts/verify_output.sh <output-path> --require-audio
```

This triggers:
1. `adapter-hyperframes` launches Playwright Chromium headless
2. Records the template HTML (with your variables) into a webm at the project's duration. **Multi-frame**: each frame's HTML is recorded to its own MP4 at that frame's `durationSec`, then ffmpeg-concatenated in order.
3. Calls ffmpeg internally to transcode webm → MP4 (H.264 1080p60, libx264 crf20)
4. **Muxes narration + bgm** into the MP4 at -18dB ducking for music

Wait for completion. Typical wall time: 10-30s for a 4-5s video. Watch for ffmpeg output for the "muxing overhead" line.

**Success**: `status: "rendered"` and `output_path` is returned. The file lives at `.html-video/projects/<project-id>/output-<timestamp>.mp4`.

Then `verify_output.sh` uses ffprobe to print:
- duration (should match the sum of frame durations, or the template's `duration_sec`)
- video stream (H.264, 1920x1080, 60fps)
- audio stream (AAC, present, 44.1kHz stereo)

Pass `--require-audio` whenever you generated narration and/or music — it turns a
missing audio stream into a hard FAIL, catching the silent-video failure mode
(asset written to disk but never registered in `project.assets`, so the mux
no-op'd). Omit the flag only for deliberate visual-only renders.

**Success**: All expected streams present, duration within ±0.2s of expected.

Tell the user the absolute path of the MP4 so they can play it.

## Output contract

When the pipeline completes, the user gets:
- One MP4 file with video + narration + bgm mixed in
- File path printed in absolute Windows form (e.g. `C:\Users\...\output-with-audio.mp4`)

## Iteration

If the user wants to change something, jump back to the relevant stage:
- **Text/headline/figure**: redo from Stage 3
- **Template**: redo from Stage 2 (old project stays as artifact; create a new project-id)
- **Voice/style**: redo Stage 4 only, then Stage 6
- **Music style**: redo Stage 5 only, then Stage 6
- **Region of MiniMax key**: edit `.html-video/media-config.json` `baseUrl`, then redo Stages 4 → 6

If the user says "do it all at once" or "don't ask me again", you may chain stages — but **always** show the result of each stage and only continue if the user has not asked for changes since the last one.

## What this skill does NOT do

- Author new HTML templates (use a separate workflow for that — write a template, drop in `templates/`, add YAML, then run this skill on it)
- Push to git / open PRs
- Run the Studio UI (this is a CLI-only pipeline; the Studio is for interactive editing)

> **Multi-frame note**: multi-frame sequences (content-graph + per-frame HTML) ARE supported via `build_frames.mjs` + `narrate_frames.mjs` (see Stage 3/4). What's still out of scope is *multi-composition templates* — parameterized reusable multi-frame templates in `templates/`. Multi-frame here means hand-authored per-frame HTML, not a packaged template.

## Resources

### scripts/
- `check_env.sh` — verify all 5 pre-flight checks
- `generate_narration.mjs` — single-segment MiniMax TTS; writes MP3 **and wires soundtrack**
- `generate_bgm.mjs` — MiniMax music-1.5; writes MP3 **and wires soundtrack**
- `build_frames.mjs` — multi-frame: write a content-graph + per-frame HTML onto a project
- `narrate_frames.mjs` — multi-frame: per-frame TTS with A/V sync (re-paces frame durations)
- `verify_output.sh` — ffprobe-based final MP4 sanity check (`--require-audio` to assert a soundtrack)

### references/
- `troubleshooting.md` — common failures and fixes (ffmpeg PATH on Windows, MiniMax region mismatch, voice id errors, chromium launch failures)
- `audio-api.md` — exact function signatures for `generateTts` and `generateMusic`, plus how creds are resolved
- `template-catalog.md` — quick reference for the 22+ templates: which work for which content, default durations, key variables
