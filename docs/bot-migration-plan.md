# MindMate Telegram Bot Migration Plan (Dev -> Production)

## Goal
Move your **current daily-use bot** (currently the “dev bot”) into a **stable production setup** with a production-looking bot identity.

> Historical note: this plan originally assumed Redis-backed memory migration. MindMate now uses PostgreSQL as the active runtime datastore, with an in-memory fallback only when PostgreSQL is unavailable.

Given your constraints:
- Only **1 real user + you**
- Users care mostly about **bot memory continuity**, not Telegram chat history

This plan aims to:
- Avoid breaking the current experience for the daily user.
- Create a clean workflow where `main` is stable and feature work doesn’t disturb users.

---

## Target End State (Recommended)

### Production (Public)
- **Telegram bot**: New production-looking username (create a new bot)
- **Render service**: `mindmate-prod`
- **Git branch**: `main`
- **Storage**: Production PostgreSQL database

### Staging/Dev (Internal)
- **Telegram bot**: Keep your existing dev bot (or create a new “staging” bot)
- **Render service**: `mindmate-dev`
- **Git branch**: `develop` (recommended) or current integration branch
- **Storage**: Staging/development PostgreSQL database (or clearly isolated env config)

Why: Telegram bot usernames cannot be changed, so the only way to avoid a “dev-looking” username is to use a new bot.

---

## Phase 0 — Pre-flight Checklist (15 minutes)

- [ ] Confirm which bot is the current daily-use bot (the one your partner uses).
- [ ] Confirm current Render mapping:
  - [ ] `mindmate-dev` -> dev bot token -> dev database config
  - [ ] `mindmate-prod` -> prod bot token -> prod database config
- [ ] Decide your new public bot username (check availability in BotFather).

> Note: Do **not** delete old bots/services yet. We’ll keep rollback options.

---

## Phase 1 — Create the New Production Telegram Bot (10 minutes)

1. In Telegram, open **@BotFather**.
2. Create a new bot:
   - Command: `/newbot`
   - Choose a **production-looking username** (no “dev”).
3. Save the new bot token securely.

Deliverable:
- New **production bot token** ready to be added to Render.

---

## Phase 2 — Point Production Render Service to the New Bot (15–30 minutes)

1. Go to Render dashboard → your **production service** (`mindmate-prod`).
2. Set environment variables:
   - `TELEGRAM_BOT_TOKEN` = **new production bot token**
   - Ensure it points to the **production PostgreSQL/database config**, not dev
   - If you have an `ENV` variable, set it to `production`
3. Deploy `mindmate-prod` from `main`.
4. Test:
   - Start chat with the new production bot
   - Confirm `/start` and basic conversation works
   - Confirm memory write/read is working (a short conversation, then ask a recall-style question)

Rollback option:
- You can revert env vars back to the old token if something goes wrong.

---

## Phase 3 — Migrate Memory (Dev PostgreSQL/Data Snapshot -> Prod PostgreSQL) (Optional but Recommended)

Because you only have **1 real user**, the simplest and safest approach is:

### Option A (Simplest): Manual “seed memory”
- Ask the user to copy/paste their key context.
- You seed it as “initial profile” in the new bot.

### Option B (Recommended): Scripted migration by Telegram `user_id`
Migrate the user's stored memory records from the development data source into the production PostgreSQL data source, if you actually need historical continuity.

High-level steps:
1. Identify what data you actually want to preserve (messages, preferences, profile data).
2. Export the relevant rows or take a safe snapshot from the development PostgreSQL database.
3. Import or seed the needed data into the production PostgreSQL database with matching user identifiers.
4. Validate by asking the new production bot questions that depend on memory.

Safety notes:
- Make a snapshot/export of development data before importing.
- Prefer **copy** over **move** (non-destructive).

Deliverable:
- User memory available in the new production bot.

---

## Phase 4 — Transition the Daily User (5 minutes)

1. In the old dev bot, send a final message:
   - “Official bot moved here: https://t.me/<new_prod_username>”
2. Ask the user to:
   - Start the new bot
   - Run `/start`
3. Confirm:
   - Their core memory is present (if you migrated)
   - They’re comfortable switching

Because they don’t care about chat history, this is typically painless.

---

## Phase 5 — Fix Your Workflow So You Don’t Break Daily Users Again

### Recommended Git flow (lightweight)
- `main`
  - Always stable
  - Deploys to production bot (`mindmate-prod`)
- `develop`
  - Integration branch
  - Deploys to staging bot (`mindmate-dev`)
- `feature/<name>`
  - Your work branches
  - Merge into `develop` first

Release process:
1. Develop features on `feature/<name>`.
2. Merge into `develop` → test on staging bot.
3. When stable, merge `develop` → `main`.
4. Deploy production.

### Operational guardrails (high impact)
- Add an `ENV` env var and print it on startup logs.
- Use clearly separate database configuration per environment (URLs, schemas, or isolated services).
- Don’t push breaking changes straight into whatever bot real users rely on.

---

## Phase 6 — Cleanup (Optional, only after a few days)

After the user is fully moved:
- Keep the old dev bot as staging/internal.
- Or create a new bot specifically named staging, e.g. `@mindmate_staging_bot`.

Do **not** delete the old bot immediately; keep it as rollback for at least 1–2 weeks.

---

## Acceptance Checklist

- [ ] New production bot exists with correct username.
- [ ] `mindmate-prod` points to new production bot token.
- [ ] Prod bot works end-to-end.
- [ ] Memory migration done (or manual seed done).
- [ ] Daily user successfully transitioned.
- [ ] `develop`/`feature/*` workflow in place so daily user isn’t disturbed.

---

## Notes / Decisions
- Production bot username: ___________________________
- Staging bot username (existing): ___________________
- Keep old production bot (`@mywellnesscompanion_bot`) as: rollback / archive / other: ___________________
