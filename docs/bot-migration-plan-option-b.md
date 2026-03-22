# MindMate Option B: Rebrand Dev Bot as Production (No New Prod Bot)

## Goal
Keep your **current daily-use bot** (`@mindmate_dev_bot`) as the **official production bot**, and repurpose your **old production bot** (`@mywellnesscompanion_bot`) as the **new development/staging bot**.

This avoids:
- Setting up a new Render production service
- Changing what your partner is already using daily

> Historical note: earlier versions of this plan referred to Redis as the active datastore. MindMate now uses PostgreSQL in the active runtime, with in-memory fallback only when PostgreSQL is unavailable.

## Target End State (Simpler - Only 2 Bots)

### Production (Stable - What Users See)
- **Telegram bot**: `@mindmate_dev_bot` (your current daily-use bot)
- **Render service**: `mindmate-dev` (keep this as-is)
- **Git branch**: `main`
- **Storage**: Current production PostgreSQL/database config remains the prod path
- **Users**: Your partner + you continue using this bot

### Staging (Development Playground)
- **Telegram bot**: `@mywellnesscompanion_bot` (your OLD production bot, now repurposed)
- **Render service**: Your OLD production Render service
- **Git branch**: `develop` or feature branches
- **Storage**: Its own staging/development database config (kept isolated from production)
- **Users**: Only you (for testing)

## Phase 1 — Freeze Current Dev Bot (Do This First)

⚠️ **Critical**: Stop pushing random changes to the bot your partner uses.

### Immediate Actions (Today)
1. [ ] **Stop auto-deploy** on `mindmate-dev` Render service
   - Go to Render dashboard → `mindmate-dev` → Settings
   - Set "Auto-Deploy" to **NO**
   - Now you control when deployments happen

2. [ ] **Create a `develop` branch** from your current working branch
   ```bash
   git checkout <your-current-branch>
   git checkout -b develop
   git push -u origin develop
   ```

3. [ ] **Create a new Render service** for staging:
   - Name: `mindmate-staging`
   - Branch: `develop`
   - Environment variables: NEW bot token (create below), staging database config
   - Auto-deploy: YES (so staging stays current with `develop`)

### Why This Helps
- Your partner's bot (`mindmate-dev`) becomes "frozen" at a stable state
- All new work goes to staging first
- You decide when to promote staging → production

---

## Phase 2 — Repurpose Old Production Bot as Staging (15 minutes)

Now we'll turn `@mywellnesscompanion_bot` into your testing ground.
### Step 1: Update Old Production Bot Environment
1. Go to Render dashboard → your **old production service** (`mindmate-prod` or whatever it's called)
2. Change environment variables:
   - `ENV` = `staging`
   - If you want, change bot description in @BotFather to "🧪 MindMate Staging Bot - For testing only"

### Step 2: Point Old Bot to `develop` Branch
1. In Render service settings, change branch from `main` to `develop`
2. Set **Auto-Deploy** to **YES**
3. Deploy

### Step 3: Test Staging
- Message `@mywellnesscompanion_bot`
- Confirm it responds
- Confirm it's using separate staging data/config (no pollution of your partner's production data)

---

## Phase 3 — Establish Git Workflow (Your Preference: Main Branch Focused)

You said: *"I prefer 1 branch, the main branch which is deployed, then make feature branches when want new features"*

Here's how to make that work with 2 bots:

### Git Branches

```
main              ← production bot (@mindmate_dev_bot)
  ↑
develop           ← staging bot (@mindmate_staging_bot)
  ↑
feature/xyz       ← your work branches
```

### Workflow

