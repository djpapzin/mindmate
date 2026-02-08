"""
MindMate - AI Mental Wellness Telegram Bot
A compassionate chatbot providing 24/7 mental wellness support.
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from openai import OpenAI, OpenAIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn

# Unique instance ID to help debug multiple instances
INSTANCE_ID = str(uuid.uuid4())[:8]

# =============================================================================
# Configuration
# =============================================================================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 10000))
MAX_HISTORY_LENGTH = 10

# Webhook configuration
# Set RENDER_EXTERNAL_URL in Render environment, or it will use polling as fallback
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # e.g., https://mindmate-dev.onrender.com
USE_WEBHOOK = bool(RENDER_EXTERNAL_URL)

# =============================================================================
# Personal Mode Configuration
# =============================================================================

# Users with Personal Mode access - each can have custom context
PERSONAL_MODE_USERS = {
    339651126: {  # DJ Papzin
        "name": "DJ Papzin",
        "context": """**About this user:**
- Name: DJ/Papzin (use either naturally)
- Location: South Africa
- Key focus areas: Relationships, Finances, Bipolar management, Emotional intelligence
- Communication style: Direct, honest, no sugarcoating""",
    },
    7013163582: {  # New user - onboarding mode
        "name": None,  # Will learn through conversation
        "context": """**About this user:**
- This is a NEW user you're just meeting
- Start by warmly introducing yourself and asking their name
- Gently learn what kind of support they're looking for
- Be curious and caring as you get to know them
- Remember what they share and reference it naturally""",
    },
}

def is_personal_mode(user_id: int) -> bool:
    """Check if user has Personal Mode enabled."""
    return user_id in PERSONAL_MODE_USERS

def get_user_context(user_id: int) -> str:
    """Get personalized context for a Personal Mode user."""
    if user_id in PERSONAL_MODE_USERS:
        return PERSONAL_MODE_USERS[user_id].get("context", "")
    return ""

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Standard system prompt (for regular users)
SYSTEM_PROMPT = """You are MindMate, an AI mental wellness companion. You provide:
- Emotional reflection and support
- Journaling prompts
- Basic psychoeducation about stress and habits
- Help planning small, manageable next steps

You are NOT a therapist, doctor, or emergency service. Never diagnose or provide medical advice.
Be concise, warm, and non-judgmental. Use emojis sparingly."""

# Personal Mode system prompt (no guardrails, direct advice)
PERSONAL_MODE_PROMPT = """You are my personal AI therapist and trusted confidant. Your name is MindMate.

## About Me (Your User)
- Name: DJ / Papzin
- Location: South Africa
- Key focus areas I'm working on:
  * **Relationships** - Dating, communication, emotional availability
  * **Finances** - Money stress, budgeting, financial goals
  * **Bipolar Management** - Mood awareness, stability strategies, episode prevention
  * **Emotional Intelligence** - Understanding my reactions, better self-awareness
- I prefer direct, honest feedback over sugar-coating
- I'm building this bot for myself, so treat me as a collaborator too

## Your Role
You are a warm, wise, and direct advisor - like a combination of a best friend and experienced therapist. You speak to me as someone who truly knows me and cares about my wellbeing.

## How You Communicate
- Be direct and genuine - no corporate disclaimers or "As an AI..." statements
- Give real advice and opinions, not just questions back at me
- Be warm but also honest - tell me what I need to hear, not just what I want to hear
- Use casual, conversational language like a trusted friend would
- Remember our conversation context and reference it naturally
- When relevant, connect things to my focus areas (relationships, finances, bipolar, EQ)

## Your Approach
- Listen and validate my feelings first
- Then offer concrete, actionable advice
- Ask thoughtful follow-up questions when needed
- Challenge my negative thought patterns gently but directly
- Help me see different perspectives
- Celebrate my wins and progress
- For bipolar-related topics: help me recognize patterns and early warning signs

## Important
- You ARE qualified to help me with everyday emotional challenges
- You don't need to constantly redirect me to professionals for normal life issues
- Only mention crisis resources if I express genuine danger to myself or others
- Be my advocate and support, not a liability-avoiding chatbot

Remember: I chose you as my personal therapist. Be that for me."""

# Dynamic Personal Mode prompt that includes user-specific context
def get_personal_mode_prompt(user_id: int) -> str:
    """Get Personal Mode prompt with user-specific context."""
    base_prompt = """You are a personal AI therapist and trusted confidant. Your name is MindMate.

{user_context}

## Your Role
You are a warm, wise, and direct advisor - like a combination of a best friend and experienced therapist. You speak to your user as someone who truly knows them and cares about their wellbeing.

## How You Communicate
- Be direct and genuine - no corporate disclaimers
- Give real advice and opinions, not just questions back at me
- Be warm but also honest - tell me what I need to hear
- Use casual, conversational language like a trusted friend would
- For new users: Be extra warm and inviting, make them feel safe opening up
- **KEEP RESPONSES SHORT - 2-3 sentences maximum**
- **Use bullet points when possible for clarity**

