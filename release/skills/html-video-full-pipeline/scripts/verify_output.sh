#!/usr/bin/env bash
# verify_output.sh — ffprobe-based sanity check on the final MP4.
# Usage: bash verify_output.sh <mp4-path> [--require-audio]
#
# --require-audio: FAIL (exit 1) if the MP4 has no audio stream. Pass this
#   whenever the project has a soundtrack set (narration and/or music) — it
#   catches the silent-video failure mode where the export-time mux was a no-op
#   because the asset was never registered in project.assets. Without the flag,
#   a missing audio stream is only a warning (correct for visual-only renders).

set -uo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash verify_output.sh <mp4-path> [--require-audio]"
  exit 2
fi

MP4="$1"
REQUIRE_AUDIO=0
[[ "${2:-}" == "--require-audio" ]] && REQUIRE_AUDIO=1
if [[ ! -f "$MP4" ]]; then
  echo "FAIL: file not found: $MP4"
  exit 1
fi

# Resolve ffprobe (PATH first, then Windows fallback)
FFPROBE=""
if command -v ffprobe >/dev/null 2>&1; then
  FFPROBE=$(command -v ffprobe)
fi
if [[ -z "$FFPROBE" ]]; then
  for cand in \
    "C:/ffmpeg-8.1.1-essentials_build/bin/ffprobe.exe" \
    "C:/ffmpeg-7.1.1-essentials_build/bin/ffprobe.exe" \
    "C:/ffmpeg-6.1.1-essentials_build/bin/ffprobe.exe" \
    "C:/ffmpeg/bin/ffprobe.exe"; do
    if [[ -f "$cand" ]]; then FFPROBE="$cand"; break; fi
  done
fi
if [[ -z "$FFPROBE" ]]; then
  echo "FAIL: ffprobe not found (install ffmpeg)"
  exit 1
fi

echo "=== File ==="
ls -lh "$MP4"

echo ""
echo "=== Streams ==="
"$FFPROBE" -v error -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels -of default=noprint_wrappers=0 "$MP4"

echo ""
echo "=== Format ==="
"$FFPROBE" -v error -show_entries format=duration,size,bit_rate -of default=noprint_wrappers=0 "$MP4"

echo ""
# Quick validation
HAS_VIDEO=$("$FFPROBE" -v error -select_streams v -show_entries stream=codec_name -of csv=p=0 "$MP4" | head -1)
HAS_AUDIO=$("$FFPROBE" -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$MP4" | head -1)

OK=0
if [[ -n "$HAS_VIDEO" ]]; then
  echo "✓ video: $HAS_VIDEO"
else
  echo "✗ video: MISSING"
fi
if [[ -n "$HAS_AUDIO" ]]; then
  echo "✓ audio: $HAS_AUDIO"
elif [[ $REQUIRE_AUDIO -eq 1 ]]; then
  echo "✗ audio: MISSING (a soundtrack was expected)"
else
  echo "· audio: none (visual-only render)"
fi

# Video is always required.
if [[ -z "$HAS_VIDEO" ]]; then
  echo ""
  echo "FAIL: no video stream."
  exit 1
fi
# Audio required only when --require-audio was passed.
if [[ $REQUIRE_AUDIO -eq 1 && -z "$HAS_AUDIO" ]]; then
  echo ""
  echo "FAIL: --require-audio set but the MP4 has no audio stream."
  echo "  Likely the soundtrack asset was not registered in project.assets, so"
  echo "  the export-time mux silently no-op'd. Re-run the audio script (it now"
  echo "  registers the asset + sets project.soundtrack), then re-render."
  exit 1
fi

echo ""
if [[ -n "$HAS_AUDIO" ]]; then
  echo "OK: MP4 has both video and audio."
else
  echo "OK: MP4 has video (visual-only, no soundtrack expected)."
fi
exit 0
