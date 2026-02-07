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
| 📝 **Context Memory** | Remembers last 10 messages per conversation |
| 🔓 **Personal Mode** | Premium experience with direct advice (no disclaimers) |
| 🎛️ **Voice Messages** | Send voice notes → bot responds with voice (Hybrid Audio Models) ✅ **COMPLETED** |
| 🧪 **A/B Testing** | Built-in model comparison tools |
| ⚡ **FastAPI Backend** | Modern async architecture with webhooks |

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Start a conversation |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |
| `/mode` | Check your mode (Standard/Personal) |
| `/model` | Switch AI models for A/B testing |
| `/test` | Start blind model comparison |
| `/rate` | Rate responses in blind test |
| `/results` | View blind test results |
| `/voice` | Choose voice personality (coming soon) |

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
| **AI** | OpenAI GPT-4o-mini |
| **Voice** | Hybrid Audio Models (gpt-4o-mini-transcribe + gpt-4o-mini-tts) |
| **Hosting** | Render (free tier) |
| **Uptime** | UptimeRobot |

### Architecture
```
Telegram → Webhook → FastAPI → OpenAI → Response
                 ↓
            /webhook endpoint (async)
```

---

## 🚀 Deployment

### Live Instances

| Bot | URL | Branch |
|-----|-----|--------|
| **Production** | @mywellnesscompanion_bot | `main` |
| **Development** | @mindmate_dev_bot | `feature/*` |

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
RENDER_EXTERNAL_URL=https://your-app.onrender.com  # Optional: enables webhooks
```

---

## 🧪 A/B Model Testing

Built-in blind testing to compare AI models:

```
1. /test              → Start blind test
2. Send a message     → Get 3 responses (A, B, C)
3. /rate A:4 B:5 C:3  → Rate each response
4. Repeat 10-20x
5. /results           → See winner!
```

**Models Available:** GPT-4o-mini, GPT-4.1-mini, GPT-5.2

Automated testing script: `research/run_blind_test.py`

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

See [ROADMAP.md](ROADMAP.md) for detailed plans:

- [x] Personal Mode
- [x] FastAPI Migration
- [x] Webhook Support
- [x] A/B Testing Tools
- [ ] Persistent Memory (PostgreSQL)
- [ ] WhatsApp Integration (Twilio)
- [ ] Voice Messages
- [ ] Daily Check-ins

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
