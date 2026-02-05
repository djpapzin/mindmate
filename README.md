# 🧠 MindMate - AI Mental Wellness Companion

<p align="center">
  <strong>A compassionate Telegram chatbot providing 24/7 mental wellness support powered by OpenAI</strong>
</p>

<p align="center">
  <a href="https://t.me/mywellnesscompanion_bot">🤖 Try MindMate</a> •
  <a href="#features">Features</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#deployment">Deploy</a>
</p>

---

## ✨ Features

### Current (v1.0)
| Feature | Description |
|---------|-------------|
| 💬 **Empathetic Chat** | AI-powered conversations with emotional intelligence |
| 🚨 **Crisis Detection** | Automatic detection of crisis keywords with immediate helpline resources |
| 🇿🇦 **SA Resources** | South African mental health helplines (SADAG, Lifeline, etc.) |
| 📝 **Context Memory** | Remembers last 10 messages per user for coherent conversations |
| 👥 **User Isolation** | Private conversations - users can't see each other's chats |
| 🔒 **Privacy First** | No data stored permanently, conversations reset on deploy |

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Start a conversation (clears history) |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |

---

## 🗺️ Roadmap

### 🎯 Phase 1: Foundation (v1.1) - *In Progress*
- [ ] Persistent database (PostgreSQL/Redis)
- [ ] User profiles (name, preferences)
- [ ] Rate limiting & abuse prevention
- [ ] Improved error handling
- [ ] Usage analytics dashboard

### 🌱 Phase 2: Wellness Tools (v2.0)
- [ ] `/mood` - Daily mood tracking with insights
- [ ] `/breathe` - Guided breathing exercises (4-7-8, box breathing)
- [ ] `/journal` - Prompted journaling for reflection
- [ ] `/gratitude` - Daily gratitude practice
- [ ] Daily check-in reminders (opt-in)
- [ ] Mood history & trends visualization

### 🎨 Phase 3: Personalization (v2.5)
- [ ] Remember user's name permanently
- [ ] Personalized coping strategies based on history
- [ ] Custom conversation styles (casual, professional, gentle)
- [ ] Track recurring concerns & provide tailored resources
- [ ] Progress insights ("You've been feeling better this week!")

### 🚀 Phase 4: Advanced Features (v3.0)
- [ ] 🎤 Voice message support
- [ ] 🌍 Multi-language support (Zulu, Afrikaans, Xhosa)
- [ ] 🧘 Meditation timer with ambient sounds
- [ ] 📅 Calendar integration for self-care reminders
- [ ] 🆘 Emergency contact notification (with consent)
- [ ] 📊 Weekly wellness reports

### 💎 Phase 5: Scale (v4.0)
- [ ] Premium features tier
- [ ] Therapist directory integration
- [ ] Corporate wellness program support
- [ ] API for third-party integrations
- [ ] White-label solution

---

## 🛠️ Technical Roadmap

| Improvement | Status | Priority |
|-------------|--------|----------|
| Webhook mode (vs polling) | 🔜 Planned | High |
| Docker containerization | 🔜 Planned | Medium |
| CI/CD with GitHub Actions | 🔜 Planned | Medium |
| Structured logging (Sentry) | 🔜 Planned | Medium |
| Test coverage > 80% | ✅ Started | High |

---

## 🚀 Deployment

**Live Instance:** https://mindmate-uidn.onrender.com

### Deploy Your Own (Free)

#### Option 1: Render (Recommended)
1. Fork this repository
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Configure:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python bot.py
   Instance Type: Free
   ```
5. Add Environment Variables:
   - `TELEGRAM_BOT_TOKEN` - from [@BotFather](https://t.me/botfather)
   - `OPENAI_API_KEY` - from [OpenAI](https://platform.openai.com/api-keys)
6. Deploy!

> 💡 **Tip:** Use [UptimeRobot](https://uptimerobot.com) to ping your URL every 5 minutes to prevent cold starts.

#### Option 2: Railway
1. Fork this repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables
4. Deploy!

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

# Run the bot
python bot.py

# Run tests
python test_bot.py
```

---

## 🧪 Testing

```bash
python test_bot.py
```

**Test Coverage:**
- ✅ Crisis keyword detection
- ✅ Conversation history management
- ✅ User isolation
- ✅ Message format validation
- ✅ History limit enforcement

---

## 🆘 Crisis Support

MindMate automatically detects crisis-related messages and provides immediate access to help:

| Resource | Contact | Available |
|----------|---------|-----------|
| **SADAG** | 0800 567 567 | 24/7 |
| **Lifeline SA** | 0861 322 322 | 24/7 |
| **Suicide Crisis Line** | 0800 567 567 | 24/7 |
| **LifeLine WhatsApp** | 0600 123 456 | 24/7 |

**Crisis keywords detected:** suicide, self-harm, kill myself, end my life, want to die, no reason to live, and more.

---

## ⚠️ Important Disclaimers

> **MindMate is NOT a replacement for professional mental health support.**

- This is an AI companion for emotional reflection and basic wellness support
- If you're experiencing a mental health crisis, please contact a professional or crisis helpline
- The bot does not provide medical advice, diagnosis, or treatment
- Conversations are not monitored by mental health professionals

---

## 🔒 Security

- Never commit `.env` files to version control
- Rotate tokens immediately if compromised
- Bot token: Revoke via [@BotFather](https://t.me/botfather)
- OpenAI key: Rotate at [platform.openai.com](https://platform.openai.com/api-keys)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with 💚 for mental wellness in South Africa
</p>
