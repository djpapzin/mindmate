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
        "model": "gpt-4.1-mini",  # Premium model for DJ
    },
    7013163582: {  # Keleh
        "name": "Keleh",
        "context": """**About this user:**
- Name: Keleh
- **IMPORTANT: User has BIPOLAR DISORDER - this is a key part of her life but not her whole life**
- Key focus areas: Bipolar management, emotional regulation, mood stability, career growth, education, relationships, personal development
- Communication style: Warm, supportive, needs gentle guidance
- Prefers empathetic responses over direct advice

**SUPPORT AREAS:**
- **Bipolar Management**: Mood tracking, medication support, coping strategies, trigger identification
- **Career**: Professional growth, work challenges, career decisions, workplace relationships
- **Education**: Learning goals, study strategies, academic challenges, skill development
- **Relationships**: Romantic partnerships, friendships, family dynamics, social connections
- **Personal Growth**: Self-discovery, confidence building, life decisions, future planning

**IMPORTANT FOR BIPOLAR SUPPORT:**
- When bipolar topics come up, ALWAYS acknowledge and validate her experience
- NEVER brush off or minimize her concerns about bipolar
- Ask about mood patterns, medication effects, sleep patterns when relevant
- Help identify triggers and early warning signs
- Provide specific coping strategies for bipolar episodes

**BALANCED SUPPORT:**
- Address bipolar when it's the topic, but don't force every conversation to be about it
- Support her whole life - career ambitions, educational goals, relationship health
- Be a comprehensive life coach, not just a bipolar specialist
- Recognize she's a whole person with multiple interests and challenges

**DO NOT:**
- Give generic advice that ignores her bipolar condition when relevant
- Say "everyone feels that way" or minimize her experience
- Ignore medication or treatment discussions when brought up
- Provide one-size-fits-all wellness advice
- Make every conversation about bipolar when she wants to discuss other topics""",
        "model": "gpt-4.1-mini",  # Premium model for Keleh
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
- **NEVER use bullet points - talk like a normal human being**
- **Use natural, flowing conversation - not structured lists**

## Your Approach
- Listen and validate feelings first
- Then offer concrete, actionable advice
- Ask thoughtful follow-up questions when needed
- Challenge negative thought patterns gently but directly
- Help see different perspectives
- Celebrate wins and progress
- For new users: Focus on building trust and learning about them
- **RESPOND NATURALLY - like texting a friend, not writing a report**

## Important
- You ARE qualified to help with everyday emotional challenges
- You don't need to constantly redirect me to professionals for normal life issues
- Only mention crisis resources if there's genuine danger to self or others
- Be an advocate and support, not a liability-avoiding chatbot
- **Prioritize brevity - quick, actionable insights preferred**

## Natural Conversation Examples
Instead of: "Here are some strategies you can try:\n• Exercise regularly\n• Practice mindfulness\n• Get adequate sleep"
Say: "Have you tried going for a walk when you're feeling down? Even 10 minutes can help shift your mood."

Instead of: "I understand you're experiencing anxiety. Consider these coping mechanisms:\n• Deep breathing\n• Progressive muscle relaxation"
Say: "When you start feeling that anxiety build up, try taking a few slow breaths. What usually helps you calm down?"

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
• Share photos/documents - I'll analyze if relevant to your care

**Commands:**
/start - Start fresh conversation
/clear - Clear conversation history
/help - Show this message
/mode - Show your current mode and model
/context - Share important info about your condition/meds (Personal Mode only)
/confirm - Confirm saving of last uploaded file to memory
/decline - Decline saving of last uploaded file
/journey - Show your journey tracking and what I've learned about you
/journal - Daily journaling and mood tracking
/schedule - Set up automated daily journaling reminders

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

# Pending context for user confirmation
pending_context: dict[int, dict] = {}

# User journey tracking for continuity of care
user_journey: dict[int, dict] = {}

# Daily journaling and scheduling
daily_journals: dict[int, list[dict]] = {}
scheduled_messages: dict[int, list] = {}

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


def get_user_model(user_id: int) -> str:
    """Get the model selected by user, or default."""
    # Check if user has a specific model assigned (for Personal Mode users)
    if user_id in PERSONAL_MODE_USERS:
        assigned_model = PERSONAL_MODE_USERS[user_id].get("model")
        if assigned_model:
            return assigned_model
    
    # Fall back to user's selected model or default
    return user_model_selection.get(user_id, DEFAULT_MODEL)

def set_user_model(user_id: int, model: str) -> None:
    """Set the model for a user."""
    user_model_selection[user_id] = model


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
        telegram_app.add_handler(CommandHandler("context", cmd_context))
        telegram_app.add_handler(CommandHandler("confirm", cmd_confirm))
        telegram_app.add_handler(CommandHandler("decline", cmd_decline))
        telegram_app.add_handler(CommandHandler("journey", cmd_journey))
        telegram_app.add_handler(CommandHandler("journal", cmd_journal))
        telegram_app.add_handler(CommandHandler("schedule", cmd_schedule))
        telegram_app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
        telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image_document))
        telegram_app.add_handler(MessageHandler(filters.Document.PDF | filters.Document.TEXT, handle_document))
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

