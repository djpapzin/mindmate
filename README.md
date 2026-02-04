# MindMate - Telegram Wellness Bot

A compassionate Telegram chatbot that provides mental wellness support using OpenAI's GPT.

## Features

- Empathetic conversational support
- Healthy coping strategy suggestions
- 24/7 availability for users to express their feelings
- Crisis keyword detection with South African helpline resources
- Conversation history tracking (last 10 messages)

## Setup

1. Clone this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your credentials:
   ```
   TELEGRAM_BOT_TOKEN=8518887693:AAGghCm4UzNQhhxqSQHi-q-wYKPK4SZ_k88
   OPENAI_API_KEY=your_openai_key_here
   ```

   - `TELEGRAM_BOT_TOKEN`: The token provided above, or get your own from [@BotFather](https://t.me/botfather) on Telegram
   - `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

5. Run the bot:
   ```bash
   python bot.py
   ```

## ⚠️ Security Warning

**IMPORTANT: Keep your credentials secure!**

- **Never commit your `.env` file to version control.** The `.env` file contains sensitive tokens that should remain private.
- **Never share your bot token publicly.** If your Telegram bot token is compromised, anyone can control your bot. If you suspect your token has been exposed, immediately revoke it via [@BotFather](https://t.me/botfather) and generate a new one.
- **Never share your OpenAI API key.** A compromised API key can result in unauthorized usage and charges to your account.
- The `.env.example` file contains only placeholder values and is safe to commit.

## Usage

- `/start` - Start a conversation with the bot (clears history)
- `/clear` - Clear conversation history
- `/help` - Show available commands
- Send any message to chat with the wellness assistant

## Crisis Support

The bot automatically detects crisis-related keywords and provides immediate access to South African mental health resources:

- SADAG: 0800 567 567
- Lifeline South Africa: 0861 322 322
- Suicide Crisis Line: 0800 567 567
- LifeLine WhatsApp: 0600 123 456

## Disclaimer

This bot is not a replacement for professional mental health support. It is an AI companion for emotional reflection and basic wellness support. If you're experiencing a mental health crisis, please contact a mental health professional or crisis helpline immediately.
