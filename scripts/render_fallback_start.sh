#!/usr/bin/env bash
set -euo pipefail

RENDER_HEALTH_URL="${RENDER_HEALTH_URL:-https://mindmate-dev.onrender.com/health}"
RENDER_CHECK_TIMEOUT="${RENDER_CHECK_TIMEOUT:-8}"
LOCAL_PORT="${PORT:-18080}"

# Keep the VM fallback opt-in and safe: only start locally when Render is not reachable/healthy.
if curl -fsS --max-time "${RENDER_CHECK_TIMEOUT}" "${RENDER_HEALTH_URL}" >/tmp/mindmate-render-health.json 2>/dev/null; then
  if command -v python3 >/dev/null 2>&1; then
    echo "Render is healthy; not starting the local fallback bot."
    echo "Health: $(tr -d '\n' </tmp/mindmate-render-health.json)"
  else
    echo "Render is healthy; not starting the local fallback bot."
  fi
  exit 0
fi

echo "Render health check failed; starting local fallback bot on port ${LOCAL_PORT}."
export PORT="${LOCAL_PORT}"
export RENDER_EXTERNAL_URL=""
export FORCE_LOCAL_POLLING="1"
exec python bot.py
