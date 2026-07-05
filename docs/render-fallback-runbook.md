# MindMate Render Fallback Runbook

## Why this exists
MindMate is deployed on Render, and UptimeRobot can help keep the service warm, but it does **not** prevent free-tier quota exhaustion.

If Render is healthy, keep it as the single active bot runtime.
If Render is down or out of quota, use the VM as a **manual fallback** so Telegram still has one active owner for the token.

## Safe operating rule
Do **not** run the Render instance and the local VM bot at the same time unless you intentionally want to test and have isolated tokens.

## Normal state
- Render is live
- UptimeRobot pings `/health`
- Local VM bot stays off

## Fallback state
Use the VM only when:
- Render health is failing consistently, or
- Render has exhausted its free quota, or
- you need an emergency temporary bot while Render is unavailable

## Local fallback launcher
The repo includes a launcher that checks Render first and only starts the local bot if Render is unavailable:

```bash
./scripts/render_fallback_start.sh
```

Optional overrides:

```bash
RENDER_HEALTH_URL=https://mindmate-dev.onrender.com/health \
RENDER_CHECK_TIMEOUT=8 \
PORT=18080 \
./scripts/render_fallback_start.sh
```

What it does:
- pings the live Render `/health`
- exits without starting anything if Render is healthy
- starts `python bot.py` locally only if Render cannot be reached successfully
- forces polling mode with `FORCE_LOCAL_POLLING=1` so a `.env` webhook URL cannot pull the VM back into webhook mode

## Emergency manual run
If you already know Render is down and want to bypass the check:

```bash
RENDER_HEALTH_URL=http://127.0.0.1:0/health ./scripts/render_fallback_start.sh
```

Or simply run the bot directly in the VM environment:

```bash
PORT=18080 python bot.py
```

## Recovery when Render comes back
1. Stop the local VM bot.
2. Confirm `https://mindmate-dev.onrender.com/health` returns `200`.
3. Leave Render as the active runtime again.

## Operational notes
- The fallback is intentionally **manual / opt-in**.
- This avoids duplicate Telegram polling/webhook ownership.
- UptimeRobot remains useful for waking Render and alerting on outages, but it does not create more free instance hours.
