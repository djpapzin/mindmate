# 🧠 MindMate - AI Mental Wellness Companion

<p align="center">
  <strong>A compassionate Telegram chatbot providing 24/7 mental wellness support powered by OpenAI</strong>
</p>

<p align="center">
  <a href="https://t.me/mywellnesscompanion_bot">🤖 Try MindMate</a> •
  <a href="#features">Features</a> •
  <a href="#personal-mode">Personal Mode</a> •
  <a href="#deployment">Deploy</a>
</p>

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| 💬 **Empathetic Chat** | AI-powered conversations with emotional intelligence |
| 🚨 **Crisis Detection** | Automatic detection with SA helpline resources (SADAG) |
| 📝 **Persistent Memory** | PostgreSQL-powered cross-session conversation history |
| 🔍 **Memory Search** | PostgreSQL keyword search over stored conversation text (not true vector semantic retrieval yet) |
| 🔓 **Personal Mode** | Premium experience with direct advice (no disclaimers) |
| �️ **Voice Messages** | Send voice notes → bot responds with voice ✅ **COMPLETED** |
| ⚡ **FastAPI Backend** | Modern async architecture with webhooks |
| 🛡️ **Graceful Fallback** | In-memory storage if PostgreSQL unavailable, with a user-facing lighter-memory notice |

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Start a conversation |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |
| `/mode` | Check your mode (Standard/Personal) |
| `/votd` | Get today's Bible verse |
| `/model` | Switch AI models for A/B testing |
| `/feedback` | Save a quick product note for review |
| `/schedule` | Manage daily direct check-ins (07:00 SAST by default) |
| `/voice` | Choose voice personality (coming soon) |

> `/votd` uses the public OurManna Verse of the Day JSON endpoint and needs no extra API key.

---

## 🔓 Personal Mode

A private, unfiltered AI therapist experience for authorized users.

| Feature | Standard Mode | Personal Mode |
|---------|---------------|---------------|
| AI Disclaimers | "As an AI..." | ❌ None |
| Advice Style | Generic tips | Direct guidance |
| Crisis Response | Hard stop | Soft prompt + continue |
| Tone | Professional | Trusted friend |
| User Context | None | Name, focus areas |

**Personal Mode is locked to specific user IDs** - perfect for personal use.

### Focus Areas (Personal Mode)
- 💑 Relationships & Dating
- 💰 Financial Stress
- 🧠 Bipolar Management
- 😰 Anxiety & Mood
- 💼 Work/Career

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI + Uvicorn |
| **Bot Library** | python-telegram-bot 21.0 |
| **AI** | OpenAI GPT-5.4 Mini |
| **Voice** | Smart Caption Handling (gpt-4o-mini-transcribe + gpt-4o-mini-tts) |
| **Hosting** | Render (free tier) |
| **Database** | PostgreSQL (Neon, persistent storage) |
| **Uptime** | UptimeRobot |

### Architecture
```
Telegram → Webhook → FastAPI → OpenAI → Response
                 ↓
      PostgreSQL persistence (+ in-memory fallback)
```

---

## 🚀 Deployment

### Live Instances
| Bot | URL | Branch | Purpose |
|-----|-----|-----|-------|---------|
| **Production** | @mindmate_dev_bot | https://mindmate-dev.onrender.com | `main` branch |
| **Staging** | @mywellnesscompanion_bot | https://mindmate-uidn.onrender.com | `feature/*` branches |

### Deploy Your Own

#### Render (Recommended)
1. Fork this repository
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Configure:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python bot.py
   ```
5. Add Environment Variables:
   | Variable | Description |
   |----------|-------------|
   | `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/botfather) |
   | `OPENAI_API_KEY` | From [OpenAI](https://platform.openai.com/api-keys) |
   | `DATABASE_URL` or `NEON_MINDMATE_DB_URL` | PostgreSQL connection string (primary storage) |
   | `RENDER_EXTERNAL_URL` | Your Render URL (enables webhooks) |

6. Deploy!

> 💡 **Tip:** Use [UptimeRobot](https://uptimerobot.com) to ping `/health` every 5 minutes.

---

## 💻 Local Development

```bash
# Clone the repository
git clone https://github.com/djpapzin/mindmate.git
cd mindmate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your tokens

# Run the bot (polling mode - no RENDER_EXTERNAL_URL)
python bot.py
```

### Environment Variables
```env
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:password@host:5432/database
# or: NEON_MINDMATE_DB_URL=postgresql://user:password@host:5432/database
RENDER_EXTERNAL_URL=https://your-app.onrender.com  # Optional: enables webhooks
```

> Note: the current storage implementation uses PostgreSQL for persistence and falls back to in-memory storage if the database is unavailable. Redis is retained only as legacy migration/reference material.

### Daily direct check-ins at 07:00 SAST
MindMate's built-in daily heartbeat scheduler sends by **direct message from the bot itself**.

Use these env values for DJ Papzin's 07:00 SAST DM heartbeat:

```env
DAILY_HEARTBEAT_ENABLED=true
DAILY_HEARTBEAT_HOUR=7
DAILY_HEARTBEAT_TIMEZONE=Africa/Johannesburg
DAILY_HEARTBEAT_ALLOWED_USER_IDS=339651126
```

Then in Telegram, open a DM with the bot as DJ Papzin and run:

```text
/schedule on
```

---

## 🧪 A/B Model Testing

Automated testing to compare AI models via `research/run_blind_test.py`:

**Models Available:** GPT-5.4 Mini, GPT-4o-mini, GPT-4.1-mini, GPT-5.2

The automated testing script runs comprehensive comparisons and generates performance reports.

---

## 🆘 Crisis Support

MindMate detects crisis keywords and provides immediate resources:

| Resource | Contact | Available |
|----------|---------|-----------|
| **SADAG** | 0800 567 567 | 24/7 |
| **Lifeline SA** | 0861 322 322 | 24/7 |
| **Suicide Crisis Line** | 0800 567 567 | 24/7 |

---

## 📋 Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed plans:

- [x] Personal Mode
- [x] FastAPI Migration
- [x] Webhook Support
- [x] A/B Testing Tools
- [x] Persistent Memory (PostgreSQL)
- [x] Voice Messages
- [x] Daily Check-ins
- [ ] WhatsApp Integration (Twilio)

---

## ⚠️ Disclaimers

> **MindMate is NOT a replacement for professional mental health support.**

- This is an AI companion for emotional reflection
- If you're in crisis, contact a professional or helpline
- The bot does not provide medical advice or diagnosis

---

## 🔒 Security

- Never commit `.env` files
- Personal Mode is locked by user ID
- Rotate tokens if compromised

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with 💚 for mental wellness in South Africa
</p>
