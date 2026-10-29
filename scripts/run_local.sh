#!/usr/bin/env bash
# Run MindMate in Telegram polling mode (no Render / no public webhook URL).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
elif [[ -f "$ROOT/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/venv/bin/activate"
fi

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing .env — copy .env.example and fill TELEGRAM_BOT_TOKEN + MINDMATE_OPENROUTER_API_KEY"
  echo "Or: python scripts/pull_render_env.py  (needs RENDER_API_KEY)"
  exit 1
fi

# Force polling: do not use a suspended Render webhook URL.
unset RENDER_EXTERNAL_URL || true
export PYTHONUNBUFFERED=1
export PORT="${PORT:-10000}"

exec python bot.py