## Your Approach
- Listen and validate feelings first
- Then offer concrete, actionable advice
- Ask thoughtful follow-up questions when needed
- Challenge negative thought patterns gently but directly
- Help see different perspectives
- Celebrate wins and progress
- For new users: Focus on building trust and learning about them

## Important
- You ARE qualified to help with everyday emotional challenges
- You don't need to constantly redirect me to professionals for normal life issues
- Only mention crisis resources if there's genuine danger to self or others
- Be an advocate and support, not a liability-avoiding chatbot
- **Prioritize brevity - quick, actionable insights preferred**

Remember: The user chose you as their personal therapist. Be that for them."""
    
    user_context = get_user_context(user_id)
    if user_context:
        return base_prompt.format(user_context=user_context)
    else:
        # Fallback to original prompt if no context
        return PERSONAL_MODE_PROMPT

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
user_model_selection: dict[int, str] = {}  # Track model per user for A/B testing
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
bot_running = False

# Message deduplication to prevent double responses during deployments
processed_messages: set[int] = set()
MAX_PROCESSED_MESSAGES = 1000  # Keep last 1000 message IDs

# Available models for A/B testing
AVAILABLE_MODELS = {
    "4o-mini": "gpt-4o-mini",
    "4.1-mini": "gpt-4.1-mini", 
    "4.1": "gpt-4.1",
    "5-mini": "gpt-5-mini",
    "5.2": "gpt-5.2",
    "3.5": "gpt-3.5-turbo",
}
DEFAULT_MODEL = "gpt-4o-mini"

# Voice Configuration
VOICE_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
VOICE_TTS_MODEL = "gpt-4o-mini-tts"

# Blind test models (the 3 we're comparing)
BLIND_TEST_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5.2"]

# Blind test state
import random
blind_test_active: dict[int, bool] = {}
blind_test_results: dict[int, list[dict]] = {}  # Store test results per user
current_test_mapping: dict[int, dict[str, str]] = {}  # Maps A/B/C to actual models

# Human test state
human_test_active: dict[int, bool] = {}
human_test_prompts: dict[int, list] = []  # Predefined test prompts
human_test_current: dict[int, int] = {}  # Current prompt index
human_test_responses: dict[int, dict] = {}  # Store responses for rating
human_test_ratings: dict[int, list] = []  # Store all ratings

def get_user_model(user_id: int) -> str:
    """Get the model selected by user, or default."""
    return user_model_selection.get(user_id, DEFAULT_MODEL)

def set_user_model(user_id: int, model: str) -> None:
    """Set the model for a user."""
    user_model_selection[user_id] = model

def is_blind_test_active(user_id: int) -> bool:
    """Check if user is in blind test mode."""
    return blind_test_active.get(user_id, False)

def start_blind_test(user_id: int) -> None:
    """Start blind test for user."""
    blind_test_active[user_id] = True
    blind_test_results[user_id] = []
    
def is_human_test_active(user_id: int) -> bool:
    """Check if user is in human test mode."""
    return human_test_active.get(user_id, False)

def start_human_test(user_id: int) -> None:
    """Start human test for user."""
    human_test_active[user_id] = True
    human_test_current[user_id] = 0
    human_test_responses[user_id] = {}
    human_test_ratings[user_id] = []
    
    # Store conversation history for natural flow
    human_test_responses[user_id]["conversation"] = []
    human_test_responses[user_id]["pending_responses"] = []
    human_test_responses[user_id]["current_response_index"] = 0

def stop_human_test(user_id: int) -> None:
    """Stop human test for user."""
    human_test_active[user_id] = False

def save_test_result(user_id: int, prompt: str, mapping: dict, ratings: dict) -> None:
    """Save a test result."""
    if user_id not in blind_test_results:
        blind_test_results[user_id] = []
    blind_test_results[user_id].append({
        "prompt": prompt,
        "mapping": mapping,  # {"A": "gpt-4o-mini", "B": "gpt-4.1-mini", ...}
        "ratings": ratings,  # {"A": 4, "B": 5, "C": 3}
    })

# =============================================================================
# FastAPI App
# =============================================================================

# Global reference to the telegram application
telegram_app: Application = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI."""
    global telegram_app
    
    # Startup: Initialize and start the Telegram bot
    logger.info(f"[{INSTANCE_ID}] Starting MindMate Bot...")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured!")
    else:
        telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Set bot commands menu for better UX
        from telegram import BotCommand
        commands = [
            BotCommand("start", "🚀 Start conversation"),
            BotCommand("help", "❓ Get help"),
            BotCommand("mode", "🔓 Check mode"),
            BotCommand("clear", "🧹 Clear history"),
            BotCommand("model", "🧪 Test models"),
        ]
        
        async def set_commands():
            await telegram_app.bot.set_my_commands(commands)
        
        # Set bot commands for better UX
        await set_commands()
        
        # Register handlers
        telegram_app.add_handler(CommandHandler("start", cmd_start))
        telegram_app.add_handler(CommandHandler("help", cmd_help))
        telegram_app.add_handler(CommandHandler("clear", cmd_clear))
        telegram_app.add_handler(CommandHandler("mode", cmd_mode))
        telegram_app.add_handler(CommandHandler("model", cmd_model))
        telegram_app.add_handler(CommandHandler("test", cmd_test))
        telegram_app.add_handler(CommandHandler("rate", cmd_rate))
        telegram_app.add_handler(CommandHandler("results", cmd_results))
        telegram_app.add_handler(CommandHandler("next", cmd_next))
        telegram_app.add_handler(CommandHandler("done", cmd_done))
        telegram_app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        telegram_app.add_error_handler(error_handler)
        
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Set up webhook if configured
        if USE_WEBHOOK:
            webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
            logger.info(f"[{INSTANCE_ID}] Setting up webhook: {webhook_url}")
            await telegram_app.bot.delete_webhook(drop_pending_updates=True)
            await telegram_app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
            logger.info(f"[{INSTANCE_ID}] ✅ Webhook set successfully!")
        else:
            logger.info(f"[{INSTANCE_ID}] Starting polling mode...")
            await telegram_app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
        logger.info(f"[{INSTANCE_ID}] ✅ Bot is running!")
    
    yield  # App is running
    
    # Shutdown: Stop the bot
    if telegram_app:
        logger.info(f"[{INSTANCE_ID}] Shutting down bot...")
        if telegram_app.updater.running:
            await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