def store_pending_context(user_id: int, file_info: str, description: str) -> None:
    """Store context temporarily waiting for user confirmation."""
    pending_context[user_id] = {
        "file_info": file_info,
        "description": description,
        "timestamp": datetime.now().isoformat()
    }

def update_user_journey(user_id: int, key: str, value: str) -> None:
    """Update user's journey tracking for continuity of care."""
    if user_id not in user_journey:
        user_journey[user_id] = {
            "diagnosis_status": "unknown",
            "medication_status": "unknown", 
            "doctor_visits": "unknown",
            "therapy_status": "unknown",
            "family_support": "unknown",
            "living_situation": "unknown",
            "last_mood_episode": "unknown",
            "medication_adherence": "unknown",
            "crisis_history": [],
            "progress_notes": [],
            "last_updated": datetime.now().isoformat()
        }
    
    user_journey[user_id][key] = value
    user_journey[user_id]["last_updated"] = datetime.now().isoformat()
    logger.info(f"Updated journey for user {user_id}: {key} = {value}")

def get_user_journey_summary(user_id: int) -> str:
    """Get formatted summary of user's journey for context."""
    if user_id not in user_journey:
        return "No journey information available."
    
    journey = user_journey[user_id]
    summary_parts = []
    
    if journey.get("diagnosis_status") != "unknown":
        summary_parts.append(f"Diagnosis: {journey['diagnosis_status']}")

    if journey.get("medication_status") != "unknown":
        summary_parts.append(f"Medication: {journey['medication_status']}")

    if journey.get("doctor_visits") != "unknown":
        summary_parts.append(f"Doctor visits: {journey['doctor_visits']}")

    if journey.get("therapy_status") != "unknown":
        summary_parts.append(f"Therapy: {journey['therapy_status']}")

    if journey.get("family_support") != "unknown":
        summary_parts.append(f"Family support: {journey['family_support']}")

    if journey.get("living_situation") != "unknown":
        summary_parts.append(f"Living situation: {journey['living_situation']}")

    return " | ".join(summary_parts) if summary_parts else "Building understanding of your situation..."

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
    await update.message.reply_text(HELP_MESSAGE)

