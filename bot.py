"""
MindMate - AI Mental Wellness Telegram Bot
A compassionate chatbot providing 24/7 mental wellness support.
"""

import asyncio
import logging
import os
import threading

from dotenv import load_dotenv
from flask import Flask, jsonify
from openai import OpenAI, OpenAIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============================================================================
# Configuration
# =============================================================================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 10000))
MAX_HISTORY_LENGTH = 10

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

SYSTEM_PROMPT = """You are MindMate, an AI mental wellness companion. You provide:
- Emotional reflection and support
- Journaling prompts
- Basic psychoeducation about stress and habits
- Help planning small, manageable next steps

You are NOT a therapist, doctor, or emergency service. Never diagnose or provide medical advice.
Be concise, warm, and non-judgmental. Use emojis sparingly."""

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "want to die", "end my life",
    "self-harm", "self harm", "hurt myself", "end it all", "no reason to live",
    "don't want to live", "better off dead"
]

CRISIS_RESPONSE = """🚨 I'm concerned about what you've shared. Help is available right now.

📞 **South African Crisis Resources:**
• SADAG: 0800 567 567 (24/7)
• Lifeline SA: 0861 322 322 (24/7)
• Suicide Crisis Line: 0800 567 567
• LifeLine WhatsApp: 0600 123 456

You matter. Please reach out to one of these services. 💙"""

WELCOME_MESSAGE = """Hello! I'm MindMate, your AI wellness companion. 🌱

I can help you with:
• Emotional reflection and journaling prompts
• Information about stress and healthy habits
• Planning small, manageable next steps

⚠️ I am NOT a therapist or emergency service.

How are you feeling today?"""

HELP_MESSAGE = """**How I can support you:**

• Send me a message about how you're feeling
• Ask for journaling prompts or reflection questions
• Learn about stress management

**Commands:**
/start - Start fresh conversation
/clear - Clear conversation history
/help - Show this message

Remember: I'm here to support, not replace professional help. 💙"""

# =============================================================================
# Global State
# =============================================================================

conversation_history: dict[int, list[dict[str, str]]] = {}
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
bot_running = False

# =============================================================================
# Flask App (Health Checks)
# =============================================================================

flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return jsonify({"status": "healthy", "service": "mindmate-bot", "bot_running": bot_running})

@flask_app.route("/health")
def health_simple():
    return "OK", 200

# =============================================================================
# Conversation History
# =============================================================================

def get_history(user_id: int) -> list[dict[str, str]]:
    return conversation_history.get(user_id, [])

def add_to_history(user_id: int, role: str, content: str) -> None:
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": role, "content": content})
    if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY_LENGTH:]

def clear_history(user_id: int) -> None:
    conversation_history.pop(user_id, None)

# =============================================================================
# Crisis Detection
# =============================================================================

def detect_crisis(message: str) -> bool:
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CRISIS_KEYWORDS)

# =============================================================================
# Telegram Bot Handlers
# =============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started bot")
    clear_history(user_id)
    await update.message.reply_text(WELCOME_MESSAGE)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    clear_history(user_id)
    logger.info(f"User {user_id} cleared history")
    await update.message.reply_text("Conversation history cleared. 🧹")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    message = update.message.text
    
    logger.info(f"Message from user {user_id}")
    
    # Crisis detection
    if detect_crisis(message):
        logger.warning(f"Crisis detected - user {user_id}")
        await update.message.reply_text(CRISIS_RESPONSE, parse_mode="Markdown")
        return
    
    if not openai_client:
        await update.message.reply_text("I'm temporarily unavailable. Please try again later.")
        return
    
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(get_history(user_id))
        messages.append({"role": "user", "content": message})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=600,
            temperature=0.8,
            presence_penalty=0.6,
            frequency_penalty=0.3
        )
        reply = response.choices[0].message.content
        
        add_to_history(user_id, "user", message)
        add_to_history(user_id, "assistant", reply)
        
        await update.message.reply_text(reply)
        logger.info(f"Responded to user {user_id}")
        
    except OpenAIError as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("I'm having trouble right now. Please try again. 💙")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Something went wrong. Please try again.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Bot error: {context.error}")

# =============================================================================
# Bot Runner
# =============================================================================

async def run_bot():
    global bot_running
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured!")
        return
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    logger.info("Initializing bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    bot_running = True
    logger.info("✅ Bot is running!")
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        bot_running = False
        logger.info("Shutting down...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

def run_flask():
    logger.info(f"Starting health server on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

# =============================================================================
# Main
# =============================================================================

def main():
    logger.info("=" * 50)
    logger.info("Starting MindMate Bot")
    logger.info("=" * 50)
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    if not OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY not set")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
        raise

if __name__ == "__main__":
    main()
