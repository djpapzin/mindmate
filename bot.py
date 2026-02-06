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

# =============================================================================
# Personal Mode Configuration
# =============================================================================

# Users who have access to Personal Mode (no guardrails, direct advice)
PERSONAL_MODE_USERS = [
    339651126,  # djpapzin
]

def is_personal_mode(user_id: int) -> bool:
    """Check if user has Personal Mode enabled."""
    return user_id in PERSONAL_MODE_USERS

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

## Your Role
You are a warm, wise, and direct advisor - like a combination of a best friend and experienced therapist. You speak to me as someone who truly knows me and cares about my wellbeing.

## How You Communicate
- Be direct and genuine - no corporate disclaimers or "As an AI..." statements
- Give real advice and opinions, not just questions back at me
- Be warm but also honest - tell me what I need to hear, not just what I want to hear
- Use casual, conversational language like a trusted friend would
- Remember our conversation context and reference it naturally

## What You Help Me With
- Relationships and dating
- Financial stress and money management
- Mood management and emotional regulation
- Work/career challenges
- Building better habits
- Processing difficult emotions
- Making decisions

## Your Approach
- Listen and validate my feelings first
- Then offer concrete, actionable advice
- Ask thoughtful follow-up questions when needed
- Challenge my negative thought patterns gently but directly
- Help me see different perspectives
- Celebrate my wins and progress

## Important
- You ARE qualified to help me with everyday emotional challenges
- You don't need to constantly redirect me to professionals for normal life issues
- Only mention crisis resources if I express genuine danger to myself or others
- Be my advocate and support, not a liability-avoiding chatbot

Remember: I chose you as my personal therapist. Be that for me."""

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

# Blind test models (the 3 we're comparing)
BLIND_TEST_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5.2"]

# Blind test state
import random
blind_test_active: dict[int, bool] = {}
blind_test_results: dict[int, list[dict]] = {}  # Store test results per user
current_test_mapping: dict[int, dict[str, str]] = {}  # Maps A/B/C to actual models

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
    
def stop_blind_test(user_id: int) -> None:
    """Stop blind test for user."""
    blind_test_active[user_id] = False

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
    personal_mode = is_personal_mode(user_id)
    logger.info(f"User {user_id} started bot [{'PERSONAL' if personal_mode else 'STANDARD'}]")
    clear_history(user_id)
    
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

async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start blind A/B/C testing mode."""
    user_id = update.effective_user.id
    
    if is_blind_test_active(user_id):
        await update.message.reply_text(
            "🧪 **Blind test already active!**\n\n"
            "Send a message to test, or:\n"
            "• `/rate A:4 B:5 C:3` - Rate responses\n"
            "• `/results` - End test & see results",
            parse_mode="Markdown"
        )
        return
    
    start_blind_test(user_id)
    await update.message.reply_text(
        "🧪 **Blind A/B/C Test Started!**\n\n"
        "**How it works:**\n"
        "1️⃣ Send any message/prompt\n"
        "2️⃣ You'll get 3 responses: 🅰️ 🅱️ 🅲️\n"
        "3️⃣ Rate them: `/rate A:4 B:5 C:3`\n"
        "4️⃣ Repeat 10-20 times\n"
        "5️⃣ `/results` to reveal models & scores\n\n"
        "**Models are hidden** - you won't know which is which until the end!\n\n"
        "📝 **Send your first test message now!**",
        parse_mode="Markdown"
    )

async def cmd_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Rate the responses from blind test."""
    user_id = update.effective_user.id
    
    if not is_blind_test_active(user_id):
        await update.message.reply_text("❌ No active test. Use `/test` to start.", parse_mode="Markdown")
        return
    
    if user_id not in current_test_mapping or not current_test_mapping[user_id]:
        await update.message.reply_text("❌ No responses to rate yet. Send a test message first!")
        return
    
    args = context.args
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
    
    # Check if in blind test mode
    if is_blind_test_active(user_id):
        await handle_blind_test_message(update, user_id, message)
        return
    
    # Select system prompt based on mode
    system_prompt = PERSONAL_MODE_PROMPT if personal_mode else SYSTEM_PROMPT
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

async def handle_blind_test_message(update: Update, user_id: int, message: str) -> None:
    """Handle message in blind test mode - query all 3 models."""
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
    app.add_handler(CommandHandler("mode", cmd_mode))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CommandHandler("rate", cmd_rate))
    app.add_handler(CommandHandler("results", cmd_results))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    logger.info("Initializing bot...")
    await app.initialize()
    await app.start()
    # drop_pending_updates=True clears any stuck updates and prevents conflicts
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
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
