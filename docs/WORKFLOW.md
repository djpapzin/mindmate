# MindMate Simplified Workflow (Final State)

## Current Setup (Post-Migration)

| Bot | Render Service | Branch | URL | Purpose |
|-----|----------------|-------|--------|---------|
| `@mindmate_dev_bot` | `mindmate` | `main` | https://mindmate-dev.onrender.com | **Production** - Your partner uses this daily |
| `@mywellnesscompanion_bot` | `mindmate-dev` | `feature/*` | https://mindmate-uidn.onrender.com | **Staging** - Your testing ground |

## What Was Done

1. ✅ Merged `feature/personal-mode` into `main`
2. ✅ Updated `mindmate-dev` Render service to deploy from `main`
3. ✅ Left auto-deploy ON (safe because you work on feature branches)

## Your New Workflow

### Starting New Work
```bash
git checkout main
git pull
git checkout -b feature/my-new-thing
# ... do work ...
git push -u origin feature/my-new-thing
```

### Testing on Staging
1. Point `mindmate` Render service to your `feature/my-new-thing` branch
2. Test with `@mywellnesscompanion_bot`
3. When satisfied, merge to `main`

### Deploying to Production
```bash
git checkout main
git merge feature/my-new-thing
git push origin main
```
- Auto-deploy pushes to `@mindmate_dev_bot` (production)
- Your partner gets the update

## Key Benefits

- **Partner's experience is stable** - They use `@mindmate_dev_bot` which only updates when `main` changes
- **You can break things freely** - Test on `@mywellnesscompanion_bot` first
- **Simple mental model** - `main` = production, feature branches = staging
- **No new bots needed** - Using what you already have

## Render Service Details

### Production (`mindmate`)
- **Bot**: `@mindmate_dev_bot`
- **Branch**: `main`
- **URL**: https://mindmate-dev.onrender.com
- **Auto-deploy**: ON
- **Redis**: Production Redis instance (`mindmate-redis`)
- **Database**: Redis with OpenAI embeddings (semantic search enabled)

### Staging (`mindmate-dev`)
- **Bot**: `@mywellnesscompanion_bot`
- **Branch**: `feature/*` (varies)
- **URL**: https://mindmate-uidn.onrender.com
- **Auto-deploy**: ON (or manual)
- **Redis**: Separate Redis instance
- **Database**: Redis with OpenAI embeddings (semantic search enabled)

## Quick Reference

| Task | Action |
|------|--------|
| Start new feature | `git checkout -b feature/name` |
| Test feature | Point `mindmate` service to branch |
| Deploy to users | Merge to `main`, push |
| Hotfix | `git checkout -b hotfix/name` from `main` |

## Notes

- The `_dev` in `@mindmate_dev_bot` is just legacy naming - your partner doesn't care
- Keep auto-deploy ON on production since you only push to `main` when ready
- If you ever need to stop production deploys, disable auto-deploy on `mindmate-dev`
