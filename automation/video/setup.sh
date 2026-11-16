#!/usr/bin/env bash
# One-time setup per session: Hindi voice (edge-tts), fonts, headless Chrome check.
set -euo pipefail
cd "$(dirname "$0")"
pip install -q edge-tts playwright --break-system-packages >/dev/null 2>&1 || true
# Trust the session proxy CA for Python (edge-tts uses certifi)
if [ -f "$HOME/.ccr/ca-bundle.crt" ]; then
  CERT=$(python3 -c "import certifi;print(certifi.where())")
  grep -q "ccr-marker" "$CERT" 2>/dev/null || { echo "# ccr-marker" >> "$CERT"; cat "$HOME/.ccr/ca-bundle.crt" >> "$CERT"; }
fi
[ -d node_modules/@fontsource/mukta ] || npm i --no-save --no-audit --no-fund --prefix "$(pwd)" @fontsource/mukta @fontsource/space-grotesk >/dev/null 2>&1
command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
CHROME=$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)
[ -n "$CHROME" ] || python3 -m playwright install chromium >/dev/null 2>&1
echo "setup ok"
