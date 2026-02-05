"""
Fixed version of MindMate Bot for Render deployment
Uses async instead of threading to avoid issues
"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from flask import Flask
from openai import OpenAI, OpenAIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create Flask app
app = Flask(__name__)

# In-memory conversation history storage
conversation_history: dict[int, list[dict[str, str]]] = {}
MAX_HISTORY_LENGTH = 10

SYSTEM_PROMPT = """You are an AI mental wellness companion. You help with emotional reflection, journaling prompts, basic psychoeducation about stress and habits, and planning small next steps. You are not a therapist, doctor, or emergency service. Do not diagnose, treat, or provide medical advice. If the user mentions self-harm, suicide, wanting to die, harming others, or being in immediate danger, you must: 1) Say you cannot handle crises. 2) Strongly encourage them to reach out to a trusted person, local emergency number, or mental health professional. 3) Stay calm and supportive. Always be concise, kind, and non-judgmental."""

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "want to die",
    "self-harm", "self harm", "hurt myself", "end it all", "no reason to live"
]

CRISIS_RESPONSE = """🚨 I'm concerned about what you've shared. I'm not equipped to handle crisis situations, but I want you to know that help is available right now.

Please reach out to one of these South African crisis resources:

📞 SADAG: 0800 567 567
📞 Lifeline: 0861 322 322
📞 Suicide Crisis Line: 0800 567 567

You matter, and you don't have to face this alone. 💙"""

# Flask routes
@app.route('/')
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "mindmate-bot"}

@app.route('/health')
def health():
    """Alternative health endpoint"""
    return "OK", 200

@app.route('/debug')
def debug():
    """Debug endpoint to check bot status"""
    return {
        "bot_running": bot_running,
        "conversation_history_size": len(conversation_history),
        "telegram_token_configured": bool(TELEGRAM_BOT_TOKEN),
        "openai_token_configured": bool(OPENAI_API_KEY)
    }

# Bot functions
def detect_crisis_keywords(message: str) -> bool:
    """Check if a message contains crisis-related keywords."""
    message_lower = message.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in message_lower:
            return True
    return False

def get_conversation_history(user_id: int) -> list[dict[str, str]]:
    """Get conversation history for a user."""
    return conversation_history.get(user_id, [])

def add_to_history(user_id: int, role: str, content: str) -> None:
    """Add a message to the user's conversation history."""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": role, "content": content})
    
    if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY_LENGTH:]

def clear_conversation_history(user_id: int) -> None:
    """Clear conversation history for a user."""
    if user_id in conversation_history:
        del conversation_history[user_id]

# Bot handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    clear_conversation_history(user.id)
    
    welcome_message = (
        "Hello! I'm MindMate, your AI wellness companion. 🌱\n\n"
        "I can help you with:\n"
        "• Emotional reflection and journaling prompts\n"
        "• Basic information about stress and healthy habits\n"
        "• Planning small, manageable next steps\n\n"
        "⚠️ Important: I am NOT a therapist or emergency service.\n\n"
        "How are you feeling today?"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_message = (
        "Here's how I can support you:\n\n"
        "• Send me a message about how you're feeling\n"
        "• Ask for journaling prompts or reflection questions\n"
        "• Learn about stress management\n\n"
        "Commands:\n"
        "/start - Start a new conversation\n"
        "/clear - Clear conversation history\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_message)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command."""
    user = update.effective_user
    clear_conversation_history(user.id)
    await update.message.reply_text("Your conversation history has been cleared. 🧹")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    user = update.effective_user
    user_message = update.message.text
    
    logger.info(f"Received message from user {user.id}: {user_message[:50]}...")
    
    # Check for crisis keywords
    if detect_crisis_keywords(user_message):
        logger.warning(f"Crisis keywords detected from user {user.id}")
        await update.message.reply_text(CRISIS_RESPONSE)
        return
    
    try:
        # Build messages array
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(get_conversation_history(user.id))
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        
        # Add to history
        add_to_history(user.id, "user", user_message)
        add_to_history(user.id, "assistant", reply)
        
        logger.info(f"Responded to user {user.id}")
        await update.message.reply_text(reply)
        
    except OpenAIError as e:
        logger.error(f"OpenAI API error for user {user.id}: {e}")
        await update.message.reply_text("I'm having trouble processing your message right now. Please try again. 💙")
    except Exception as e:
        logger.error(f"Unexpected error for user {user.id}: {e}")
        await update.message.reply_text("Something went wrong. Please try again later.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(f"Exception while handling update: {context.error}")

# Global variable to track bot status
bot_running = False

async def run_telegram_bot():
    """Run the Telegram bot."""
    global bot_running
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    logger.info("Starting Telegram bot polling...")
    
    # Initialize and start polling manually to avoid signal handler issues
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Bot polling started successfully!")
    
    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Stopping bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def run_flask_app():
    """Run Flask app in a separate thread."""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting Flask app on port {port}...")
    app.run(host='0.0.0.0', port=port)

def main():
    """Main function to run both Flask and Telegram bot."""
    logger.info("Starting MindMate Bot application...")
    
    # Start Flask in a thread
    import threading
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    import time
    time.sleep(2)
    
    # Run Telegram bot in main thread
    try:
        asyncio.run(run_telegram_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
