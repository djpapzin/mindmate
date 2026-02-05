"""
Simplified MindMate Bot for Render deployment
Minimal version to ensure it starts properly
"""

import logging
import os
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
    logger.info("Health check accessed")
    return {
        "status": "healthy", 
        "service": "mindmate-bot",
        "tokens_configured": {
            "telegram": bool(TELEGRAM_BOT_TOKEN),
            "openai": bool(OPENAI_API_KEY)
        }
    }

@app.route('/health')
def health():
    """Alternative health endpoint"""
    return "OK", 200

@app.route('/debug')
def debug():
    """Debug endpoint to check bot status"""
    import threading
    active_threads = threading.enumerate()
    thread_count = len(active_threads)
    
    # Check if bot thread is running
    bot_thread_found = False
    for thread in active_threads:
        if 'run_telegram_bot' in str(thread):
            bot_thread_found = True
            break
    
    return {
        "threads": thread_count,
        "active_threads": [t.name for t in active_threads],
        "bot_thread_found": bot_thread_found,
        "bot_thread_alive": any(t.is_alive() for t in active_threads if 'run_telegram_bot' in str(t)),
        "conversation_history_size": len(conversation_history),
        "tokens_configured": {
            "telegram": bool(TELEGRAM_BOT_TOKEN),
            "openai": bool(OPENAI_API_KEY)
        }
    }

def run_telegram_bot():
    """Run Telegram bot - simplified version"""
    logger.info("run_telegram_bot function called")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found")
        return
    
    try:
        import asyncio
        import threading
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        from openai import OpenAI
        
        logger.info("Starting Telegram bot...")
        
        # Simple response handler
        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # Create and configure application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", handle_message))
        application.add_handler(CommandHandler("help", handle_message))
        application.add_handler(CommandHandler("clear", handle_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Create new event loop for this thread
        logger.info("Creating event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start polling
        logger.info("Bot polling started...")
        loop.run_until_complete(application.run_polling(allowed_updates=Update.ALL_TYPES))
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

def main():
    """Main function"""
    logger.info("Starting MindMate Bot (Simple Version)...")
    
    # Start Telegram bot in background
    import threading
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
