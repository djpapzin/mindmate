# MindMate - Telegram Wellness Bot

A compassionate Telegram chatbot that provides mental wellness support using OpenAI's GPT.

🤖 **Try it:** [@mywellnesscompanion_bot](https://t.me/mywellnesscompanion_bot)

## Features

- Empathetic conversational support
- Healthy coping strategy suggestions
- 24/7 availability for users to express their feelings
- Crisis keyword detection with South African helpline resources
- Conversation history tracking (last 10 messages)

## Deployment

This bot is deployed on **Render** (Free Tier):
- **URL:** https://mindmate-uidn.onrender.com
- **Auto-deploys** on push to main branch

### Deploy Your Own (Render - Free)

1. Fork this repository
2. Go to [render.com](https://render.com) and sign in
3. Create a **New Web Service**
4. Connect your GitHub repo
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
6. Add Environment Variables:
   - `TELEGRAM_BOT_TOKEN` - from [@BotFather](https://t.me/botfather)
   - `OPENAI_API_KEY` - from [OpenAI](https://platform.openai.com/api-keys)
7. Deploy!

> **Note:** Free tier spins down after inactivity (~50s cold start delay). Use [UptimeRobot](https://uptimerobot.com) to ping your URL every 14 minutes to keep it awake.

## Local Development

1. Clone this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

4. Add your credentials to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_token
   OPENAI_API_KEY=your_openai_key
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## ⚠️ Security Warning

**IMPORTANT: Keep your credentials secure!**

- **Never commit your `.env` file to version control.**
- **Never share your bot token publicly.** If compromised, revoke it via [@BotFather](https://t.me/botfather).
- **Never share your OpenAI API key.** A compromised key can result in unauthorized charges.

## Usage

| Command | Description |
|---------|-------------|
| `/start` | Start a conversation (clears history) |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |

Send any message to chat with MindMate!

## Crisis Support

The bot automatically detects crisis-related keywords and provides immediate access to South African mental health resources:

| Resource | Contact |
|----------|---------|
| SADAG | 0800 567 567 |
| Lifeline South Africa | 0861 322 322 |
| Suicide Crisis Line | 0800 567 567 |
| LifeLine WhatsApp | 0600 123 456 |

## Disclaimer

This bot is not a replacement for professional mental health support. It is an AI companion for emotional reflection and basic wellness support. If you're experiencing a mental health crisis, please contact a mental health professional or crisis helpline immediately.

## License

MIT
