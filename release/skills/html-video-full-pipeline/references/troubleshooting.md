# Troubleshooting

Common failures and their fixes for the html-video-full-pipeline.

## ffmpeg: "ffmpeg not found on PATH"

**Symptom**: `project-render` or `check_env.sh` reports ffmpeg missing, but `ffmpeg -version` works in a fresh terminal.

**Cause**: User added ffmpeg to the Windows user-level PATH *after* the Node process started. The live Node process inherited the old PATH at startup; user-level changes don't propagate.

**Fix** (any of these):
1. Close and reopen the terminal/editor that started the Node process
2. Manually place ffmpeg at one of these well-known paths (the CLI and adapter both probe these):
   - `C:\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe`
   - `C:\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe`
   - `C:\ffmpeg\bin\ffmpeg.exe`
3. Set `FFMPEG_PATH` env var in the current shell before running

## MiniMax TTS: "voice id not exist" (error 2054)

**Symptom**: `generateTts` throws with status_code 2054, voice id referenced in the error.

**Cause**: Voice id belongs to a different region. There are two MiniMax regions:
- International: `api.minimax.io` — voice ids like `English_Grace`, `English_Passion`
- China: `api.minimaxi.com` — voice ids like `male-qn-qingse`, `female-shaonv`

A key only authenticates against its own region.

**Fix**: The `generate_narration.mjs` script auto-detects region from `baseUrl` and picks the right default voice. Don't override `voiceId` manually unless you know the voice exists in your region.

If you need a specific voice, get the full list from MiniMax's docs for your region.

## MiniMax music: "music-1.5 returned 0 bytes" or hangs

**Symptom**: `generateMusic` returns empty bytes, or never returns (timeout at 120s).

**Cause**: Model mismatch. The skill uses `music-1.5` (synchronous, returns in ~50s). The newer `music-2.6` family hangs for our key (verified: 180s with no response). `music-1.5` also requires a `lyrics` field — the wrapper passes an empty placeholder for instrumental tracks since the API lacks an `is_instrumental` flag on the 1.5 model.

**Fix**: Don't override the model. The wrapper handles the right call shape. If you need different music, change the prompt, not the model.

## MiniMax: "401 Unauthorized" or "auth failed"

**Symptom**: TTS or music call returns 401.

**Cause**: API key is wrong, expired, or for the wrong region.

**Fix**:
1. Open Studio at `http://127.0.0.1:3071`, go to Settings → MiniMax, paste a fresh key
2. Or edit `.html-video/media-config.json` directly with the new key
3. The key precedence is: config file > `OD_MINIMAX_API_KEY` env > `MINIMAX_API_KEY` env

## Playwright Chromium: "Cannot find chromium" / launch timeout

**Symptom**: `project-render` hangs at "launching browser" stage, or throws about missing chromium.

**Cause**: Playwright bundled chromium missing or corrupted.

**Fix**:
```bash
npx playwright install chromium
```

Verify with:
```bash
ls "$LOCALAPPDATA/ms-playwright/chromium-"*  # should list chromium-XXXX
```

## Studio project vs CLI project mismatch

**Symptom**: A project created via Studio UI's "New project" button doesn't appear in `html-video project-list`. Or vice versa.

**Cause**: Studio creates projects in-memory during the session; CLI reads from disk. They have separate stores that don't sync.

**Fix**: Pick one. For scripted/automated pipelines, use CLI. For interactive editing, use Studio. Don't mix.

## "voice id not exist" with a 125-char key from .html-video/media-config.json

**Symptom**: Key looks valid (length is right), but voice calls fail.

**Cause**: Key is China-region (baseUrl `api.minimaxi.com`) but you tried to use `English_Grace` (international voice).

**Fix**: Let the script pick. Or set `voiceId` to `male-qn-qingse` (China default).

## "node: --version" shows wrong version

**Symptom**: Two Node versions on the system, html-video is picking up the wrong one.

**Fix**: Either use the version pnpm was installed with, or reinstall pnpm against the desired Node.

## pnpm install fails with ECONNRESET

**Symptom**: `pnpm install` errors with network/connection issues.

**Fix**: Add a Chinese mirror to `.npmrc`:
```
registry=https://registry.npmmirror.com
```

Already done in the html-video `.npmrc` from the initial setup.