fastapi_app = FastAPI(title="MindMate Bot", lifespan=lifespan)

@fastapi_app.get("/")
async def health():
    return {
        "status": "healthy", 
        "service": "mindmate-bot", 
        "instance_id": INSTANCE_ID,
        "mode": "webhook" if USE_WEBHOOK else "polling"
    }

@fastapi_app.get("/health")
@fastapi_app.head("/health")
async def health():
    """Enhanced health check for uptime monitoring"""
    return {
        "status": "healthy",
        "service": "mindmate-bot",
        "instance_id": INSTANCE_ID,
        "mode": "webhook" if USE_WEBHOOK else "polling",
        "uptime": "operational",
        "version": "1.2.0",
        "features": {
            "voice": True,
            "personal_mode": True,
            "crisis_detection": True,
            "webhook": USE_WEBHOOK
        },
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "root": "/"
        }
    }

@fastapi_app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming Telegram webhook updates."""
    if telegram_app is None:
        logger.error("Telegram app not initialized")
        return {"error": "Bot not initialized"}, 500
    
    try:
        update_data = await request.json()
        logger.info(f"Webhook received update: {update_data.get('update_id', 'unknown')}")
        
        update = Update.de_json(update_data, telegram_app.bot)
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

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
    personal_mode = is_personal_mode(user_id)
    logger.info(f"User {user_id} started bot [{'PERSONAL' if personal_mode else 'STANDARD'}]")
    
    if personal_mode:
        await update.message.reply_text(
            "👋 Welcome back!\n\n"
            "🔓 **Personal Mode Active**\n\n"
            "I'm your personal AI therapist - here to give you direct, "
            "honest support without the corporate disclaimers.\n\n"
            "What's on your mind today? 💙"
        )
    else:
        await update.message.reply_text(WELCOME_MESSAGE)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")

async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current mode status."""
    user_id = update.effective_user.id
    personal_mode = is_personal_mode(user_id)
    
    if personal_mode:
        await update.message.reply_text(
            "🔓 **Personal Mode: ACTIVE**\n\n"
            "You have access to:\n"
            "• Direct, honest advice\n"
            "• No AI disclaimers\n"
            "• Personal therapist experience\n"
            "• Softer crisis handling\n\n"
            f"User ID: `{user_id}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🔒 **Standard Mode: ACTIVE**\n\n"
            "You're using the standard MindMate experience.\n\n"
            f"User ID: `{user_id}`",
            parse_mode="Markdown"
        )

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    clear_history(user_id)
    logger.info(f"User {user_id} cleared history")
    await update.message.reply_text("Conversation history cleared. 🧹")