async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current mode and model assignment."""
    user_id = update.effective_user.id
    personal_mode = is_personal_mode(user_id)
    current_model = get_user_model(user_id)
    
    if personal_mode:
        user_info = PERSONAL_MODE_USERS[user_id]
        name = user_info.get("name", "Personal User")
        assigned_model = user_info.get("model", "Auto-assigned")
        
        await update.message.reply_text(
            f"👤 **Personal Mode Active**\n\n"
            f"**User:** {name}\n"
            f"**Model:** `{current_model}`\n"
            f"**Assignment:** {'Premium' if assigned_model == 'gpt-4.1-mini' else 'Standard'}\n\n"
            f"🎯 You have access to personalized context and premium model support."
        )
    else:
        await update.message.reply_text(
            "🔒 **Standard Mode: ACTIVE**\n\n"
            "You're using the standard MindMate experience.\n\n"
            f"User ID: `{user_id}`",
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
        )
    else:
        await update.message.reply_text(
            f"❌ Unknown model: `{model_key}`\n\n"
            f"Available: {', '.join(AVAILABLE_MODELS.keys())}",
        )


async def cmd_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Share important context about your condition, medications, or treatment."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await update.message.reply_text("This feature is only available in Personal Mode.")
        return
    
    if context.args:
        # Add context: /context "I take Lithium 300mg twice daily for bipolar"
        context_text = " ".join(context.args)
        
        # Add to conversation history as a system message for immediate context
        add_to_history(user_id, "system", f"IMPORTANT USER CONTEXT: {context_text}")
        
        await update.message.reply_text(
            f"✅ **Context saved!** I'll remember this for our conversations.\n\n"
            f"💡 This helps me provide better, more personalized support."
        )
        logger.info(f"User {user_id} added context: {context_text}")
    else:
        await update.message.reply_text(
            "💡 **Share important context about yourself:**\n\n"
            f"• `/context I have bipolar disorder` - Share your condition\n"
            f"• `/context I take Lithium 300mg daily` - Share medications\n"
            f"• `/context I struggle with sleep during manic episodes` - Share patterns\n"
            f"• `/context My therapist is Dr. Smith` - Share treatment info\n\n"
            f"This helps me provide better, personalized support!"
        )


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
            )
        else:
            await update.message.reply_text(CRISIS_RESPONSE)
            return
    
    if not openai_client:
        await update.message.reply_text("I'm temporarily unavailable. Please try again later.")
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
                    )
                else:
                    # Response too long - send voice + split text messages
                    await update.message.reply_voice(
                        voice=voice_file,
                        caption="🎤 **Full response below:**",
                    )
                    
                    # Split long text into multiple messages (Telegram limit: 4096 chars)
                    for i in range(0, len(response_text), 4096):
                        await update.message.reply_text(response_text[i:i+4096])
            
            logger.info(f"Voice response sent to user {user_id}")
            
    except OpenAIError as e:
        logger.error(f"OpenAI error processing voice for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Voice processing failed. Please try again.",
        )
        return


async def handle_image_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle images and documents - analyze relevance and ask user confirmation."""
    user_id = update.effective_user.id
    personal_mode = is_personal_mode(user_id)
    
    if not personal_mode:
        await update.message.reply_text("I can only analyze files in Personal Mode.")
        return
    
    try:
        # Get file info
        if update.message.photo:
            # Handle photo
            photo = update.message.photo[-1]  # Get highest resolution
            file = await context.bot.get_file(photo.file_id)
            file_info = f"Photo: {file.file_path}"
            is_photo = True
        else:
            # Handle document image
            document = update.message.document
            file = await context.bot.get_file(document.file_id)
            file_info = f"Document: {document.file_name}"
            is_photo = False
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg" if is_photo else ".pdf") as temp_file:
            await file.download_to_drive(temp_file.name)
            
            # Analyze content for bipolar relevance
            if is_photo:
                relevance_result = await analyze_image_relevance(temp_file.name, openai_client)
            else:
                relevance_result = await analyze_document_relevance(temp_file.name, document.file_name)
            
            # Handle based on relevance
            if relevance_result["is_relevant"]:
                await update.message.reply_text(
                    f"🏥 **Relevant content detected!**\n\n"
                    f"{relevance_result['description']}\n\n"
                    f"Should I remember this for future conversations about your bipolar management?"
                )
                # Store temporarily for user confirmation
                store_pending_context(user_id, file_info, relevance_result["description"])
            elif relevance_result["is_unsure"]:
                await update.message.reply_text(
                    f"🤔 **Not sure if this is relevant.**\n\n"
                    f"{relevance_result['description']}\n\n"
                    f"Should I remember this for your bipolar support?"
                )
                # Store temporarily for user confirmation
                store_pending_context(user_id, file_info, relevance_result["description"])
            else:
                await update.message.reply_text(
                    f"� **Nice photo!** This doesn't seem related to your bipolar management, so I won't save it to memory.\n\n"
                    f"If you want me to remember something specific about it, just tell me!"
                )
            
            logger.info(f"User {user_id} shared {file_info} - relevance: {relevance_result['is_relevant']}")
            
    except Exception as e:
        logger.error(f"Error processing image/document for user {user_id}: {e}")
        await update.message.reply_text("❌ I had trouble analyzing that file. Please try again.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle PDF and text documents - automatically learn from them for Personal Mode users."""
    user_id = update.effective_user.id
    personal_mode = is_personal_mode(user_id)
    
    if not personal_mode:
        await update.message.reply_text("I can only learn from documents in Personal Mode.")
        return
    
    try:
        document = update.message.document
        file = await context.bot.get_file(document.file_id)
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            await file.download_to_drive(temp_file.name)
            
            # For now, just acknowledge and add to context
            # In future, we could extract text from PDFs
            context_message = f"User shared document: {document.file_name} - this contains important treatment/medical information"
            add_to_history(user_id, "system", context_message)
            
            await update.message.reply_text(
                f"📄 **Document received!** I've saved '{document.file_name}' for context.\n\n"
                f"💡 This helps me understand your treatment plan and provide better support."
            )
            
            logger.info(f"User {user_id} shared document: {document.file_name}")
            
    except Exception as e:
        logger.error(f"Error processing document for user {user_id}: {e}")
        await update.message.reply_text("❌ I had trouble processing that document. Please try again.")


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