1. **Start new work**:
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/my-new-thing
   # ... do work ...
   git push -u origin feature/my-new-thing
   ```

2. **Test on staging**:
   - Merge `feature/my-new-thing` → `develop`
   - Render auto-deploys to `mindmate-staging` bot
   - Test with staging bot

3. **Promote to production**:
   - When ready, merge `develop` → `main`
   - Manually deploy `mindmate-dev` (now your prod) from Render dashboard
   - Or set `mindmate-dev` to auto-deploy from `main` only

### Why This Works for You
- `main` = always stable, deployed to the bot users see
- `develop` = integration/testing, deployed to staging bot
- Feature branches = your sandbox, never touch user-facing bot directly

---

## Phase 4 — Handle the "Dev" Username (Communication Fix)

Your bot username is `@mindmate_dev_bot`. Options:

### Option 1: Keep It (Simplest)
- Just accept the `_dev` in the username
- Most users won't care or notice
- Your partner already uses it daily

### Option 2: Create a "Pretty" Link/Forward (Optional)
- Create a channel or group with a nice name like "MindMate"
- Pin a message with the bot link
- Users join the channel, click the pinned bot link

### Option 3: Use Bot Description to Clarify (Recommended)
- In @BotFather, set bot description:
  ```
  🤖 MindMate - Your AI Mental Wellness Companion
  
  Note: This is the official bot. The "_dev" in the username is legacy from early development.
  ```
- Set bot about text similarly

I recommend **Option 1 + Option 3** (do nothing + add description).

---

## Phase 5 — Update Documentation & Naming

### Update README.md
- Change references to production bot from `@mywellnesscompanion_bot` → `@mindmate_dev_bot`
- Add note: "Development/staging bot: @mindmate_staging_bot (for testing only)"

### Update Render Service Names (Optional)
You could rename services in Render:
- `mindmate-dev` → `mindmate-prod` (what users use)
- `mindmate-staging` → `mindmate-dev` (your testing)

Or keep names as-is and just know:
- `mindmate-dev` = production (despite the name)
- `mindmate-staging` = your testing ground

### Add Startup Logging
Add to your bot startup:
```python
print(f"🚀 MindMate starting in {ENV} mode")
print(f"🤖 Bot: @{bot_username}")
print(f"🗄️  Database: {db_host}")
```

So logs always show which environment is running.

---

## Phase 6 — Clean Up Old Production Bot (Optional)

You have `@mywellnesscompanion_bot` (old prod).

Options:
1. **Keep as archive**: Do nothing, just don't use it
2. **Add forwarding message**: Set bot description to "Moved to @mindmate_dev_bot"
3. **Delete**: Only if sure you won't need rollback

Recommendation: Option 2 for 1-2 months, then Option 1.

---

## Summary of Changes Needed

### Immediate (Today - To Stop Breaking Partner's Bot)
- [ ] Disable auto-deploy on current `mindmate-dev`
- [ ] Create `develop` branch
- [ ] Create staging Telegram bot
- [ ] Create `mindmate-staging` Render service

### Short-term (This Week)
- [ ] Update README with correct bot usernames
- [ ] Add startup logging to show environment
- [ ] Test staging workflow: feature branch → develop → staging bot
- [ ] Deploy stable `main` to production bot (manual deploy)

### Ongoing (New Normal)
- [ ] Feature work on branches, merged to `develop` first
- [ ] Test on staging bot
- [ ] Merge `develop` → `main` when ready
- [ ] Deploy `main` to production bot manually or via auto-deploy

---

## Checklist: First Stable Release

- [ ] Partner confirms their bot still works (no disruption)
- [ ] `develop` branch exists and is up to date
- [ ] `mindmate-staging` service created and running
- [ ] Staging bot responds correctly
- [ ] Staging uses separate database/config isolation (verify data doesn't overlap)
- [ ] README updated with correct bot links
- [ ] Production bot description updated (explain "_dev" in username)
- [ ] First feature branch tested: `feature/xyz` → `develop` → staging → `main` → prod

---

## Questions to Decide Before Starting

1. **Staging bot username**: What do you want to call it?
   - Suggestion: `@mindmate_staging_bot` or `@mindmate_test_bot`

2. **Database isolation for staging**: Same PostgreSQL instance with strict isolation, or a separate database/service?
   - Same instance + careful isolation = easier, but higher blast radius if config is wrong
   - Separate database/service = cleaner, slightly more setup

3. **Render service naming**: Rename services or keep legacy names?
   - Rename: Clearer mentally, but requires Render config
   - Keep names: Less work, just document the mental model

---

## Next Step

Tell me:
1. Your preferred staging bot username
2. Same PostgreSQL instance with clear isolation, or a separate database for staging?

Then I'll help you execute Phase 1 (freeze current bot, create staging setup) without breaking your partner's experience.