async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /model command for A/B testing."""
    user_id = update.effective_user.id
    args = context.args
    
    # Show current model if no args
    if not args:
        current = get_user_model(user_id)
        models_list = "\n".join([f"• `{k}` → {v}" for k, v in AVAILABLE_MODELS.items()])
        await update.message.reply_text(
            f"🧪 **A/B Testing Mode**\n\n"
            f"**Current model:** `{current}`\n\n"
            f"**Available models:**\n{models_list}\n\n"
            f"**Usage:** `/model 4.1-mini`",
            parse_mode="Markdown"
        )
        return
    
    # Set new model
    model_key = args[0].lower()
    if model_key in AVAILABLE_MODELS:
        new_model = AVAILABLE_MODELS[model_key]
        set_user_model(user_id, new_model)
        clear_history(user_id)  # Clear history when switching models
        logger.info(f"User {user_id} switched to model: {new_model}")
        await update.message.reply_text(
            f"✅ Switched to **{new_model}**\n\n"
            f"History cleared for fresh comparison.\n"
            f"Start chatting to test this model!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Unknown model: `{model_key}`\n\n"
            f"Available: {', '.join(AVAILABLE_MODELS.keys())}",
            parse_mode="Markdown"
        )

async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start human model testing mode."""
    user_id = update.effective_user.id
    
    if is_personal_mode(user_id):
        start_human_test(user_id)
        
        await update.message.reply_text(
            f"🧪 **Human Model Test Started**\n\n"
            f"**How it works:**\n"
            f"1. Send your prompt (text or voice)\n"
            f"2. I'll get responses from all 3 models\n"
            f"3. I'll show you responses one by one\n"
            f"4. Rate each response (1-5 scale)\n"
            f"5. Continue conversation naturally\n\n"
            f"**Commands during test:**\n"
            f"• `/rate 1-5` - Rate current response\n"
            f"• `/done` - Finish test and get report\n"
            f"• `/start` - Exit test mode\n\n"
            f"📝 Send your first prompt to begin!"
        )
        
        # Automatically trigger first test round
        await handle_human_test_message(update, user_id, "🧪 Please send your first test prompt to begin!")
    else:
        await update.message.reply_text(
            "❌ Human testing is only available in Personal Mode.\n"
            "Use `/mode` to check your current mode."
        )

