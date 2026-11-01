#!/usr/bin/env bash
# check_env.sh — verify html-video-full-pipeline pre-flight.
# Run from the html-video project root. Returns 0 if all pass, 1 if any fail.

set -uo pipefail

PASS=0
FAIL=0

check() {
  local name="$1"
  local result="$2"
  local detail="${3:-}"
  if [[ "$result" == "ok" ]]; then
    echo "  ✓ $name${detail:+ — $detail}"
    PASS=$((PASS+1))
  else
    echo "  ✗ $name${detail:+ — $detail}"
    FAIL=$((FAIL+1))
  fi
}

# 1. Node version >= 20
NODE_V=$(node --version 2>/dev/null | sed 's/^v//' | cut -d. -f1)
if [[ -n "$NODE_V" && "$NODE_V" -ge 20 ]]; then
  check "node" "ok" "v$(node --version | sed 's/^v//')"
else
  check "node" "fail" "found $(node --version 2>/dev/null || echo 'nothing'), need v20+"
fi

# 2. pnpm
if command -v pnpm >/dev/null 2>&1 || npx pnpm --version >/dev/null 2>&1; then
  PV=$(npx pnpm --version 2>/dev/null)
  check "pnpm" "ok" "v${PV:-?}"
else
  check "pnpm" "fail" "install with: npm i -g pnpm"
fi

# 3. ffmpeg (PATH first, then Windows unpack locations)
FFMPEG=""
if command -v ffmpeg >/dev/null 2>&1; then
  FFMPEG=$(command -v ffmpeg)
fi
if [[ -z "$FFMPEG" && "$OS" == "Windows_NT" || -n "$WINDIR" ]]; then
  for cand in \
    "C:/ffmpeg-8.1.1-essentials_build/bin/ffmpeg.exe" \
    "C:/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe" \
    "C:/ffmpeg-6.1.1-essentials_build/bin/ffmpeg.exe" \
    "C:/ffmpeg/bin/ffmpeg.exe"; do
    if [[ -f "$cand" ]]; then FFMPEG="$cand"; break; fi
  done
fi
if [[ -n "$FFMPEG" ]]; then
  FV=$("$FFMPEG" -version 2>/dev/null | head -1 | sed 's/ffmpeg version //' | cut -d' ' -f1)
  check "ffmpeg" "ok" "v${FV:-?} at $FFMPEG"
else
  check "ffmpeg" "fail" "install via gyan.dev/builds (essentials) and add bin/ to PATH"
fi

# 4. Playwright Chromium
CHROMIUM_DIR=""
if [[ -n "${LOCALAPPDATA:-}" ]]; then
  CHROMIUM_DIR=$(ls -d "${LOCALAPPDATA}/ms-playwright/chromium-"* 2>/dev/null | head -1)
fi
if [[ -n "$CHROMIUM_DIR" && -d "$CHROMIUM_DIR" ]]; then
  check "chromium" "ok" "$CHROMIUM_DIR"
else
  check "chromium" "fail" "run: npx playwright install chromium"
fi

# 5. MiniMax API key
KEY_SOURCE=""
if [[ -f ".html-video/media-config.json" ]]; then
  KEY_SOURCE="config"
elif [[ -n "${OD_MINIMAX_API_KEY:-}${MINIMAX_API_KEY:-}" ]]; then
  KEY_SOURCE="env"
fi
if [[ -n "$KEY_SOURCE" ]]; then
  check "minimax-key" "ok" "from $KEY_SOURCE"
else
  check "minimax-key" "fail" "configure via Studio UI or set OD_MINIMAX_API_KEY env"
fi

echo ""
echo "Summary: $PASS pass, $FAIL fail"
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
