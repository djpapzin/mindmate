"""
Final version of MindMate Bot
Run bot in main process, Flask in background thread
"""

import asyncio
import logging
import os
import threading
from flask import Flask
from dotenv import load_dotenv

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

# Create Flask app
app = Flask(__name__)

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
    """Debug endpoint"""
    return {
        "bot_running": bot_running,
        "flask_thread_alive": flask_thread.is_alive() if 'flask_thread' in globals() else False,
        "tokens_configured": {
            "telegram": bool(TELEGRAM_BOT_TOKEN),
            "openai": bool(OPENAI_API_KEY)
        }
    }

# Bot functions
async def handle_message(update, context):
    """Handle incoming messages."""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"Message from {user.first_name}: {message_text}")
    
    if "/start" in message_text:
        response = "Hello! I'm MindMate, your AI wellness companion. How are you feeling today?"
    elif "/help" in message_text:
        response = "Available commands: /start, /help, /clear"
    elif "/clear" in message_text:
        response = "Conversation history cleared."
    else:
        response = f"I hear you saying: {message_text}. I'm here to support you!"
    
    await update.message.reply_text(response)

async def run_telegram_bot():
    """Run Telegram bot in main process."""
    global bot_running
    bot_running = True
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found")
        return
    
    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        
        logger.info("Starting Telegram bot...")
        
        # Create and configure application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", handle_message))
        application.add_handler(CommandHandler("help", handle_message))
        application.add_handler(CommandHandler("clear", handle_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start polling
        logger.info("Bot polling started...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        bot_running = False

def run_flask_app():
    """Run Flask app in background thread."""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting Flask app on port {port}...")
    app.run(host='0.0.0.0', port=port)

# Global variable to track bot status
bot_running = False
flask_thread = None

def main():
    """Main function - bot in main, Flask in thread."""
    logger.info("Starting MindMate Bot (Final Version)...")
    
    # Start Flask in background thread
    global flask_thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    import time
    time.sleep(2)
    
    # Run Telegram bot in main process
    try:
        asyncio.run(run_telegram_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