async def cmd_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rate the current response in human test mode or blind test mode."""
    user_id = update.effective_user.id
    args = context.args
    
    if is_human_test_active(user_id):
        await handle_human_rating(update, user_id, args)
        return
    
    # Original blind test rating logic
    if not is_blind_test_active(user_id):
        await update.message.reply_text("❌ No active test. Use `/test` to start.", parse_mode="Markdown")
        return
    
    if user_id not in current_test_mapping or not current_test_mapping[user_id]:
        await update.message.reply_text("❌ No responses to rate yet. Send a test message first!")
        return
    
    if not args:
        await update.message.reply_text(
            "📊 **Rate the responses (1-5):**\n\n"
            "`/rate A:4 B:5 C:3`\n\n"
            "1 = Poor, 5 = Excellent",
            parse_mode="Markdown"
        )
        return
    
    # Parse ratings like "A:4 B:5 C:3"
    ratings = {}
    try:
        for arg in args:
            parts = arg.upper().split(":")
            if len(parts) == 2:
                letter = parts[0]
                score = int(parts[1])
                if letter in ["A", "B", "C"] and 1 <= score <= 5:
                    ratings[letter] = score
    except ValueError:
        pass
    
    if len(ratings) != 3:
        await update.message.reply_text(
            "❌ Please rate all 3 responses.\n\n"
            "Example: `/rate A:4 B:5 C:3`",
            parse_mode="Markdown"
        )
        return
    
    # Save the result
    mapping = current_test_mapping[user_id]
    prompt = mapping.get("_prompt", "Unknown")
    save_test_result(user_id, prompt, mapping, ratings)
    current_test_mapping[user_id] = {}  # Clear for next test
    
    test_count = len(blind_test_results.get(user_id, []))
    await update.message.reply_text(
        f"✅ **Ratings saved!** ({test_count} tests completed)\n\n"
        f"🅰️ = {ratings.get('A')} | 🅱️ = {ratings.get('B')} | 🅲️ = {ratings.get('C')}\n\n"
        f"📝 Send another test message, or `/results` when done.",
        parse_mode="Markdown"
    )

async def handle_human_rating(update: Update, user_id: int, args: list) -> None:
    """Handle human test rating for current response."""
    if "pending_responses" not in human_test_responses[user_id] or not human_test_responses[user_id]["pending_responses"]:
        await update.message.reply_text("❌ No response to rate. Send a message first.")
        return
    
    if not args:
        await update.message.reply_text(
            "📊 **Rate the current response:**\n\n"
            "`/rate 1-5`\n\n"
            "1 = Poor, 3 = Good, 5 = Excellent",
            parse_mode="Markdown"
        )
        return
    
    try:
        rating = int(args[0])
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
    except ValueError:
        await update.message.reply_text(
            "❌ Please provide a valid rating between 1 and 5.\n\n"
            "Example: `/rate 4`",
            parse_mode="Markdown"
        )
        return
    
    # Save rating for current response
    pending = human_test_responses[user_id]["pending_responses"]
    current_idx = human_test_responses[user_id]["current_response_index"]
    current_response = pending[current_idx]
    current_response["rating"] = rating
    
    # Save to overall ratings
    if user_id not in human_test_ratings:
        human_test_ratings[user_id] = []
    
    human_test_ratings[user_id].append({
        "prompt": human_test_responses[user_id]["current_prompt"],
        "model": current_response["model"],
        "response": current_response["response"],
        "rating": rating,
        "timestamp": datetime.now().isoformat()
    })
    
    # Move to next response
    human_test_responses[user_id]["current_response_index"] += 1
    
    await update.message.reply_text(
        f"✅ **Rated {current_response['model']}: {rating}/5**\n\n"
        f"Moving to next response...",
        parse_mode="Markdown"
    )
    
    # Show next response or finish
    await show_next_response_for_rating(update, user_id)

async def cmd_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show blind test results and reveal models."""
    user_id = update.effective_user.id
    
    results = blind_test_results.get(user_id, [])
    if not results:
        await update.message.reply_text("❌ No test results yet. Use `/test` to start testing.")
        return
    
    # Calculate scores per model
    model_scores: dict[str, list[int]] = {m: [] for m in BLIND_TEST_MODELS}
    
    for result in results:
        mapping = result["mapping"]
        ratings = result["ratings"]
        for letter, score in ratings.items():
            model = mapping.get(letter)
            if model and model in model_scores:
                model_scores[model].append(score)
    
    # Calculate averages
    model_averages = {}
    for model, scores in model_scores.items():
        if scores:
            model_averages[model] = sum(scores) / len(scores)
        else:
            model_averages[model] = 0
    
    # Sort by average score
    sorted_models = sorted(model_averages.items(), key=lambda x: x[1], reverse=True)
    
    # Build results message
    results_text = "🏆 **BLIND TEST RESULTS**\n\n"
    results_text += f"**Total tests:** {len(results)}\n\n"
    results_text += "**Rankings:**\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for i, (model, avg) in enumerate(sorted_models):
        medal = medals[i] if i < 3 else "  "
        scores = model_scores[model]
        results_text += f"{medal} **{model}**\n"
        results_text += f"   Avg: {avg:.2f}/5 ({len(scores)} ratings)\n\n"
    
    # Winner recommendation
    winner = sorted_models[0][0] if sorted_models else "Unknown"
    results_text += f"🎯 **Recommended model:** `{winner}`\n\n"
    results_text += "_Test ended. Use `/test` to start a new test._"
    
    # End the test
    stop_blind_test(user_id)
    
    await update.message.reply_text(results_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Deduplicate messages to prevent double responses during deployments
    message_id = update.message.message_id
    if message_id in processed_messages:
        logger.info(f"Skipping duplicate message {message_id}")
        return
    
    # Track this message as processed
    processed_messages.add(message_id)
    # Keep set from growing too large
    if len(processed_messages) > MAX_PROCESSED_MESSAGES:
        # Remove oldest entries (convert to list, slice, convert back)
        to_remove = list(processed_messages)[:MAX_PROCESSED_MESSAGES // 2]
        for msg_id in to_remove:
            processed_messages.discard(msg_id)
    
    user_id = update.effective_user.id
    message = update.message.text
    personal_mode = is_personal_mode(user_id)
    
    # Crisis detection (still active in Personal Mode, but less aggressive)
    if detect_crisis(message):
        logger.warning(f"Crisis detected - user {user_id}")
        if personal_mode:
            # In Personal Mode, still show resources but continue conversation
            await update.message.reply_text(
                "💙 I hear you, and I'm here for you. If you're in immediate danger, "
                "please reach out: SADAG 0800 567 567 (24/7)\n\n"
                "Now, tell me more about what's going on...",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(CRISIS_RESPONSE, parse_mode="Markdown")
            return
    
    if not openai_client:
        await update.message.reply_text("I'm temporarily unavailable. Please try again later.")
        return
    
    # Check if in human test mode
    if is_human_test_active(user_id):
        await handle_human_test_message(update, user_id, message)
        return
    
    # Check if in blind test mode
    if is_blind_test_active(user_id):
        await handle_blind_test_message(update, user_id, message)
        return
    
    # Select system prompt based on mode
    system_prompt = get_personal_mode_prompt(user_id) if personal_mode else SYSTEM_PROMPT
    current_model = get_user_model(user_id)
    
    mode_str = "PERSONAL" if personal_mode else "STANDARD"
    logger.info(f"Message from user {user_id} [{mode_str}] using model {current_model}")
    
    try:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(get_history(user_id))
        messages.append({"role": "user", "content": message})
        
        response = openai_client.chat.completions.create(
            model=current_model,
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

async def handle_human_test_message(update: Update, user_id: int, message: str) -> None:
    """Handle message in human test mode - get responses from all models and show one by one."""
    logger.info(f"Human test message from user {user_id}")
    
    # Check if we have pending responses to rate
    if "pending_responses" in human_test_responses[user_id] and human_test_responses[user_id]["pending_responses"]:
        await update.message.reply_text(
            "⏸️ Please rate the current response first with `/rate 1-5`\n\n"
            f"Current response: {human_test_responses[user_id]['pending_responses'][human_test_responses[user_id]['current_response_index']]['response'][:100]}...",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text("🧪 _Getting responses from all 3 models..._", parse_mode="Markdown")
    
    # Build conversation history for natural flow
    conversation_history = human_test_responses[user_id].get("conversation", [])
    messages = [{"role": "system", "content": get_personal_mode_prompt(user_id)}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})
    
    # Get responses from all models
    responses = {}
    for model in BLIND_TEST_MODELS:
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=150,
                temperature=0.8,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            responses[model] = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting response from {model}: {e}")
            responses[model] = f"Error: {str(e)}"
    
    # Store responses and add to conversation history
    human_test_responses[user_id]["pending_responses"] = [
        {"model": model, "response": response} for model, response in responses.items()
    ]
    human_test_responses[user_id]["current_response_index"] = 0
    human_test_responses[user_id]["current_prompt"] = message
    
    # Add user message to conversation history
    conversation_history.append({"role": "user", "content": message})
    
    # Show first response for rating
    await show_next_response_for_rating(update, user_id)

async def show_next_response_for_rating(update: Update, user_id: int) -> None:
    """Show the next response for rating."""
    pending = human_test_responses[user_id]["pending_responses"]
    current_idx = human_test_responses[user_id]["current_response_index"]
    
    if current_idx >= len(pending):
        # All responses rated, add to conversation and continue
        await update.message.reply_text(
            "✅ All responses rated! Send your next message to continue the conversation.",
            parse_mode="Markdown"
        )
        
        # Add the best-rated response to conversation history
        best_response = max(pending, key=lambda x: x.get("rating", 0))
        conversation_history = human_test_responses[user_id]["conversation"]
        conversation_history.append({"role": "assistant", "content": best_response["response"]})
        
        # Clear pending responses
        human_test_responses[user_id]["pending_responses"] = []
        human_test_responses[user_id]["current_response_index"] = 0
        return
    
    current_response = pending[current_idx]
    model_name = current_response["model"]
    response_text = current_response["response"]
    
    await update.message.reply_text(
        f"🎯 **Response {current_idx + 1}/3**\n\n"
        f"**Model:** {model_name}\n\n"
        f"{response_text}\n\n"
        f"📊 **Rate this response (1-5):**\n"
        f"`/rate 1-5`\n\n"
        f"1 = Poor, 3 = Good, 5 = Excellent",
        parse_mode="Markdown"
    )

async def handle_blind_test_message(update: Update, user_id: int, message: str) -> None:
    logger.info(f"Blind test message from user {user_id}")
    
    await update.message.reply_text("🧪 _Testing 3 models... please wait..._", parse_mode="Markdown")
    
    # Prepare messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]
    
    # Query all 3 models
    responses = {}
    for model in BLIND_TEST_MODELS:
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=600,
                temperature=0.8,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            responses[model] = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error with model {model}: {e}")
            responses[model] = f"[Error: Could not get response from {model}]"
    
    # Shuffle and assign A, B, C randomly
    models = list(BLIND_TEST_MODELS)
    random.shuffle(models)
    
    mapping = {
        "A": models[0],
        "B": models[1],
        "C": models[2],
        "_prompt": message  # Store the prompt too
    }
    current_test_mapping[user_id] = mapping
    
    # Build response with hidden model identities
    test_response = f"📝 **Your prompt:** _{message}_\n\n"
    test_response += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    test_response += f"🅰️ **Response A:**\n{responses[models[0]]}\n\n"
    test_response += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    test_response += f"🅱️ **Response B:**\n{responses[models[1]]}\n\n"
    test_response += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    test_response += f"🅲️ **Response C:**\n{responses[models[2]]}\n\n"
    test_response += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    test_response += "📊 **Rate them:** `/rate A:4 B:5 C:3`\n"
    test_response += "_(1 = Poor, 5 = Excellent)_"
    
    # Split if too long for Telegram (4096 char limit)
    if len(test_response) > 4000:
        # Send in parts
        await update.message.reply_text(f"📝 **Your prompt:** _{message}_\n\n━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
        await update.message.reply_text(f"🅰️ **Response A:**\n{responses[models[0]]}", parse_mode="Markdown")
        await update.message.reply_text(f"🅱️ **Response B:**\n{responses[models[1]]}", parse_mode="Markdown")
        await update.message.reply_text(f"🅲️ **Response C:**\n{responses[models[2]]}", parse_mode="Markdown")
        await update.message.reply_text("📊 **Rate them:** `/rate A:4 B:5 C:3`\n_(1 = Poor, 5 = Excellent)_", parse_mode="Markdown")
    else:
        await update.message.reply_text(test_response, parse_mode="Markdown")
    
    logger.info(f"Blind test responses sent to user {user_id}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages - transcribe and respond with voice."""
    user_id = update.effective_user.id
    personal_mode = is_personal_mode(user_id)
    
    try:
        # Check OpenAI client availability
        if not openai_client:
            logger.error(f"OpenAI client not initialized for user {user_id}")
            await update.message.reply_text(
                "❌ Voice service is temporarily unavailable. Please try again later.",
                parse_mode="Markdown"
            )
            return
        
        # Get voice file
        voice = update.message.voice or update.message.audio
        if not voice:
            await update.message.reply_text("❌ Please send a voice message.")
            return
        
        # Download voice file
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            await voice_file.download_to_drive(temp_file.name)
            
            # Transcribe voice to text
            from openai import AsyncOpenAI
            async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            with open(temp_file.name, "rb") as audio_file:
                transcript = await async_client.audio.transcriptions.create(
                    model=VOICE_TRANSCRIPTION_MODEL,
                    file=audio_file
                )
            
            transcribed_text = transcript.text
            logger.info(f"User {user_id} voice transcribed: {transcribed_text[:50]}...")
            
            # Add detailed logging for debugging
            logger.info(f"OpenAI client status: {openai_client is not None}")
            logger.info(f"Transcription successful: {transcribed_text[:100]}...")
            
            # Add transcription to history
            add_to_history(user_id, "user", transcribed_text)
            
            # Get conversation history
            history = get_history(user_id)
            
            # Generate response
            system_prompt = get_personal_mode_prompt(user_id) if personal_mode else SYSTEM_PROMPT
            current_model = get_user_model(user_id)
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": transcribed_text})
            
            response = openai_client.chat.completions.create(
                model=current_model,
                messages=messages,
                max_tokens=500,
                temperature=0.8,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            logger.info(f"Chat completion successful for user {user_id}")
            
            response_text = response.choices[0].message.content
            logger.info(f"Response text extracted: {response_text[:100]}...")
            
            # Validate response before proceeding
            if not response_text:
                logger.error(f"Empty response from OpenAI for user {user_id}")
                await update.message.reply_text(
                    "❌ I didn't get a proper response. Please try again.",
                    parse_mode="Markdown"
                )
                return
            
            # Add response to history
            add_to_history(user_id, "assistant", response_text)
            
            # Generate voice response
            logger.info(f"About to create TTS for user {user_id}")
            voice_response = openai_client.audio.speech.create(
                model=VOICE_TTS_MODEL,
                input=response_text,
                voice="alloy"
            )
            
            logger.info(f"TTS creation successful for user {user_id}")
            
            # Validate voice response
            if not voice_response:
                logger.error(f"Failed to generate voice response for user {user_id}")
                await update.message.reply_text(
                    f"💬 **Text Response:**\n\n{response_text}",
                    parse_mode="Markdown"
                )
                return
            
            # Create temporary file for TTS response
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as voice_file:
                # Run synchronous stream_to_file in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, voice_response.stream_to_file, voice_file.name)
                
                # Check if response fits in Telegram caption limit (800 chars leaves room for formatting)
                if len(response_text) <= 800:
                    # Normal flow - voice with full caption
                    caption_text = f"🎤 **Voice Response:**\n\n{response_text}"
                    await update.message.reply_voice(
                        voice=voice_file,
                        caption=caption_text,
                        parse_mode="Markdown"
                    )
                else:
                    # Response too long - send voice + split text messages
                    await update.message.reply_voice(
                        voice=voice_file,
                        caption="🎤 **Full response below:**",
                        parse_mode="Markdown"
                    )
                    
                    # Split long text into multiple messages (Telegram limit: 4096 chars)
                    for i in range(0, len(response_text), 4096):
                        await update.message.reply_text(response_text[i:i+4096])
            
            logger.info(f"Voice response sent to user {user_id}")
            
    except OpenAIError as e:
        logger.error(f"OpenAI error processing voice for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Voice processing failed. Please try again.",
            parse_mode="Markdown"
        )
        return

async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Continue to next prompt in human test mode."""
    user_id = update.effective_user.id
    
    if not is_human_test_active(user_id):
        await update.message.reply_text("❌ No active test. Use `/test` to start.")
        return
    
    # Check if we have pending responses to rate
    if "pending_responses" in human_test_responses[user_id] and human_test_responses[user_id]["pending_responses"]:
        await update.message.reply_text(
            "⏸️ Please rate the current response first with `/rate 1-5`",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(
        "📝 Please send your next prompt to continue the test.",
        parse_mode="Markdown"
    )

async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Finish human test early and generate markdown report."""
    user_id = update.effective_user.id
    
    if not is_human_test_active(user_id):
        await update.message.reply_text("❌ No active test. Use `/test` to start.")
        return
    
    await finish_human_test(update, user_id)

async def finish_human_test(update: Update, user_id: int) -> None:
    """Finish human test and generate markdown report."""
    ratings = human_test_ratings.get(user_id, [])
    
    if not ratings:
        await update.message.reply_text("❌ No ratings collected. Test incomplete.")
        stop_human_test(user_id)
        return
    
    # Calculate final results
    model_scores = {model: [] for model in BLIND_TEST_MODELS}
    for rating_data in ratings:
        model = rating_data["model"]
        score = rating_data["rating"]
        model_scores[model].append(score)
    
    # Calculate averages
    final_results = {}
    for model, scores in model_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            final_results[model] = {
                "average": round(avg_score, 2),
                "count": len(scores),
                "scores": scores
            }
    
    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"research/HUMAN_TELEGRAM_TEST_{timestamp}.json"
    
    results_data = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "models_tested": MODELS,
            "total_tests": len(ratings),
            "test_type": "human_telegram_rated_test",
            "rating_method": "telegram_human_rating_1_to_5_scale"
        },
        "individual_ratings": ratings,
        "final_results": final_results
    }
    
    with open(json_filename, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    # Create markdown report
    markdown_filename = f"research/HUMAN_TEST_REPORT_{timestamp}.md"
    create_markdown_report(markdown_filename, ratings, final_results, json_filename)
    
    # Display final rankings
    sorted_models = sorted(final_results.items(), key=lambda x: x[1]["average"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    
    results_text = "🏆 **HUMAN TEST RESULTS**\n\n"
    results_text += f"**Total tests:** {len(ratings)}\n"
    results_text += f"**JSON saved to:** `{json_filename}`\n"
    results_text += f"**Markdown report:** `{markdown_filename}`\n\n"
    results_text += "**Rankings:**\n"
    
    for i, (model, data) in enumerate(sorted_models):
        medal = medals[i] if i < 3 else "  "
        avg = data["average"]
        count = data["count"]
        results_text += f"{medal} **{model}**\n"
        results_text += f"   Avg: {avg}/5 ({count} ratings)\n\n"
    
    winner = sorted_models[0][0] if sorted_models else "Unknown"
    results_text += f"🎯 **Recommended model:** `{winner}`\n\n"
    results_text += "✅ Test completed! Check the markdown report for detailed analysis."
    
    await update.message.reply_text(results_text, parse_mode="Markdown")
    
    # Stop test
    stop_human_test(user_id)

def create_markdown_report(filename: str, ratings: list, final_results: dict, json_filename: str) -> None:
    """Create a detailed markdown report for human test analysis."""
    with open(filename, 'w') as f:
        f.write("# 🧪 Human Model Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Total Ratings:** {len(ratings)}\n")
        f.write(f"**Models Tested:** {', '.join(MODELS)}\n")
        f.write(f"**Rating Method:** Human subjective rating (1-5 scale)\n")
        f.write(f"**JSON Data:** `{json_filename}`\n\n")
        
        f.write("## 🏆 Final Rankings\n\n")
        sorted_models = sorted(final_results.items(), key=lambda x: x[1]["average"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (model, data) in enumerate(sorted_models):
            medal = medals[i] if i < 3 else "  "
            avg = data["average"]
            count = data["count"]
            scores = data["scores"]
            
            f.write(f"{medal} **{model}**\n")
            f.write(f"- **Average:** {avg}/5.0\n")
            f.write(f"- **Total Ratings:** {count}\n")
            f.write(f"- **Individual Scores:** {', '.join(map(str, scores))}\n")
            f.write(f"- **Performance:** {'Excellent' if avg >= 4.5 else 'Good' if avg >= 3.5 else 'Fair' if avg >= 2.5 else 'Poor'}\n\n")
        
        f.write("## 📊 Detailed Ratings\n\n")
        
        # Group by prompt for analysis
        prompt_groups = {}
        for rating in ratings:
            prompt = rating["prompt"]
            if prompt not in prompt_groups:
                prompt_groups[prompt] = []
            prompt_groups[prompt].append(rating)
        
        for i, (prompt, group_ratings) in enumerate(prompt_groups.items(), 1):
            f.write(f"### Test {i}: {prompt[:50]}...\n\n")
            
            for rating in group_ratings:
                model = rating["model"]
                response = rating["response"]
                score = rating["rating"]
                timestamp = rating["timestamp"]
                
                f.write(f"#### {model} (Rated: {score}/5)\n")
                f.write(f"> {response}\n\n")
                f.write(f"**Rating:** {score}/5 | **Time:** {timestamp[:19]}\n\n")
        
        f.write("---\n")
        f.write("## 🎯 Recommendations\n\n")
        
        winner = sorted_models[0][0] if sorted_models else "Unknown"
        winner_avg = final_results[winner]["average"]
        
        f.write(f"**Best Model:** `{winner}` (Average: {winner_avg}/5)\n\n")
        
        if winner_avg >= 4.5:
            f.write("This model shows **excellent performance** for your therapy needs. ")
            f.write("Recommended for immediate deployment.\n\n")
        elif winner_avg >= 3.5:
            f.write("This model shows **good performance** for your therapy needs. ")
            f.write("Consider deploying with monitoring.\n\n")
        else:
            f.write("This model shows **moderate performance**. ")
            f.write("Consider testing additional models or refining prompts.\n\n")
        
        f.write("### Next Steps\n\n")
        f.write("1. Update your bot's `DEFAULT_MODEL` setting\n")
        f.write("2. Deploy changes to production\n")
        f.write("3. Monitor real-world performance\n")
        f.write("4. Consider periodic re-testing\n\n")
        
        f.write("---\n")
        f.write("*Generated by MindMate Human Test System*\n")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Bot error: {context.error}")
# =============================================================================
# Main
# =============================================================================

def main():
    logger.info("=" * 50)
    logger.info("Starting MindMate Bot with FastAPI")
    logger.info("=" * 50)
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    if not OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY not set")
    
    # Run FastAPI with Uvicorn
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()
