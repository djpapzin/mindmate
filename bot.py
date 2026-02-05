import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env file
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

# In-memory conversation history storage: {user_id: [{"role": "user/assistant", "content": "..."}]}
conversation_history: dict[int, list[dict[str, str]]] = {}
MAX_HISTORY_LENGTH = 10  # Store last 10 messages (5 exchanges)

SYSTEM_PROMPT = """You are an AI mental wellness companion. You help with emotional reflection, journaling prompts, basic psychoeducation about stress and habits, and planning small next steps. You are not a therapist, doctor, or emergency service. Do not diagnose, treat, or provide medical advice. If the user mentions self-harm, suicide, wanting to die, harming others, or being in immediate danger, you must: 1) Say you cannot handle crises. 2) Strongly encourage them to reach out to a trusted person, local emergency number, or mental health professional. 3) Stay calm and supportive. Always be concise, kind, and non-judgmental."""

CRISIS_KEYWORDS = [
    "suicide",
    "suicidal",
    "kill myself",
    "want to die",
    "self-harm",
    "self harm",
    "hurt myself",
    "end it all",
    "no reason to live",
]

CRISIS_RESPONSE = """🚨 I'm concerned about what you've shared. I'm not equipped to handle crisis situations, but I want you to know that help is available right now.

Please reach out to one of these South African crisis resources:

📞 SADAG (SA Depression and Anxiety Group): 0800 567 567
📞 Lifeline South Africa: 0861 322 322
📞 Suicide Crisis Line: 0800 567 567
💬 LifeLine WhatsApp: 0600 123 456

These services are staffed by trained professionals who can provide immediate support.

You matter, and you don't have to face this alone. Please reach out to them or a trusted person in your life. 💙"""


def detect_crisis_keywords(message: str) -> bool:
    """Check if a message contains crisis-related keywords (case-insensitive)."""
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
    
    # Keep only the last MAX_HISTORY_LENGTH messages
    if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY_LENGTH:]


def clear_conversation_history(user_id: int) -> None:
    """Clear conversation history for a user."""
    if user_id in conversation_history:
        del conversation_history[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Clear conversation history on /start
    clear_conversation_history(user.id)
    logger.info(f"Cleared conversation history for user {user.id}")
    
    welcome_message = (
        "Hello! I'm MindMate, your AI wellness companion. 🌱\n\n"
        "I can help you with:\n"
        "• Emotional reflection and journaling prompts\n"
        "• Basic information about stress and healthy habits\n"
        "• Planning small, manageable next steps\n\n"
        "⚠️ Important: I am NOT a therapist, doctor, or emergency service. "
        "I cannot diagnose conditions, provide medical advice, or handle crises.\n\n"
        "If you're in crisis or experiencing thoughts of self-harm, please reach out to "
        "a trusted person, your local emergency number, or a mental health professional.\n\n"
        "How are you feeling today?"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the /help command is issued."""
    logger.info(f"User {update.effective_user.id} requested help")
    
    help_message = (
        "Here's how I can support you:\n\n"
        "• Send me a message about how you're feeling\n"
        "• Ask for journaling prompts or reflection questions\n"
        "• Learn about stress management and healthy habits\n"
        "• Get help planning small next steps\n\n"
        "Commands:\n"
        "/start - Start a new conversation\n"
        "/clear - Clear conversation history\n"
        "/help - Show this help message\n\n"
        "Remember: I'm here to support, not to replace professional help."
    )
    await update.message.reply_text(help_message)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the user's conversation history."""
    user = update.effective_user
    clear_conversation_history(user.id)
    logger.info(f"User {user.id} cleared their conversation history")
    
    await update.message.reply_text(
        "Your conversation history has been cleared. 🧹\n\n"
        "Feel free to start fresh whenever you're ready."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages and send them to OpenAI for a response."""
    user = update.effective_user
    user_message = update.message.text
    
    logger.info(f"Received message from user {user.id}")

    # Check for crisis keywords BEFORE sending to OpenAI
    if detect_crisis_keywords(user_message):
        logger.warning(f"Crisis keywords detected in message from user {user.id}")
        await update.message.reply_text(CRISIS_RESPONSE)
        return

    try:
        # Build messages array with system prompt and conversation history
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
        
        # Add both user message and assistant reply to history
        add_to_history(user.id, "user", user_message)
        add_to_history(user.id, "assistant", reply)
        
        logger.info(f"Successfully generated response for user {user.id}")
        await update.message.reply_text(reply)
        
    except OpenAIError as e:
        logger.error(f"OpenAI API error for user {user.id}: {e}")
        await update.message.reply_text(
            "I'm having trouble processing your message right now. "
            "Please try again in a moment. 💙"
        )
    except Exception as e:
        logger.error(f"Unexpected error for user {user.id}: {e}")
        await update.message.reply_text(
            "Something went wrong on my end. Please try again later. "
            "If this keeps happening, the service may be temporarily unavailable."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Exception while handling an update: {context.error}")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'MindMate bot is running!')
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


def start_health_server():
    """Start a simple HTTP server for health checks."""
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()


def main() -> None:
    """Start the bot."""
    # Validate configuration
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in environment variables")
        raise ValueError("OPENAI_API_KEY is required")

    # Start health check server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    logger.info("Starting MindMate Bot...")

    # Build the application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)

    # Start the bot with polling
    logger.info("Bot is running with polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
