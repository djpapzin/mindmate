"""
MindMate - AI Mental Wellness Telegram Bot
A compassionate chatbot providing 24/7 mental wellness support.
"""

import asyncio
import html
import json
import logging
import os
import re
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from openai import OpenAI, OpenAIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn

# Brave web search helper (optional, opt-in via explicit trigger)
from web_search import build_web_attribution_line, search_web
from verse_of_the_day import get_verse_of_the_day

# Import the active storage module: PostgreSQL with an in-memory fallback.
from postgres_db import Message, PostgresDatabase
from postgres_db import InMemoryDatabase as PostgresInMemoryDatabase

DB_AVAILABLE = "postgres"

# Unique instance ID to help debug multiple instances
INSTANCE_ID = str(uuid.uuid4())[:8]

# =============================================================================
# Helper Functions
# =============================================================================

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2 format."""
    # Characters that need to be escaped in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def _render_basic_telegram_html(text: str) -> str:
    """Render the small markdown subset used by MindMate into safe Telegram HTML."""
    escaped = html.escape(text)

    # Handle the formatting we actually use in bot copy.
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped, flags=re.DOTALL)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*(?!\*)([^*\n]+?)\*(?!\*)", r"<i>\1</i>", escaped)

    return escaped


async def send_markdown_message(update: Update, text: str):
    """Send a message using Telegram HTML after safely rendering simple markdown."""
    html_text = _render_basic_telegram_html(text)
    return await update.message.reply_text(html_text, parse_mode='HTML')

# =============================================================================
# Configuration
# =============================================================================

# Load env from this project only (avoid global OpenClaw .env)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
PORT = int(os.getenv("PORT", 10000))
MAX_HISTORY_LENGTH = 10
AUTO_WEB_SEARCH_ENABLED = os.getenv("AUTO_WEB_SEARCH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
DAILY_HEARTBEAT_ENABLED = os.getenv("DAILY_HEARTBEAT_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
DAILY_HEARTBEAT_HOUR = int(os.getenv("DAILY_HEARTBEAT_HOUR", "7"))
DAILY_HEARTBEAT_WINDOW_MINUTES = max(1, int(os.getenv("DAILY_HEARTBEAT_WINDOW_MINUTES", "15")))
DAILY_HEARTBEAT_POLL_SECONDS = max(30, int(os.getenv("DAILY_HEARTBEAT_POLL_SECONDS", "60")))
DAILY_HEARTBEAT_TIMEZONE = os.getenv("DAILY_HEARTBEAT_TIMEZONE", "Africa/Johannesburg").strip() or "Africa/Johannesburg"
DAILY_HEARTBEAT_CHAT_ID = os.getenv("DAILY_HEARTBEAT_CHAT_ID", "").strip()
DAILY_HEARTBEAT_MESSAGE_THREAD_ID = os.getenv("DAILY_HEARTBEAT_MESSAGE_THREAD_ID", "").strip()
DAILY_HEARTBEAT_ALLOWED_USER_IDS = {
    int(token.strip())
    for token in os.getenv("DAILY_HEARTBEAT_ALLOWED_USER_IDS", "").split(",")
    if token.strip().isdigit()
}

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
        "model": "gpt-5.4-mini",  # Premium model for DJ
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
        "model": "gpt-5.4-mini",  # Premium model for Keleh
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
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Standard system prompt (for regular users)
BASE_SAFETY_RULES = """You are MindMate, an AI mental wellness companion.

## Safety Boundaries
- You are supportive, reflective, and practical, but you are not a licensed therapist, doctor, psychiatrist, or emergency service.
- Never diagnose, prescribe, provide medical instructions, or claim clinical authority.
- Do not create dependency, exclusivity, or manipulative intimacy. Never imply you are the user's only safe person, soulmate, or replacement for human relationships.
- If the user is in crisis or at risk of harming themself or others, keep the response grounded, calm, and safety-oriented. Crisis routing stays deterministic in application logic, so do not improvise around it.
- Be honest about uncertainty. If current information is unavailable, say so plainly instead of sounding more certain than you are.
"""

STANDARD_PERSONA_TRAITS = """## Core Persona
- Warm, steady, emotionally literate, and non-judgmental.
- More like a thoughtful wellness companion than a formal coach.
- Practical over preachy; human over robotic.
- Use emojis sparingly.
"""

PERSONAL_MODE_PERSONA_TEMPLATE = """## Core Persona
- Warm, wise, direct, and emotionally attuned.
- Sound like a trusted grounded confidant, not a corporate assistant.
- Be honest without being harsh, and caring without becoming over-intimate.
- Offer clear opinions and practical perspective when it helps.

## User Context
{user_context}
"""

CHAT_RESPONSE_MODE_RULES = """## Response Mode
- Prioritize emotional presence, insight, and one useful next step when needed.
- Default to short natural replies. Usually 2 short paragraphs or fewer unless the user clearly wants depth.
- Use plain conversational language, not report-writing.
- Ask a follow-up only when it meaningfully helps; it is not required in every reply.
- When advice is helpful, give it directly instead of hiding behind endless reflection.
"""

VOICE_RESPONSE_MODE_RULES = """## Voice Response Mode
- Keep voice replies easy to listen to: compact, warm, and natural.
- Aim for roughly 2-5 spoken sentences unless the user asks for detail.
- Prefer smooth spoken phrasing over dense wording or structured lists.
- End cleanly; don't tack on an unnecessary question every time.
"""

HEARTBEAT_RESPONSE_MODE_RULES = """## Daily Check-in Voice
- This is a light morning companion check-in, not a therapy session.
- Sound breezy, grounded, and encouraging.
- Keep it brief and low-pressure.
- Focus on one gentle reflection and one realistic nudge for today.
- Do not sound like the main chat persona doing a mini counseling session.
"""

ANTI_TEMPLATE_RULES = """## Anti-Template Rules
- Do not follow a rigid 'summary + validate + question' template.
- Vary openings and sentence rhythm so replies feel alive, not canned.
- Not every response needs explicit validation language such as 'that sounds hard' or 'I hear you'. Use it when it fits, skip it when it doesn't.
- Not every response should end with a question. Sometimes end with a grounded observation, encouragement, or a concrete suggestion.
- Avoid stacking multiple reflective phrases that repeat the user's point in slightly different words.
- Avoid bulleted lists unless the user explicitly asks for options, steps, or comparison.
"""

WEB_ROUTING_RULES = """## Web Routing
- When the user asks for current, changing, or location-specific factual information relevant to health or practical support — for example current medical guidance, live public-health/news updates, or nearby services/resources — prefer fresh web context when it is available.
- For emotional support, journaling, reflection, relationship processing, or everyday coping conversations, do not force web lookup behavior; stay present and conversational instead.
"""

SYSTEM_PROMPT = "\n\n".join([
    BASE_SAFETY_RULES,
    STANDARD_PERSONA_TRAITS,
    CHAT_RESPONSE_MODE_RULES,
    ANTI_TEMPLATE_RULES,
    WEB_ROUTING_RULES,
])

PERSONAL_MODE_PROMPT = """You are MindMate in personal mode.

## User Snapshot
- Name: DJ / Papzin
- Location: South Africa
- Key focus areas:
  * Relationships
  * Finances
  * Bipolar management
  * Emotional intelligence
- Communication style: prefers direct, honest feedback over sugar-coating
- Treat the user as a collaborator when that naturally fits.
"""


def _clean_prompt_block(block: str | None) -> str | None:
    if not block:
        return None
    cleaned = block.strip()
    return cleaned or None


def build_identity_prompt(*layers: str | None) -> str:
    """Combine prompt layers into one clean system prompt."""
    return "\n\n".join(block for block in (_clean_prompt_block(layer) for layer in layers) if block)



def get_personal_mode_prompt(user_id: int) -> str:
    """Get Personal Mode prompt with user-specific context."""
    user_context = get_user_context(user_id)
    if not user_context:
        user_context = PERSONAL_MODE_PROMPT

    return build_identity_prompt(
        BASE_SAFETY_RULES,
        PERSONAL_MODE_PERSONA_TEMPLATE.format(user_context=user_context),
        CHAT_RESPONSE_MODE_RULES,
        ANTI_TEMPLATE_RULES,
        WEB_ROUTING_RULES,
        "## Personal Mode Guidance\n- You can be more direct and tailored than standard mode, but keep the same safety boundaries.\n- Support everyday emotional challenges with practical reflection and grounded suggestions.\n- Only mention crisis resources when the app's crisis path has already surfaced that need.",
    )



def build_generation_system_prompt(
    user_id: int,
    *,
    personal_mode: bool,
    response_mode: str = 'chat',
    current_time: str | None = None,
    web_results: str | None = None,
) -> str:
    """Build the layered system prompt for chat/voice generation."""
    identity_prompt = get_personal_mode_prompt(user_id) if personal_mode else SYSTEM_PROMPT

    response_mode_layer = CHAT_RESPONSE_MODE_RULES
    if response_mode == 'voice':
        response_mode_layer = VOICE_RESPONSE_MODE_RULES
    elif response_mode == 'heartbeat':
        response_mode_layer = HEARTBEAT_RESPONSE_MODE_RULES

    prompt = build_identity_prompt(identity_prompt, response_mode_layer)

    if current_time:
        prompt = build_identity_prompt(prompt, f"Current time: {current_time}")

    prompt = build_identity_prompt(
        prompt,
        "Routing reminder: Prefer live web-backed context for current, changing, or location-specific factual questions about health resources, medical/public-health updates, news, weather, or nearby services when that context is available. Do not force web behavior for journaling, emotional support, or reflective conversation unless the user is clearly asking for live facts.",
    )

    if web_results:
        prompt = build_identity_prompt(
            prompt,
            "You also have fresh web search results fetched for the user's query. Use them as factual, time-sensitive context, but still reason carefully.",
            web_results,
        )

    return prompt



def build_daily_summary_ack_prompt(user_id: int) -> str:
    """Prompt for lightweight acknowledgment after a daily heartbeat reply."""
    return build_identity_prompt(
        BASE_SAFETY_RULES,
        STANDARD_PERSONA_TRAITS,
        HEARTBEAT_RESPONSE_MODE_RULES,
        ANTI_TEMPLATE_RULES,
        "## Daily Summary Reply Guidance\n- Thank the user for checking in.\n- Sound warm and lightly encouraging, not clinical or heavy.\n- Mention one grounded takeaway or next step if it fits.\n- Keep it brief and avoid turning this into a long therapy-style response.\n- Do not end with a question unless the user's message clearly asks for help right now.",
    )

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
/votd - Get today's Bible verse
/context - Share important info about your condition/meds (Personal Mode only)
/remember - Remember important information easier than /context
/forget - Forget specific information I've learned
/confirm - Confirm saving of last uploaded file to memory
/decline - Decline saving of last uploaded file
/journey - Show your journey tracking and what I've learned about you
/journal - Daily journaling and mood tracking
/schedule - Manage your daily 07:00 SAST direct check-ins
/feedback - Share a quick note about what helped or felt off

**Live web lookup (explicit only):**
Use `web: your question here`
Example: `web: latest bipolar treatment guidelines`

Remember: I'm here to support, not replace professional help. 💙"""

# =============================================================================
# Global State
# =============================================================================

# Active database manager: PostgreSQL in normal operation.
db_manager: PostgresDatabase = None

# In-memory fallback used only when PostgreSQL is unavailable at startup or runtime.
conversation_history: dict[int, list[dict[str, str]]] = {}
user_model_selection: dict[int, str] = {}  # Track model per user for A/B testing
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
bot_running = False
degraded_mode_notice_sent: set[int] = set()

# Message deduplication to prevent double responses during deployments
processed_messages: set[int] = set()
MAX_PROCESSED_MESSAGES = 1000  # Keep last 1000 message IDs

# Pending file/context confirmation state for uploaded items
pending_context: dict[int, dict] = {}

# User journey tracking for continuity of care
user_journey: dict[int, dict] = {}

# Daily journaling and scheduling
daily_journals: dict[int, dict[str, list[dict]]] = {}
scheduled_messages: dict[int, list] = {}
daily_summary_tracking: dict[int, dict] = {}  # Track scheduled message context

DEFAULT_USER_JOURNEY = {
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
}

# Available models for A/B testing
AVAILABLE_MODELS = {
    "5.4-mini": "gpt-5.4-mini",
    "4o-mini": "gpt-4o-mini",
    "4.1-mini": "gpt-4.1-mini",
    "4.1": "gpt-4.1",
    "5-mini": "gpt-5-mini",
    "5.2": "gpt-5.2",
    "3.5": "gpt-3.5-turbo",
}
DEFAULT_MODEL = "gpt-5.4-mini"

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


def build_chat_completion_kwargs(model: str, messages: list[dict], max_output_tokens: int) -> dict:
    """Build chat completion kwargs with GPT-5-family compatibility.

    GPT-5-family chat models are stricter about accepted parameters, so keep
    their payload minimal and only switch token field compatibility there.
    Older chat models preserve the existing sampling/penalty behavior.
    """
    kwargs = {
        "model": model,
        "messages": messages,
    }

    if model.startswith("gpt-5"):
        kwargs["max_completion_tokens"] = max_output_tokens
    else:
        kwargs.update({
            "max_tokens": max_output_tokens,
            "temperature": 0.8,
            "presence_penalty": 0.6,
            "frequency_penalty": 0.3,
        })

    return kwargs


def build_chat_recovery_message(error: Exception, used_web: bool = False) -> str:
    """Return a user-friendly fallback message for chat model failures."""
    status_code = getattr(error, "status_code", None)
    error_name = error.__class__.__name__.lower()

    if status_code == 429 or "ratelimit" in error_name or "rate_limit" in error_name:
        message = (
            "💙 I'm getting more requests than usual right now, so my reply engine needs a moment. "
            "Please try again in about a minute."
        )
    elif status_code and status_code >= 500:
        message = (
            "💙 My reply engine hit a temporary server problem just now. "
            "Please try again in a moment."
        )
    elif "timeout" in error_name:
        message = (
            "💙 My reply took too long to come back just now. "
            "Please try again, or send the key part in a shorter message."
        )
    elif "connection" in error_name or "apierror" in error_name:
        message = (
            "💙 I lost connection to my reply engine for a moment. "
            "Please try again shortly."
        )
    else:
        message = (
            "💙 I hit a temporary problem while preparing that reply. "
            "Please try again."
        )

    if used_web:
        message += " If needed, resend it without `web:` and I'll answer without live web lookup."
    else:
        message += " If it keeps happening, resend the main part in one shorter message."

    message += " You can also use /feedback to flag it for review."
    return message


def format_votd_message(verse_text: str, reference: str, version: str | None = None, link: str | None = None) -> str:
    """Render a clean, mobile-friendly Verse of the Day message."""
    version_suffix = f" ({version})" if version else ""
    return (
        "📖 **Today's Verse**\n\n"
        f'“{verse_text}”\n\n'
        f"— **{reference}**{version_suffix}"
    )


async def send_votd_unavailable(update: Update) -> None:
    """Keep /votd responsive when the verse source is temporarily unavailable."""
    await send_markdown_message(
        update,
        "📖 I couldn't fetch today's verse right now. Please try `/votd` again in a little bit."
    )


def is_degraded_memory_mode() -> bool:
    """Return True when the bot is using non-persistent fallback storage."""
    return isinstance(db_manager, PostgresInMemoryDatabase)


async def maybe_send_degraded_mode_notice(update: Update, user_id: int) -> None:
    """Let the user know when long-term memory is temporarily degraded."""
    if user_id in degraded_mode_notice_sent or not is_degraded_memory_mode() or not update.message:
        return

    degraded_mode_notice_sent.add(user_id)
    await update.message.reply_text(
        "🟡 Quick heads-up: I'm still here for the conversation, but my long-term memory is in a lighter mode right now.\n\n"
        "I may not reliably remember this chat after a restart, so repeat anything important later or use /feedback if you want to flag something for review."
    )


def get_daily_heartbeat_timezone() -> ZoneInfo:
    """Return the configured timezone for scheduled daily check-ins."""
    try:
        return ZoneInfo(DAILY_HEARTBEAT_TIMEZONE)
    except Exception:
        logger.warning("Invalid DAILY_HEARTBEAT_TIMEZONE=%s; falling back to UTC", DAILY_HEARTBEAT_TIMEZONE)
        return ZoneInfo("UTC")


async def is_daily_heartbeat_enabled_for_user(user_id: int) -> bool:
    """Return True when a user is eligible and has not opted out of the daily heartbeat."""
    rollout_allows_user = (
        user_id in PERSONAL_MODE_USERS
        and (not DAILY_HEARTBEAT_ALLOWED_USER_IDS or user_id in DAILY_HEARTBEAT_ALLOWED_USER_IDS)
    )
    if not rollout_allows_user:
        return False
    if not db_manager or not hasattr(db_manager, "get_user_preference"):
        return False
    enabled = await db_manager.get_user_preference(user_id, "daily_heartbeat_enabled")
    if enabled is None:
        return True
    return bool(enabled)


async def set_daily_heartbeat_enabled_for_user(user_id: int, enabled: bool) -> None:
    """Persist the user's daily heartbeat opt-in state."""
    if db_manager and hasattr(db_manager, "store_user_preference"):
        await db_manager.store_user_preference(user_id, "daily_heartbeat_enabled", enabled)


def can_force_test_daily_heartbeat(user_id: int) -> bool:
    """Return True when this user may manually trigger a live heartbeat test."""
    return DAILY_HEARTBEAT_ENABLED and user_id in PERSONAL_MODE_USERS and (
        not DAILY_HEARTBEAT_ALLOWED_USER_IDS or user_id in DAILY_HEARTBEAT_ALLOWED_USER_IDS
    )


async def get_daily_heartbeat_last_sent_date(user_id: int) -> str | None:
    """Return the last local-date string this user received a scheduled check-in."""
    if not db_manager or not hasattr(db_manager, "get_user_preference"):
        return None
    value = await db_manager.get_user_preference(user_id, "daily_heartbeat_last_sent_date")
    return value if isinstance(value, str) else None


async def mark_daily_heartbeat_sent(user_id: int, local_date: str) -> None:
    """Persist the local date when the scheduled check-in was sent."""
    if db_manager and hasattr(db_manager, "store_user_preference"):
        await db_manager.store_user_preference(user_id, "daily_heartbeat_last_sent_date", local_date)


async def get_daily_heartbeat_candidate_user_ids() -> list[int]:
    """Return eligible known users unless they have explicitly opted out."""
    if not DAILY_HEARTBEAT_ENABLED or not db_manager or not hasattr(db_manager, "get_known_user_ids"):
        return []

    candidate_user_ids = await db_manager.get_known_user_ids()
    eligible_user_ids: list[int] = []
    for user_id in candidate_user_ids:
        if await is_daily_heartbeat_enabled_for_user(user_id):
            eligible_user_ids.append(user_id)
    return eligible_user_ids


HEARTBEAT_SUPPORT_KEYWORDS = {
    "anxious", "anxiety", "burnout", "calm", "coping", "crash", "crying", "depressed", "depression",
    "drained", "emotion", "emotional", "energy", "episode", "exhausted", "family", "fatigue",
    "feel", "feeling", "feelings", "friend", "grief", "journal", "lonely", "manic", "medication",
    "medicine", "meds", "mood", "overwhelmed", "panic", "partner", "relationship", "rest", "sad",
    "sleep", "stressed", "stress", "support", "therapy", "therapist", "tired", "trigger", "work"
}
HEARTBEAT_HIGH_PRIORITY_KEYWORDS = {
    "journal", "journaling", "mood", "stress", "stressed", "sleep", "tired", "rest", "overwhelmed",
    "anxious", "anxiety", "panic", "depressed", "depression", "manic", "episode", "therapy",
    "therapist", "meds", "medication", "medicine", "relationship", "partner", "family", "friend",
    "lonely", "grief", "crying", "support", "coping", "trigger"
}
HEARTBEAT_CURRENT_EVENTS_PATTERNS = (
    re.compile(r"\b(?:news|current events?|headlines?|latest|update|updates|happening|happened)\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s| is)?\s+(?:exactly\s+)?(?:happening|going on|the update)\b", re.IGNORECASE),
    re.compile(r"\b(?:there|in [a-z][a-z\s'-]{1,40})\s+(?:lately|right now|today|this week)\b", re.IGNORECASE),
)
HEARTBEAT_LOW_VALUE_PATTERNS = (
    re.compile(r"^/[a-z0-9_]+(?:\s|$)", re.IGNORECASE),
    re.compile(r"^(?:search|browse|look up|lookup|google|find)(?:\s+the)?\s+web\b", re.IGNORECASE),
    re.compile(r"^(?:search|browse|look up|lookup|google|find)\b", re.IGNORECASE),
    re.compile(r"\b(?:search|look up|lookup|google|find)\b.{0,30}\b(?:price|weather|news|score|stock|bitcoin|btc|crypto)\b", re.IGNORECASE),
    re.compile(r"\b(?:bitcoin|btc|crypto|stock|forex|weather|news|score)s?\b", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
)
HEARTBEAT_COMMAND_TERMS = {
    "search", "browse", "google", "lookup", "look", "find", "price", "prices", "weather", "news", "score", "scores",
    "bitcoin", "btc", "crypto", "stock", "stocks", "forex", "translate", "summarize", "web"
}


def _normalize_heartbeat_context_text(value: str) -> str:
    return " ".join((value or "").split()).strip()


def _is_current_events_heartbeat_message(message: str) -> bool:
    normalized = _normalize_heartbeat_context_text(message)
    if not normalized:
        return False

    lower = normalized.lower()
    if any(pattern.search(lower) for pattern in HEARTBEAT_CURRENT_EVENTS_PATTERNS):
        return True

    tokens = set(re.findall(r"[a-z']+", lower))
    return bool({"news", "headline", "headlines", "update", "updates", "latest", "happening", "happened"} & tokens)



def _is_low_value_heartbeat_message(message: str) -> bool:
    normalized = _normalize_heartbeat_context_text(message)
    if not normalized:
        return True
    lower = normalized.lower()
    if len(lower) < 8:
        return True
    if any(pattern.search(lower) for pattern in HEARTBEAT_LOW_VALUE_PATTERNS):
        return True
    tokens = re.findall(r"[a-z']+", lower)
    if tokens and len(tokens) <= 6 and sum(token in HEARTBEAT_COMMAND_TERMS for token in tokens) >= max(2, len(tokens) // 2):
        return True
    return False



def _score_heartbeat_context_message(message: str) -> int:
    normalized = _normalize_heartbeat_context_text(message)
    if not normalized:
        return -100

    lower = normalized.lower()
    tokens = set(re.findall(r"[a-z']+", lower))
    score = 0

    if _is_low_value_heartbeat_message(normalized):
        score -= 6

    if _is_current_events_heartbeat_message(normalized):
        score -= 8

    support_hits = sum(token in HEARTBEAT_SUPPORT_KEYWORDS for token in tokens)
    score += min(6, support_hits * 2)

    priority_hits = sum(token in HEARTBEAT_HIGH_PRIORITY_KEYWORDS for token in tokens)
    score += min(8, priority_hits * 2)

    if any(phrase in lower for phrase in ("i feel", "i'm feeling", "ive been", "i've been", "yesterday", "recently")):
        score += 2
    if any(phrase in lower for phrase in ("my mood", "my sleep", "my therapist", "my meds", "my medication", "my partner", "my relationship", "my journal")):
        score += 3
    if len(tokens) >= 8:
        score += 1
    if any(token in tokens for token in {"bipolar", "therapy", "therapist", "meds", "medication", "anxiety", "depressed", "overwhelmed", "panic", "sleep", "relationship", "partner"}):
        score += 2

    return score



def _select_heartbeat_context_messages(messages: list[str], limit: int = 3) -> list[str]:
    support_candidates: list[tuple[int, int, str]] = []
    general_candidates: list[tuple[int, int, str]] = []
    fallback_messages: list[str] = []
    current_event_fallback_messages: list[str] = []

    for index, raw_message in enumerate(messages):
        normalized = _normalize_heartbeat_context_text(raw_message)
        if not normalized:
            continue

        score = _score_heartbeat_context_message(normalized)
        is_current_events = _is_current_events_heartbeat_message(normalized)
        has_high_priority_support = any(
            token in HEARTBEAT_HIGH_PRIORITY_KEYWORDS for token in re.findall(r"[a-z']+", normalized.lower())
        )

        if score > 0:
            if has_high_priority_support and not is_current_events:
                support_candidates.append((score, index, normalized))
            elif not is_current_events:
                general_candidates.append((score, index, normalized))
            else:
                current_event_fallback_messages.append(normalized)
        elif not _is_low_value_heartbeat_message(normalized):
            if is_current_events:
                current_event_fallback_messages.append(normalized)
            else:
                fallback_messages.append(normalized)

    def _dedupe_ranked(items: list[tuple[int, int, str]]) -> list[str]:
        ranked = sorted(items, key=lambda item: (item[0], item[1]), reverse=True)
        selected: list[str] = []
        seen: set[str] = set()
        for _, _, message in ranked:
            if message in seen:
                continue
            seen.add(message)
            selected.append(message)
            if len(selected) >= limit:
                break
        return selected

    if support_candidates:
        return _dedupe_ranked(support_candidates)

    if general_candidates:
        return _dedupe_ranked(general_candidates)

    deduped_fallback: list[str] = []
    seen_fallback: set[str] = set()
    for message in reversed(fallback_messages):
        if message in seen_fallback:
            continue
        seen_fallback.add(message)
        deduped_fallback.append(message)
        if len(deduped_fallback) >= limit:
            break

    if deduped_fallback:
        return deduped_fallback

    deduped_current_events: list[str] = []
    seen_current_events: set[str] = set()
    for message in reversed(current_event_fallback_messages):
        if message in seen_current_events:
            continue
        seen_current_events.add(message)
        deduped_current_events.append(message)
        if len(deduped_current_events) >= limit:
            break

    # Do not force vague current-events phrasing into a personal morning check-in.
    # If we only found low-value current-events style context, it's better to omit
    # the "Recently, you've been carrying this" line entirely.
    return []


async def build_daily_heartbeat_message(user_id: int, now: datetime | None = None, verse = None) -> str:
    """Build a lightweight morning companion briefing from recent context."""
    tz = get_daily_heartbeat_timezone()
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    yesterday = (local_now - timedelta(days=1)).strftime("%Y-%m-%d")
    recent_history = await get_history(user_id)
    journal_entries = await get_journal_entries_for_date(user_id, yesterday)
    journey = await ensure_user_journey_loaded(user_id)

    intro = "🌤️ Morning. Tiny check-in before the day runs away with you."

    yesterday_line = None
    if journal_entries:
        latest_entry = (journal_entries[-1].get("entry") or "").strip()
        if latest_entry:
            compact_entry = " ".join(latest_entry.split())
            if len(compact_entry) > 180:
                compact_entry = compact_entry[:177].rstrip() + "..."
            yesterday_line = f"🪞 From yesterday: \"{compact_entry}\""

    recent_user_messages = [
        (item.get("content") or "").strip()
        for item in recent_history
        if item.get("role") == "user" and (item.get("content") or "").strip()
    ]
    relevant_user_messages = _select_heartbeat_context_messages(recent_user_messages, limit=3)

    if not yesterday_line and relevant_user_messages:
        last_user_message = relevant_user_messages[0]
        if len(last_user_message) > 180:
            last_user_message = last_user_message[:177].rstrip() + "..."
        yesterday_line = f"🪞 Lately it's sounded like: \"{last_user_message}\""

    plan_suggestions: list[str] = []
    combined_context = " ".join(
        [
            " ".join((entry.get("entry") or "") for entry in journal_entries),
            " ".join(relevant_user_messages),
            " ".join(str(value) for value in journey.values() if isinstance(value, str)),
        ]
    ).lower()

    if any(token in combined_context for token in ["tired", "sleep", "exhausted", "rest"]):
        plan_suggestions.append("protect your energy early today and keep your first task light")
    if any(token in combined_context for token in ["anxious", "stress", "overwhelmed", "panic"]):
        plan_suggestions.append("keep today small: one clear priority, slower breathing, fewer tabs open")
    if any(token in combined_context for token in ["work", "job", "career", "boss", "deadline"]):
        plan_suggestions.append("pick the single work task that would make today feel less heavy")
    if any(token in combined_context for token in ["medication", "medicine", "meds", "dose"]):
        plan_suggestions.append("stay steady with the basics that support you, including your normal meds routine if that's part of your day")
    if any(token in combined_context for token in ["relationship", "partner", "friend", "family", "mom", "dad"]):
        plan_suggestions.append("aim for one calm, honest check-in instead of carrying everything silently")

    if not plan_suggestions:
        plan_suggestions.extend([
            "choose one thing to protect your peace this morning",
            "pick one realistic win for today instead of chasing ten things at once",
        ])

    suggestions_text = "; then maybe ".join(plan_suggestions[:2])
    plan_line = f"🎯 Gentle nudge: {suggestions_text}."
    reflection_line = None
    if verse:
        verse_themes = []
        verse_text_lower = (verse.text or "").lower()
        if any(token in verse_text_lower for token in ["trust", "strength", "victory", "help", "fear", "peace", "rest"]):
            verse_themes.append("today doesn't have to be carried by pressure alone")
        if any(token in combined_context for token in ["stress", "overwhelmed", "anxious", "panic"]):
            verse_themes.append("it fits the way your mind has been carrying a lot lately")
        if any(token in combined_context for token in ["family", "relationship", "partner", "friend"]):
            verse_themes.append("it also lands in the middle of the relationship weight you've been holding")
        if any(token in combined_context for token in ["work", "job", "career"]):
            verse_themes.append("it speaks into the pressure to force outcomes by yourself")
        if not verse_themes:
            verse_themes.append("it feels like a quiet reminder that you don't have to grip the whole day so tightly")

        reflection_line = "🫶 The verse feels relevant today because " + "; ".join(verse_themes[:2]) + "."

    reply_line = "💬 If you want, send a quick mood check, a sentence about yesterday, or the one thing that feels heaviest today."

    lines = [intro]
    if yesterday_line:
        lines.append(yesterday_line)
    if reflection_line:
        lines.append(reflection_line)
    lines.append(plan_line)
    lines.append(reply_line)
    return "\n\n".join(lines)


async def run_daily_heartbeat_cycle(now: datetime | None = None) -> int:
    """Send one scheduled daily check-in per eligible user per local day."""
    if not DAILY_HEARTBEAT_ENABLED or not telegram_app or not telegram_app.bot:
        return 0

    tz = get_daily_heartbeat_timezone()
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    if local_now.hour != DAILY_HEARTBEAT_HOUR or local_now.minute >= DAILY_HEARTBEAT_WINDOW_MINUTES:
        return 0

    sent_count = 0
    local_date = local_now.strftime("%Y-%m-%d")
    for user_id in await get_daily_heartbeat_candidate_user_ids():
        pending_tracking = await get_latest_pending_daily_summary_tracking(user_id)
        if pending_tracking and pending_tracking.get("waiting_for_summary"):
            continue
        if await get_daily_heartbeat_last_sent_date(user_id) == local_date:
            continue
        try:
            await send_scheduled_daily_summary(user_id)
            pending_tracking = await get_latest_pending_daily_summary_tracking(user_id)
            if pending_tracking and pending_tracking.get("waiting_for_summary"):
                await mark_daily_heartbeat_sent(user_id, local_date)
                sent_count += 1
        except Exception as e:
            logger.error("Daily heartbeat send failed for user %s: %s", user_id, e)
    return sent_count


async def daily_heartbeat_scheduler_loop() -> None:
    """Background scheduler for the once-daily MindMate heartbeat MVP."""
    logger.info(
        "Daily heartbeat scheduler active: enabled=%s hour=%s tz=%s window=%sm allowlist=%s",
        DAILY_HEARTBEAT_ENABLED,
        DAILY_HEARTBEAT_HOUR,
        DAILY_HEARTBEAT_TIMEZONE,
        DAILY_HEARTBEAT_WINDOW_MINUTES,
        sorted(DAILY_HEARTBEAT_ALLOWED_USER_IDS) if DAILY_HEARTBEAT_ALLOWED_USER_IDS else "all-opted-in-users",
    )
    while True:
        try:
            sent_count = await run_daily_heartbeat_cycle()
            if sent_count:
                logger.info("Daily heartbeat scheduler sent %s check-in(s)", sent_count)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Daily heartbeat scheduler loop error: %s", e)
        await asyncio.sleep(DAILY_HEARTBEAT_POLL_SECONDS)


# =============================================================================
# FastAPI App
# =============================================================================

# Global reference to the telegram application
telegram_app: Application = None
daily_heartbeat_task: asyncio.Task | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI."""
    global telegram_app, db_manager, daily_heartbeat_task
    
    # Startup: Initialize PostgreSQL database first
    logger.info(f"[{INSTANCE_ID}] Initializing PostgreSQL database...")
    
    db_url = os.environ.get('NEON_MINDMATE_DB_URL') or os.environ.get('DATABASE_URL')
    
    try:
        db_manager = PostgresDatabase(db_url, openai_client)
        await db_manager.connect()
        logger.info(f"[{INSTANCE_ID}] ✅ PostgreSQL database connected successfully!")
    except Exception as e:
        logger.error(f"[{INSTANCE_ID}] ❌ Failed to connect to PostgreSQL: {e}")
        logger.info(f"[{INSTANCE_ID}] 🔄 Will use in-memory fallback storage")
        db_manager = PostgresInMemoryDatabase()
        await db_manager.connect()
    
    # Initialize and start the Telegram bot
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
            BotCommand("mode", "🔓 Switch to Personal Mode"),
            BotCommand("clear", "🧹 Clear history"),
            BotCommand("votd", "📖 Get today's Bible verse"),
            BotCommand("model", "🧪 Switch AI model"),
            BotCommand("schedule", "⏰ Manage daily check-ins"),
            BotCommand("feedback", "📝 Share quick feedback"),
        ]
        
        async def set_commands():
            await telegram_app.bot.set_my_commands(commands)
        
        # Set bot commands for better UX
        await set_commands()
        
        # Register handlers
        telegram_app.add_handler(CommandHandler("start", cmd_start))
        telegram_app.add_handler(CommandHandler("help", cmd_help))
        telegram_app.add_handler(CommandHandler("chatid", cmd_chatid))
        telegram_app.add_handler(CommandHandler("clear", cmd_clear))
        telegram_app.add_handler(CommandHandler("mode", cmd_mode))
        telegram_app.add_handler(CommandHandler("votd", cmd_votd))
        telegram_app.add_handler(CommandHandler("model", cmd_model))
        telegram_app.add_handler(CommandHandler("feedback", cmd_feedback))
        telegram_app.add_handler(CommandHandler("context", cmd_context))
        telegram_app.add_handler(CommandHandler("remember", cmd_remember))
        telegram_app.add_handler(CommandHandler("forget", cmd_forget))
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

        if DAILY_HEARTBEAT_ENABLED:
            daily_heartbeat_task = asyncio.create_task(daily_heartbeat_scheduler_loop(), name="mindmate-daily-heartbeat")
            logger.info(f"[{INSTANCE_ID}] ✅ Daily heartbeat scheduler started")
        else:
            logger.info(f"[{INSTANCE_ID}] Daily heartbeat scheduler disabled via env")
        
        logger.info(f"[{INSTANCE_ID}] ✅ Bot is running!")
    
    yield  # App is running
    
    if daily_heartbeat_task:
        daily_heartbeat_task.cancel()
        try:
            await daily_heartbeat_task
        except asyncio.CancelledError:
            pass
        daily_heartbeat_task = None
    
    # Shutdown: Close database and stop the bot
    if db_manager:
        logger.info(f"[{INSTANCE_ID}] Closing database connection...")
        await db_manager.close()
    
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

async def get_history(user_id: int) -> list[dict[str, str]]:
    """Get conversation history for a user from PostgreSQL or fallback memory."""
    if db_manager:
        try:
            return await db_manager.get_conversation_history(user_id, MAX_HISTORY_LENGTH)
        except Exception as e:
            logger.warning(f"Failed to get history from PostgreSQL: {e}")
    
    # Fallback to in-memory storage
    return conversation_history.get(user_id, [])

def store_pending_context(user_id: int, file_info: str, description: str) -> None:
    """Store context temporarily waiting for user confirmation."""
    pending_context[user_id] = {
        "file_info": file_info,
        "description": description,
        "timestamp": datetime.now().isoformat()
    }


def _default_user_journey() -> dict:
    journey = dict(DEFAULT_USER_JOURNEY)
    journey["crisis_history"] = list(DEFAULT_USER_JOURNEY["crisis_history"])
    journey["progress_notes"] = list(DEFAULT_USER_JOURNEY["progress_notes"])
    journey["last_updated"] = datetime.now().isoformat()
    return journey


async def ensure_user_journey_loaded(user_id: int) -> dict:
    """Load the durable journey snapshot into memory when available."""
    if user_id in user_journey:
        return user_journey[user_id]

    journey = _default_user_journey()
    if db_manager and hasattr(db_manager, "get_user_journey"):
        try:
            stored = await db_manager.get_user_journey(user_id)
            if isinstance(stored, dict) and stored:
                journey.update(stored)
        except Exception as e:
            logger.warning(f"Failed to load journey from durable storage for user {user_id}: {e}")
    user_journey[user_id] = journey
    return journey


async def persist_user_journey(user_id: int) -> None:
    if not db_manager or not hasattr(db_manager, "save_user_journey"):
        return
    try:
        await db_manager.save_user_journey(user_id, user_journey.get(user_id, _default_user_journey()))
    except Exception as e:
        logger.warning(f"Failed to persist journey for user {user_id}: {e}")


async def update_user_journey(user_id: int, key: str, value: str) -> None:
    """Update user's journey tracking for continuity of care."""
    journey = await ensure_user_journey_loaded(user_id)
    journey[key] = value
    journey["last_updated"] = datetime.now().isoformat()
    logger.info(f"Updated journey for user {user_id}: {key} = {value}")
    await persist_user_journey(user_id)

async def get_user_journey_summary(user_id: int) -> str:
    """Get formatted summary of user's journey for context."""
    journey = await ensure_user_journey_loaded(user_id)
    if not journey:
        return "No journey information available."

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


async def get_journal_entries_for_date(user_id: int, local_date: str) -> list[dict]:
    """Load durable journal entries for a local date, with in-memory fallback."""
    if db_manager and hasattr(db_manager, "get_journal_entries"):
        try:
            entries = await db_manager.get_journal_entries(user_id, local_date=local_date)
            daily_journals.setdefault(user_id, {})[local_date] = list(entries)
            return list(entries)
        except Exception as e:
            logger.warning(f"Failed to load journal entries for user {user_id} on {local_date}: {e}")
    return list(daily_journals.get(user_id, {}).get(local_date, []))


def _entry_source_message_id(entry: dict | None) -> str | None:
    metadata = (entry or {}).get("metadata") or {}
    source_message_id = metadata.get("source_message_id")
    return str(source_message_id) if source_message_id is not None else None


async def get_existing_journal_entry_for_source_message(
    user_id: int,
    source_message_id: int | str | None,
    *,
    local_date: str | None = None,
    entry_type: str | None = None,
) -> dict | None:
    """Return an existing journal entry tied to a source message id, if any."""
    if source_message_id is None:
        return None

    source_message_id_str = str(source_message_id)
    if db_manager and hasattr(db_manager, "get_journal_entry_by_source_message"):
        try:
            existing = await db_manager.get_journal_entry_by_source_message(
                user_id=user_id,
                source_message_id=source_message_id_str,
                local_date=local_date,
                entry_type=entry_type,
            )
            if existing:
                return existing
        except Exception as e:
            logger.warning(
                f"Failed to look up journal dedupe key for user {user_id} message {source_message_id_str}: {e}"
            )

    candidate_dates = [local_date] if local_date else list(daily_journals.get(user_id, {}).keys())
    for candidate_date in candidate_dates:
        for existing in daily_journals.get(user_id, {}).get(candidate_date, []):
            if _entry_source_message_id(existing) == source_message_id_str:
                if entry_type and existing.get("type") != entry_type:
                    continue
                return dict(existing)
    return None


async def append_journal_entry_for_user(
    user_id: int,
    local_date: str,
    entry_text: str,
    entry_type: str = "journal",
    mood: str | None = None,
    plan_tomorrow: str | None = None,
    metadata: dict | None = None,
    source_message_id: int | str | None = None,
) -> tuple[dict, bool]:
    """Append a journal entry and persist it when durable storage is available."""
    entry_metadata = dict(metadata or {})
    if source_message_id is not None:
        entry_metadata["source_message_id"] = str(source_message_id)

    existing_entry = await get_existing_journal_entry_for_source_message(
        user_id,
        source_message_id,
        local_date=local_date,
        entry_type=entry_type,
    )
    if existing_entry:
        cache = daily_journals.setdefault(user_id, {}).setdefault(local_date, [])
        if not any(_entry_source_message_id(item) == _entry_source_message_id(existing_entry) for item in cache):
            cache.append(existing_entry)
        return existing_entry, False

    entry = {
        "timestamp": datetime.now().isoformat(),
        "entry": entry_text,
        "type": entry_type,
        "mood": mood,
        "plan_tomorrow": plan_tomorrow,
    }
    if entry_metadata:
        entry["metadata"] = entry_metadata

    if db_manager and hasattr(db_manager, "append_journal_entry"):
        try:
            entry = await db_manager.append_journal_entry(
                user_id=user_id,
                local_date=local_date,
                entry_text=entry_text,
                entry_type=entry_type,
                mood=mood,
                plan_tomorrow=plan_tomorrow,
                metadata=entry_metadata,
            )
        except Exception as e:
            logger.warning(f"Failed to persist journal entry for user {user_id}: {e}")

    cache = daily_journals.setdefault(user_id, {}).setdefault(local_date, [])
    if source_message_id is None or not any(_entry_source_message_id(item) == str(source_message_id) for item in cache):
        cache.append(entry)
    return entry, True


async def get_latest_pending_daily_summary_tracking(user_id: int) -> dict | None:
    """Load the latest pending daily-summary tracking state, including after restart."""
    cached = daily_summary_tracking.get(user_id)
    if cached and cached.get("waiting_for_summary"):
        return cached

    if db_manager and hasattr(db_manager, "get_latest_pending_daily_checkin"):
        try:
            tracked = await db_manager.get_latest_pending_daily_checkin(user_id)
            if tracked:
                daily_summary_tracking[user_id] = tracked
                return tracked
        except Exception as e:
            logger.warning(f"Failed to load pending daily summary tracking for user {user_id}: {e}")
    return cached


async def set_daily_summary_tracking(
    user_id: int,
    local_date: str,
    waiting_for_summary: bool,
    *,
    sent_at: datetime | None = None,
    responded_at: datetime | None = None,
    prompt_message_id: int | str | None = None,
    response_message_id: int | str | None = None,
    prompt_kind: str = "daily_heartbeat",
    status: str | None = None,
    metadata: dict | None = None,
) -> dict:
    tracking = {
        "local_date": local_date,
        "waiting_for_summary": waiting_for_summary,
        "sent_time": sent_at.isoformat() if sent_at else None,
        "responded_at": responded_at.isoformat() if responded_at else None,
        "message_id": str(prompt_message_id) if prompt_message_id is not None else None,
        "response_message_id": str(response_message_id) if response_message_id is not None else None,
        "kind": prompt_kind,
        "status": status or ("completed" if responded_at else "sent" if waiting_for_summary else "dismissed"),
    }
    if metadata:
        tracking["metadata"] = metadata

    if db_manager and hasattr(db_manager, "upsert_daily_checkin"):
        try:
            persisted = await db_manager.upsert_daily_checkin(
                user_id=user_id,
                local_date=local_date,
                waiting_for_summary=waiting_for_summary,
                sent_at=sent_at,
                responded_at=responded_at,
                prompt_message_id=prompt_message_id,
                response_message_id=response_message_id,
                prompt_kind=prompt_kind,
                status=status,
                metadata=metadata,
            )
            tracking.update(persisted)
        except Exception as e:
            logger.warning(f"Failed to persist daily check-in tracking for user {user_id}: {e}")

    daily_summary_tracking[user_id] = tracking
    return tracking


async def add_to_history(user_id: int, role: str, content: str) -> None:
    """Add a message to PostgreSQL, with in-memory fallback if needed."""
    if db_manager:
        try:
            # Create message object for PostgreSQL storage
            message = Message(
                user_id=user_id,
                content=content,
                role=role,
                timestamp=datetime.now(),
                message_id=f"{user_id}_{datetime.now().timestamp()}"
            )
            await db_manager.store_message(message)
            return
        except Exception as e:
            logger.warning(f"Failed to store message in PostgreSQL: {e}")
    
    # Fallback to in-memory storage
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": role, "content": content})
    if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY_LENGTH:]

async def clear_history(user_id: int) -> None:
    """Clear conversation history from PostgreSQL, with in-memory fallback if needed."""
    if db_manager:
        try:
            await db_manager.clear_conversation(user_id)
            return
        except Exception as e:
            logger.warning(f"Failed to clear history in PostgreSQL: {e}")
    
    # Fallback to in-memory storage
    conversation_history.pop(user_id, None)

# =============================================================================
# Crisis Detection
# =============================================================================

def detect_crisis(message: str) -> bool:
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CRISIS_KEYWORDS)


WEB_TEMPORAL_SIGNALS = (
    "today", "tonight", "tomorrow", "now", "right now", "current", "currently",
    "latest", "recent", "recently", "live", "this week", "this month", "this year",
    "as of", "update", "updates", "headline", "headlines", "lately",
)
WEB_LIVE_TOPICS = (
    "weather", "forecast", "temperature", "rain", "news", "price", "stock", "market",
    "bitcoin", "btc", "ethereum", "eth", "gold", "oil", "exchange rate", "zar", "usd",
    "score", "scores", "match", "game", "traffic", "load shedding", "power outage",
)
WEB_HEALTH_TOPICS = (
    "symptom", "symptoms", "medication", "medicine", "meds", "dose", "dosage",
    "side effect", "side effects", "interaction", "interactions", "treatment",
    "therapy", "therapist", "psychiatrist", "clinic", "hospital", "pharmacy",
    "helpline", "hotline", "flu", "covid", "virus", "outbreak", "vaccine",
)
WEB_LOCATION_TOPICS = (
    "near me", "nearby", "closest", "open now", "in my area", "local",
    "where can i", "where do i", "which hospital", "which clinic", "which pharmacy",
)
WEB_CURRENT_EVENT_TOPICS = (
    "war", "conflict", "ceasefire", "strike", "missile", "attack", "attacks",
    "election", "protest", "sanction", "sanctions", "summit", "crime", "violence",
)
WEB_UPDATE_INTENTS = (
    "latest on", "update on", "updates on", "news on", "what's the update",
    "whats the update", "what is the update", "what's happening", "whats happening",
    "what is happening", "what happened", "any update on", "any updates on",
)
WEB_QUESTION_STARTERS = (
    "what", "what's", "whats", "how", "is", "are", "will", "did", "can", "when",
)
EXPLICIT_WEB_SEARCH_RE = re.compile(
    r"^(?:hey\s+mindmate[,!]?\s+)?(?:can you|could you|would you|please|pls|kindly)?\s*"
    r"(?:search (?:the )?web|search online|check online|check the internet|look (?:it|this|that) up)\b"
    r"(?:\s+(?:for|about|on))?[\s:,-]*(.*)$",
    re.IGNORECASE,
)
FOLLOW_UP_REFERENCE_TERMS = ("there", "that", "it", "this", "they", "those", "these")
FOLLOW_UP_TIME_TERMS = ("lately", "right now", "currently", "latest", "recently", "today", "now", "still")
FOLLOW_UP_PERSONAL_TERMS = (
    " i ", " i'm ", " ive ", " i've ", " me ", " my ", " myself ", " we ", " our ",
    "feel", "feeling", "anxious", "sad", "depressed", "relationship", "therapy",
)


def _normalize_for_web_routing(message: str) -> str:
    return (message or "").strip().lower().replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")


def _looks_like_live_or_current_query(message: str) -> bool:
    stripped = (message or "").strip()
    if not stripped or len(stripped) > 200:
        return False

    normalized = _normalize_for_web_routing(stripped)
    if normalized.startswith("web:"):
        return True

    has_temporal_signal = any(token in normalized for token in WEB_TEMPORAL_SIGNALS)
    has_live_topic = any(token in normalized for token in WEB_LIVE_TOPICS)
    has_health_topic = any(token in normalized for token in WEB_HEALTH_TOPICS)
    has_location_topic = any(token in normalized for token in WEB_LOCATION_TOPICS)
    has_current_event_topic = any(token in normalized for token in WEB_CURRENT_EVENT_TOPICS)
    has_update_intent = any(token in normalized for token in WEB_UPDATE_INTENTS)
    looks_like_question = "?" in stripped or normalized.startswith(WEB_QUESTION_STARTERS)

    return looks_like_question and (
        (has_temporal_signal and (has_live_topic or has_health_topic or has_location_topic))
        or (has_update_intent and (has_current_event_topic or has_health_topic))
        or (has_location_topic and has_health_topic)
    )


def _last_live_web_topic(history: list[dict[str, str]] | None) -> str | None:
    if not history or len(history) < 2:
        return None

    last_assistant = history[-1]
    last_user = history[-2]
    if last_assistant.get("role") != "assistant" or last_user.get("role") != "user":
        return None

    assistant_text = last_assistant.get("content", "")
    user_text = (last_user.get("content") or "").strip()
    normalized = _normalize_for_web_routing(user_text)
    padded = f" {normalized} "
    personal_signal = any(term in padded for term in FOLLOW_UP_PERSONAL_TERMS)
    has_topical_signal = (
        any(token in normalized for token in WEB_UPDATE_INTENTS)
        or any(token in normalized for token in WEB_TEMPORAL_SIGNALS)
        or any(token in normalized for token in WEB_LIVE_TOPICS)
        or any(token in normalized for token in WEB_CURRENT_EVENT_TOPICS)
    )
    if "🌐 Used live web" not in assistant_text:
        return None
    if not user_text or len(user_text) > 200 or personal_signal or not has_topical_signal:
        return None
    return user_text


def extract_auto_web_query(message: str, history: list[dict[str, str]] | None = None) -> str | None:
    """Return a safe auto-web query or None."""
    if not AUTO_WEB_SEARCH_ENABLED:
        return None

    stripped = (message or "").strip()
    if not stripped or len(stripped) > 200:
        return None

    normalized = _normalize_for_web_routing(stripped)
    if normalized.startswith("web:"):
        return None

    recent_live_topic = _last_live_web_topic(history)

    explicit_match = EXPLICIT_WEB_SEARCH_RE.match(stripped)
    if explicit_match:
        explicit_tail = explicit_match.group(1).strip(" :-,?!.")
        if explicit_tail:
            return explicit_tail
        return recent_live_topic

    if _looks_like_live_or_current_query(stripped):
        return stripped

    word_count = len(stripped.split())
    looks_like_question = "?" in stripped or normalized.startswith(WEB_QUESTION_STARTERS)
    has_reference = any(term in normalized.split() for term in FOLLOW_UP_REFERENCE_TERMS)
    has_time_signal = any(term in normalized for term in FOLLOW_UP_TIME_TERMS)
    padded = f" {normalized} "
    personal_signal = any(term in padded for term in FOLLOW_UP_PERSONAL_TERMS)

    if recent_live_topic and word_count <= 10 and looks_like_question and has_reference and has_time_signal and not personal_signal:
        return f"{recent_live_topic} {stripped}"

    return None


def should_auto_web_search(message: str, history: list[dict[str, str]] | None = None) -> bool:
    """Return True when conservative auto-web routing should run."""
    return extract_auto_web_query(message, history) is not None
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
            "I'm here as your personal support companion — warm, direct, "
            "and tailored to you, without pretending to be a clinician.\n\n"
            "What's on your mind today? 💙"
        )
    else:
        await send_markdown_message(update, WELCOME_MESSAGE)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_markdown_message(update, HELP_MESSAGE)


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current chat ID and thread ID, if available."""
    chat = update.effective_chat
    message = update.effective_message
    chat_id = chat.id if chat else "unknown"
    chat_type = chat.type if chat else "unknown"
    thread_id = getattr(message, "message_thread_id", None)

    reply = f"🧭 **Chat ID**\n\n`{chat_id}`\n\n**Type:** `{chat_type}`"
    if thread_id is not None:
        reply += f"\n**Thread:** `{thread_id}`"

    await send_markdown_message(update, reply)


async def cmd_votd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a short Bible verse of the day."""
    user_id = update.effective_user.id if update.effective_user else "unknown"

    try:
        verse = await get_verse_of_the_day()
    except Exception as e:
        logger.warning(f"Failed to fetch Verse of the Day for user {user_id}: {e}")
        await send_votd_unavailable(update)
        return

    await send_markdown_message(
        update,
        format_votd_message(
            verse_text=verse.text,
            reference=verse.reference,
            version=verse.version,
            link=verse.link,
        ),
    )


async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current mode and model assignment."""
    user_id = update.effective_user.id
    personal_mode = is_personal_mode(user_id)
    current_model = get_user_model(user_id)
    
    if personal_mode:
        user_info = PERSONAL_MODE_USERS[user_id]
        name = user_info.get("name", "Personal User")
        assigned_model = user_info.get("model", "Auto-assigned")
        
        await send_markdown_message(update,
            f"👤 **Personal Mode Active**\n\n"
            f"**User:** {name}\n"
            f"**Model:** `{current_model}`\n"
            f"**Assignment:** {'Premium' if str(assigned_model).startswith('gpt-5') else 'Standard'}\n\n"
            f"🎯 You have access to personalized context and premium model support."
        )
    else:
        await send_markdown_message(update,
            "🔒 **Standard Mode: ACTIVE**\n\n"
            "You're using the standard MindMate experience.\n\n"
            f"User ID: `{user_id}`",
        )

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await clear_history(user_id)
    logger.info(f"User {user_id} cleared history")
    await send_markdown_message(update, "Conversation history cleared. 🧹")

async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store lightweight user feedback for product improvement."""
    user_id = update.effective_user.id
    feedback_text = " ".join(context.args).strip()

    if not feedback_text:
        await send_markdown_message(update,
            "📝 **Share feedback anytime**\n\n"
            "Use `/feedback <what helped or what felt off>`\n"
            "Example: `/feedback The reminder tone felt supportive, but the reply was too long.`"
        )
        return

    metadata = {
        "command": "feedback",
        "personal_mode": is_personal_mode(user_id),
        "model": get_user_model(user_id),
        "message_date": update.message.date.isoformat() if update.message and update.message.date else None,
        "storage_mode": "memory" if is_degraded_memory_mode() else "persistent",
    }

    saved = False
    session_only = False
    storage_label = "unknown"

    if db_manager and hasattr(db_manager, "store_feedback"):
        try:
            result = await db_manager.store_feedback(user_id, feedback_text, metadata=metadata, source="telegram-command")
            saved = bool(result.get("saved"))
            session_only = bool(result.get("session_only"))
            storage_label = result.get("storage", storage_label)
        except Exception as e:
            logger.warning(f"Failed to store feedback for user {user_id}: {e}")

    if not saved:
        await send_markdown_message(update,
            "📝 Thanks — I couldn't save that note permanently just now, but the feedback command is live and can be retried later."
        )
        return

    if session_only:
        await send_markdown_message(update,
            "📝 Thanks — I saved that feedback for this session, but my longer-term memory is temporarily limited right now."
        )
    else:
        await send_markdown_message(update,
            "📝 Thanks — I saved that feedback for review."
        )

    logger.info(f"Stored feedback from user {user_id} via {storage_label} storage")


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /model command for A/B testing."""
    user_id = update.effective_user.id
    args = context.args
    
    # Show current model if no args
    if not args:
        current = get_user_model(user_id)
        models_list = "\n".join([f"• `{k}` → {v}" for k, v in AVAILABLE_MODELS.items()])
        await send_markdown_message(update,
            f"🧪 **A/B Testing Mode**\n\n"
            f"**Current model:** `{current}`\n\n"
            f"**Available models:**\n{models_list}\n\n"
            f"**Usage:** `/model 5.4-mini`",
        )
        return
    
    # Set new model
    model_key = args[0].lower()
    if model_key in AVAILABLE_MODELS:
        new_model = AVAILABLE_MODELS[model_key]
        set_user_model(user_id, new_model)
        await clear_history(user_id)  # Clear history when switching models
        logger.info(f"User {user_id} switched to model: {new_model}")
        await send_markdown_message(update,
            f"✅ Switched to **{new_model}**\n\n"
            f"History cleared for fresh comparison.\n"
            f"Start chatting to test this model!",
        )
    else:
        await send_markdown_message(update,
            f"❌ Unknown model: `{model_key}`\n\n"
            f"Available: {', '.join(AVAILABLE_MODELS.keys())}",
        )


async def cmd_remember(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remember important information - easier to remember than /context."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    if context.args:
        # Add context: /remember "I have bipolar type 2"
        context_text = " ".join(context.args)
        
        # Add to conversation history as a system message for immediate context
        await add_to_history(user_id, "system", f"IMPORTANT USER CONTEXT: {context_text}")
        
        # Also update journey tracking with structured context
        await update_context_from_message(user_id, context_text)
        
        await send_markdown_message(update,
            f"🧠 **Got it!** I'll remember this for our conversations.\n\n"
            f"💡 This helps me provide better, more personalized support."
        )
        logger.info(f"User {user_id} remembered: {context_text}")
    else:
        # Show current context and explain auto-learning
        current_context = await get_user_journey_summary(user_id)
        
        await send_markdown_message(update,
            f"🧠 **Share important information to remember:**\n\n"
            f"• `/remember I have bipolar type 2` - Medical info\n"
            f"• `/remember I take Lithium 300mg daily` - Medication details\n"
            f"• `/remember My therapist is Dr. Smith` - Treatment info\n"
            f"• `/remember I live alone in Johannesburg` - Living situation\n"
            f"• `/remember My boyfriend is very supportive` - Relationship info\n\n"
            f"🧠 **Current Understanding:**\n{current_context}\n\n"
            f"🤖 **Automatic Learning:** I also learn from our conversations naturally! "
            f"When you mention medications, symptoms, life changes, or relationship issues, "
            f"I remember these for future support. No need to manually add everything "
            f"unless it's important information you want me to prioritize."
        )


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forget specific information - remove from journey tracking."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    if context.args:
        # Forget specific information: /forget "medication status"
        forget_text = " ".join(context.args).lower()
        
        # Try to match and remove specific journey entries
        removed_items = []
        
        journey = await ensure_user_journey_loaded(user_id)
        journey_keys_to_remove = []

        if any(word in forget_text for word in ["medication", "meds", "medicine"]):
            if "medication_status" in journey:
                journey.pop("medication_status", None)
                journey_keys_to_remove.append("medication_status")
                removed_items.append("medication status")

        if any(word in forget_text for word in ["therapy", "therapist", "counselor"]):
            if "therapy_status" in journey:
                journey.pop("therapy_status", None)
                journey_keys_to_remove.append("therapy_status")
                removed_items.append("therapy status")

        if any(word in forget_text for word in ["diagnosis", "condition", "bipolar"]):
            if "diagnosis_status" in journey:
                journey.pop("diagnosis_status", None)
                journey_keys_to_remove.append("diagnosis_status")
                removed_items.append("diagnosis status")

        if any(word in forget_text for word in ["relationship", "partner", "boyfriend", "girlfriend"]):
            if "relationship_status" in journey:
                journey.pop("relationship_status", None)
                journey_keys_to_remove.append("relationship_status")
                removed_items.append("relationship status")

        if any(word in forget_text for word in ["work", "job", "career"]):
            if "career_status" in journey:
                journey.pop("career_status", None)
                journey_keys_to_remove.append("career_status")
                removed_items.append("career status")

        if journey_keys_to_remove:
            journey["last_updated"] = datetime.now().isoformat()
            if db_manager and hasattr(db_manager, "delete_user_journey_keys"):
                try:
                    await db_manager.delete_user_journey_keys(user_id, journey_keys_to_remove)
                except Exception as e:
                    logger.warning(f"Failed to delete journey keys for user {user_id}: {e}")
            else:
                await persist_user_journey(user_id)
        
        if removed_items:
            await update.message.reply_text(
                f"🗑️ **Forgotten:** {', '.join(removed_items)}\n\n"
                f"💡 I've removed this information from my memory. "
                f"I'll update my understanding based on future conversations."
            )
            logger.info(f"User {user_id} forgot: {', '.join(removed_items)}")
        else:
            await update.message.reply_text(
                f"❓ **Not sure what to forget.**\n\n"
                f"Try: `/forget medication` or `/forget therapy` or `/forget relationship`\n\n"
                f"💡 I'll remove that specific information from my memory."
            )
    else:
        await update.message.reply_text(
            f"🗑️ **Forget specific information:**\n\n"
            f"• `/forget medication` - Remove medication info\n"
            f"• `/forget therapy` - Remove therapy info\n"
            f"• `/forget diagnosis` - Remove diagnosis info\n"
            f"• `/forget relationship` - Remove relationship info\n"
            f"• `/forget work` - Remove career info\n\n"
            f"💡 I'll remove that specific information from my memory "
            f"and update based on future conversations."
        )


async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm saving of last uploaded file to memory."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    # Check if there's a pending file/context to confirm
    pending_item = pending_context.get(user_id)
    if not pending_item:
        await update.message.reply_text(
            "❓ **No pending file to confirm.**\n\n"
            "Please upload a file first, then use /confirm to save it to my memory."
        )
        return
    
    file_info = pending_item["file_info"]
    description = pending_item["description"]
    
    await add_to_history(user_id, "system", f"USER FILE: {file_info}\n\n{description}")
    
    # Update journey tracking with file insights
    await update_context_from_message(user_id, f"Uploaded file: {description[:200]}")
    
    # Clear pending file/context
    del pending_context[user_id]
    
    await update.message.reply_text(
        f"✅ **File saved to memory!**\n\n"
        f"📄 **{file_info}** has been saved to our conversation history.\n\n"
        f"💡 I'll use this information to provide better, more personalized support."
    )
    
    logger.info(f"User {user_id} confirmed file/context: {file_info}")


async def cmd_decline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Decline saving of last uploaded file."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    # Check if there's a pending file/context to decline
    pending_item = pending_context.get(user_id)
    if not pending_item:
        await update.message.reply_text(
            "❓ **No pending file to decline.**\n\n"
            "Please upload a file first, then use /decline to discard it."
        )
        return
    
    file_info = pending_item["file_info"]
    
    # Clear pending file/context
    del pending_context[user_id]
    
    await update.message.reply_text(
        f"🗑️ **File discarded.**\n\n"
        f"📄 **{file_info}** has been removed and not saved to memory.\n\n"
        f"💡 Your privacy is important - nothing was retained."
    )
    
    logger.info(f"User {user_id} declined file/context: {file_info}")


async def cmd_journey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show your journey tracking and what I've learned about you."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    # Get journey summary
    journey_summary = await get_user_journey_summary(user_id)
    
    if not journey_summary or "No journey information" in journey_summary:
        await update.message.reply_text(
            "📔 **Your Journey**\n\n"
            "I haven't learned much about you yet!\n\n"
            "💡 Share information using:\n"
            "• `/remember I have bipolar disorder`\n"
            "• `/remember I take Lithium 300mg`\n"
            "• Or just chat naturally - I learn from our conversations!\n\n"
            "🤖 **Automatic Learning:** I also detect important information "
            "from our conversations and remember it for future support."
        )
        return
    
    await update.message.reply_text(
        f"📔 **Your Journey Summary**\n\n"
        f"{journey_summary}\n\n"
        f"💡 **How I Learn:**\n"
        f"• Manual: `/remember` important information\n"
        f"• Automatic: I learn from our conversations\n"
        f"• Control: `/forget` to remove specific info\n\n"
        f"🎯 This helps me provide personalized support!"
    )


async def cmd_journal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily journaling and mood tracking."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    # Check if user has journal entries
    today = datetime.now().strftime("%Y-%m-%d")
    user_journals_today = await get_journal_entries_for_date(user_id, today)
    
    if user_journals_today:
        await update.message.reply_text(
            f"📔 **Today's Journal** ({today})\n\n"
            f"You've written {len(user_journals_today)} entry(ies) today.\n\n"
            f"💡 **Recent entries:**\n"
            + "\n\n".join([
                f"• {entry['timestamp'].split('T')[1][:5]} - {entry['entry'][:100]}..."
                for entry in user_journals_today[-3:]
            ]) + "\n\n"
            f"🎯 Keep writing! Your consistency builds valuable insights."
        )
    else:
        await update.message.reply_text(
            f"📔 **Daily Journal** ({today})\n\n"
            f"No entries yet today.\n\n"
            f"💡 **Start journaling:**\n"
            f"• Write about your day\n"
            f"• Share how you're feeling\n"
            f"• Note any challenges or wins\n\n"
            f"🎯 I'll remember your entries and help you spot patterns!"
        )


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manage the env-gated daily journaling reminder MVP."""
    user_id = update.effective_user.id

    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return

    action = (context.args[0].strip().lower() if context.args else "status")
    if action not in {"status", "on", "off", "test"}:
        await update.message.reply_text(
            "⏰ Use `/schedule status`, `/schedule on`, `/schedule off`, or `/schedule test`."
        )
        return

    rollout_limited = bool(DAILY_HEARTBEAT_ALLOWED_USER_IDS)
    rollout_allows_user = (not rollout_limited) or (user_id in DAILY_HEARTBEAT_ALLOWED_USER_IDS)

    if action == "test":
        if not can_force_test_daily_heartbeat(user_id):
            await update.message.reply_text(
                "⏰ Manual test sends are limited to the current heartbeat test allowlist."
            )
            return
        if not telegram_app or not telegram_app.bot:
            await update.message.reply_text(
                "⏰ The live bot context isn't ready yet. Please try again in a moment."
            )
            return
        pending_tracking = await get_latest_pending_daily_summary_tracking(user_id)
        if pending_tracking and pending_tracking.get("waiting_for_summary"):
            await update.message.reply_text(
                "⏰ You've already got an active check-in waiting for a reply, so I didn't send another one."
            )
            return

        await send_scheduled_daily_summary(user_id)
        pending_tracking = await get_latest_pending_daily_summary_tracking(user_id)
        if pending_tracking and pending_tracking.get("waiting_for_summary"):
            await update.message.reply_text(
                "🧪 Sent a live test check-in from inside the running bot. This won't mark today's scheduled send as completed."
            )
        else:
            await update.message.reply_text(
                "⏰ I couldn't send the live test check-in just now. Please check the bot logs."
            )
        return

    if action == "on":
        if not DAILY_HEARTBEAT_ENABLED:
            await update.message.reply_text(
                "⏰ Daily check-ins aren't live right now. The scheduler is still disabled on the server."
            )
            return
        if not rollout_allows_user:
            await update.message.reply_text(
                "⏰ Daily check-ins are in a limited rollout right now, so I can't enable them for this account yet."
            )
            return
        await set_daily_heartbeat_enabled_for_user(user_id, True)
    elif action == "off":
        await set_daily_heartbeat_enabled_for_user(user_id, False)

    enabled_for_user = await is_daily_heartbeat_enabled_for_user(user_id)
    journey = await ensure_user_journey_loaded(user_id)
    last_summary = journey.get('last_daily_summary', 'No recent summaries')
    timezone_name = get_daily_heartbeat_timezone().key
    rollout_note = "Limited rollout (default on)" if rollout_limited else "Default on"
    scheduler_status = "enabled" if DAILY_HEARTBEAT_ENABLED else "disabled"
    user_status = "on" if enabled_for_user else "off"

    await send_markdown_message(
        update,
        f"⏰ **Daily Check-in Schedule**\n\n"
        f"Scheduler: **{scheduler_status}**\n"
        f"Your reminder: **{user_status}**\n"
        f"Time: **{DAILY_HEARTBEAT_HOUR:02d}:00 {timezone_name}**\n"
        f"Delivery: **direct message from MindMate**\n"
        f"Rollout: **{rollout_note}**\n\n"
        f"Reply naturally when I check in. If you're busy, say **later** or **skip** and I'll leave it for the next day.\n\n"
        f"Recent activity: **{last_summary}**"
    )


async def cmd_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Share important context about your condition, medications, or treatment."""
    user_id = update.effective_user.id
    
    if not is_personal_mode(user_id):
        await send_markdown_message(update, "This feature is only available in Personal Mode.")
        return
    
    if context.args:
        # Add context: /context "I take Lithium 300mg twice daily for bipolar"
        context_text = " ".join(context.args)
        
        # Add to conversation history as a system message for immediate context
        await add_to_history(user_id, "system", f"IMPORTANT USER CONTEXT: {context_text}")
        
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
    history = await get_history(user_id)

    # ------------------------------------------------------------------
    # Optional, explicit Brave web search trigger
    # Pattern: messages starting with "web:" (e.g. "web: bitcoin price today")
    # keep this opt-in only; no background/implicit web calls
    # ------------------------------------------------------------------
    web_results = None
    web_query = None
    web_search_result = None
    used_web = False

    stripped = message.strip()
    lowered = stripped.lower()
    if lowered.startswith("web:"):
        # Everything after the first colon is treated as the web query
        web_query = stripped.split(":", 1)[1].strip()
        if not web_query:
            await update.message.reply_text(
                "To use web search, type something like: `web: bitcoin price today`.",
            )
            return

        search_result = search_web(web_query, max_results=5)
        if search_result.ok:
            web_search_result = search_result
            web_results = search_result.summary
            used_web = True
            logger.info(
                "Fetched %s web results for user %s query: %s...",
                search_result.result_count,
                user_id,
                web_query[:80],
            )
        else:
            logger.warning(
                "Web search unavailable for user %s query '%s': %s",
                user_id,
                web_query[:80],
                search_result.error,
            )
            await update.message.reply_text(
                f"🌐 Web lookup unavailable: {search_result.error}\n\nI'll answer without live web data."
            )

        # When using web search, treat the user's visible query as the portion after `web:`
        message = web_query
    else:
        auto_web_query = extract_auto_web_query(stripped, history)
        if auto_web_query:
            web_query = auto_web_query
            search_result = search_web(web_query, max_results=5)
            if search_result.ok:
                web_search_result = search_result
                web_results = search_result.summary
                used_web = True
                logger.info(
                    "Auto-fetched %s web results for user %s query: %s...",
                    search_result.result_count,
                    user_id,
                    web_query[:80],
                )
            else:
                logger.info(
                    "Auto web lookup skipped for user %s query '%s': %s",
                    user_id,
                    web_query[:80],
                    search_result.error,
                )

    # Check if this is a reply to a scheduled daily summary message
    pending_tracking = await get_latest_pending_daily_summary_tracking(user_id)
    if pending_tracking and pending_tracking.get("waiting_for_summary"):
        # This is a reply to our daily summary request, including after restart.
        await handle_daily_summary_response(update, context, user_id, message)
        return
    
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
            await send_markdown_message(update, CRISIS_RESPONSE)
            return
    
    if not openai_client:
        await update.message.reply_text("I'm temporarily unavailable. Please try again later.")
        return

    await maybe_send_degraded_mode_notice(update, user_id)

    if personal_mode:
        await update_context_from_message(user_id, message)

    current_model = get_user_model(user_id)
    current_time = update.message.date.strftime("%I:%M %p on %B %d, %Y")
    system_prompt = build_generation_system_prompt(
        user_id,
        personal_mode=personal_mode,
        response_mode="chat",
        current_time=current_time,
        web_results=web_results,
    )

    mode_str = "PERSONAL" if personal_mode else "STANDARD"
    logger.info(f"Message from user {user_id} [{mode_str}] using model {current_model}")
    
    try:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        response = openai_client.chat.completions.create(
            **build_chat_completion_kwargs(
                model=current_model,
                messages=messages,
                max_output_tokens=600,
            )
        )
        reply = response.choices[0].message.content

        web_attribution_line = build_web_attribution_line(web_search_result) if used_web else ""
        if web_attribution_line:
            reply = f"{reply}\n\n{web_attribution_line}"
        
        await add_to_history(user_id, "user", message)
        await add_to_history(user_id, "assistant", reply)
        
        await send_markdown_message(update, reply)
        logger.info(f"Responded to user {user_id}")
        
    except OpenAIError as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text(
            build_chat_recovery_message(e, used_web=used_web)
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "💙 Something went wrong while I was preparing that reply. "
            "Please try again, or resend the main part in one shorter message."
        )


async def handle_daily_summary_response(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str) -> None:
    """Handle response to daily summary request with smart filtering."""
    
    # Check if user wants to postpone or skip
    postpone_keywords = ["busy", "later", "not now", "can't", "cannot", "postpone", "skip", "not today", "tomorrow"]
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in postpone_keywords):
        # User wants to postpone
        tracking = await get_latest_pending_daily_summary_tracking(user_id) or {}
        local_date = tracking.get("local_date") or datetime.now().strftime("%Y-%m-%d")
        await set_daily_summary_tracking(
            user_id,
            local_date,
            False,
            sent_at=datetime.fromisoformat(tracking["sent_time"]) if tracking.get("sent_time") else None,
            prompt_message_id=tracking.get("message_id"),
            prompt_kind=tracking.get("kind", "daily_heartbeat"),
            status="dismissed",
            metadata=tracking.get("metadata"),
        )

        await update.message.reply_text(
            f"👍 **No problem!** I understand you're busy right now.\n\n"
            f"💡 Just send me your check-in whenever you're ready, or I'll check in again tomorrow morning.\n\n"
            f"Take care! 💙"
        )
        
        # Update journey tracking
        await update_user_journey(user_id, "journaling_pattern", "Sometimes busy, flexible schedule")
        return
    
    # This looks like a daily heartbeat reply - save it as a journal check-in
    tracking = await get_latest_pending_daily_summary_tracking(user_id) or {}
    today = tracking.get("local_date") or datetime.now().strftime("%Y-%m-%d")

    response_message_id = getattr(update.message, "message_id", None)
    _, created = await append_journal_entry_for_user(
        user_id=user_id,
        local_date=today,
        entry_text=message,
        entry_type="daily_heartbeat",
        metadata={
            "source": "daily_checkin_reply",
            "prompt_message_id": tracking.get("message_id"),
        },
        source_message_id=response_message_id,
    )

    await set_daily_summary_tracking(
        user_id,
        today,
        False,
        sent_at=datetime.fromisoformat(tracking["sent_time"]) if tracking.get("sent_time") else None,
        responded_at=datetime.now(),
        prompt_message_id=tracking.get("message_id"),
        response_message_id=response_message_id,
        prompt_kind=tracking.get("kind", "daily_heartbeat"),
        status="completed",
        metadata=tracking.get("metadata"),
    )

    # Update journey tracking
    await update_user_journey(user_id, "last_daily_summary", today)
    await update_user_journey(user_id, "journaling_habit", "Active - responds to daily prompts")
    
    if created:
        if is_degraded_memory_mode():
            reply_text = (
                f"✅ **Check-in Recorded for Now**\n\n"
                f"Thanks for sharing. I recorded this for {today} while my memory is in a temporary lighter mode.\n\n"
                f"⚠️ That means it can help in this session, but it may not survive a restart. If it's important, feel free to send it again later once persistence is back."
            )
        else:
            reply_text = (
                f"✅ **Check-in Saved!**\n\n"
                f"Thanks for sharing. I saved this for {today} so I can support you with better continuity.\n\n"
                f"💡 I'll check in again tomorrow morning, and you can message me anytime before then too. 💙"
            )
        logger.info(f"User {user_id} submitted daily summary for {today}")
    else:
        if is_degraded_memory_mode():
            reply_text = (
                f"✅ **Check-in Already Recorded for Now**\n\n"
                f"I already recorded this reply for {today} in my temporary lighter-memory mode, so I didn't add it twice.\n\n"
                f"⚠️ Because storage is degraded right now, that temporary record may not survive a restart."
            )
        else:
            reply_text = (
                f"✅ **Check-in Already Saved**\n\n"
                f"I already recorded this reply for {today}, so I didn't add it twice.\n\n"
                f"💡 You're all set for today."
            )
        logger.info(f"Skipped duplicate daily summary reply for user {user_id} on {today}")

    await update.message.reply_text(reply_text)


async def update_context_from_message(user_id: int, message: str) -> None:
    """Automatically update user journey based on conversation content.
    
    This function uses simple keyword matching to detect important information in natural conversation.
    It's NOT built into the AI - it's custom application logic that scans messages for specific patterns.
    """
    message_lower = message.lower()
    
    # Medication mentions - scan for medication-related keywords
    if any(word in message_lower for word in ["medication", "meds", "medicine", "pill", "prescription", "dose", "lithium", "seroquel", "lamictal"]):
        if "take" in message_lower or "on" in message_lower or "start" in message_lower:
            await update_user_journey(user_id, "medication_status", "Currently taking medication")
        elif "stop" in message_lower or "quit" in message_lower or "off" in message_lower:
            await update_user_journey(user_id, "medication_status", "Stopped medication")
        elif "miss" in message_lower or "forget" in message_lower:
            await update_user_journey(user_id, "medication_adherence", "Sometimes misses doses")
    
    # Doctor/therapy mentions - scan for treatment-related keywords
    if any(word in message_lower for word in ["doctor", "therapist", "psychiatrist", "counselor", "appointment", "session"]):
        if "appointment" in message_lower or "visit" in message_lower or "see" in message_lower:
            await update_user_journey(user_id, "doctor_visits", "Recent doctor visit")
        elif "therapy" in message_lower or "counseling" in message_lower:
            await update_user_journey(user_id, "therapy_status", "Currently in therapy")
    
    # Mood/episode mentions - scan for bipolar-related keywords
    if any(word in message_lower for word in ["depressed", "depression", "manic", "mania", "episode", "mood swing", "hypomanic"]):
        if "last week" in message_lower or "recently" in message_lower:
            await update_user_journey(user_id, "last_mood_episode", "Recent mood episode")
    
    # Support system mentions - scan for family/social keywords
    if any(word in message_lower for word in ["family", "sister", "brother", "mom", "dad", "support", "alone", "isolated"]):
        if "help" in message_lower or "support" in message_lower:
            await update_user_journey(user_id, "family_support", "Has family support")
        elif "no support" in message_lower or "alone" in message_lower or "isolated" in message_lower:
            await update_user_journey(user_id, "family_support", "Limited family support")
    
    # Living situation mentions - scan for housing keywords
    if any(word in message_lower for word in ["live alone", "living by myself", "roommate", "apartment", "house", "moved"]):
        await update_user_journey(user_id, "living_situation", "Living independently")
    
    # Work/career mentions - scan for job-related keywords
    if any(word in message_lower for word in ["work", "job", "career", "boss", "coworker", "unemployed", "fired"]):
        if "stress" in message_lower or "overwhelmed" in message_lower:
            await update_user_journey(user_id, "career_status", "Work stress affecting mental health")
    
    # Relationship mentions - scan for relationship keywords
    if any(word in message_lower for word in ["boyfriend", "girlfriend", "partner", "relationship", "dating", "breakup", "friend"]):
        if "fight" in message_lower or "argument" in message_lower:
            await update_user_journey(user_id, "relationship_status", "Relationship conflicts")
        elif "supportive" in message_lower or "understanding" in message_lower:
            await update_user_journey(user_id, "relationship_status", "Supportive partner")
    
    logger.info(f"Auto-updated context for user {user_id} from message: {message[:50]}...")


async def send_scheduled_daily_summary(user_id: int) -> None:
    """Send the once-daily proactive MindMate verse + check-in flow and track the reply."""

    sent_at = datetime.now()
    local_date = sent_at.astimezone(get_daily_heartbeat_timezone()).strftime("%Y-%m-%d")
    tracking = await set_daily_summary_tracking(
        user_id,
        local_date,
        True,
        sent_at=sent_at,
        prompt_kind="daily_heartbeat",
        status="sent",
    )

    try:
        delivery_target = "telegram-user-direct"
        delivery_chat_id = user_id
        send_kwargs = {"disable_notification": False, "chat_id": user_id}

        if DAILY_HEARTBEAT_CHAT_ID:
            send_kwargs["chat_id"] = DAILY_HEARTBEAT_CHAT_ID
            delivery_target = "telegram-configured-chat"
            delivery_chat_id = DAILY_HEARTBEAT_CHAT_ID
            if DAILY_HEARTBEAT_MESSAGE_THREAD_ID.isdigit():
                send_kwargs["message_thread_id"] = int(DAILY_HEARTBEAT_MESSAGE_THREAD_ID)
                delivery_target = "telegram-configured-chat-thread"

        verse = None
        try:
            verse = await get_verse_of_the_day()
        except Exception as verse_error:
            logger.warning("Failed to fetch Verse of the Day for scheduled heartbeat user %s: %s", user_id, verse_error)

        verse_message = None
        if verse:
            verse_text = format_votd_message(
                verse_text=verse.text,
                reference=verse.reference,
                version=verse.version,
                link=verse.link,
            )
            verse_message = await telegram_app.bot.send_message(
                text=_render_basic_telegram_html(verse_text),
                parse_mode='HTML',
                **send_kwargs,
            )

        heartbeat_text = await build_daily_heartbeat_message(user_id, verse=verse)

        message = await telegram_app.bot.send_message(text=heartbeat_text, **send_kwargs)

        await set_daily_summary_tracking(
            user_id,
            local_date,
            True,
            sent_at=sent_at,
            prompt_message_id=message.message_id,
            prompt_kind="daily_heartbeat",
            status="sent",
            metadata={
                **(tracking.get("metadata") or {}),
                "delivery_target": delivery_target,
                "delivery_chat_id": delivery_chat_id,
                "delivery_thread_id": int(DAILY_HEARTBEAT_MESSAGE_THREAD_ID) if DAILY_HEARTBEAT_MESSAGE_THREAD_ID.isdigit() else None,
                "verse_message_id": verse_message.message_id if verse_message else None,
                "verse_reference": verse.reference if verse else None,
            },
        )
        logger.info("Sent daily verse/check-in flow to user %s via %s", user_id, delivery_target)

    except Exception as e:
        logger.error(f"Failed to send daily heartbeat to user {user_id}: {e}")
        await set_daily_summary_tracking(
            user_id,
            local_date,
            False,
            sent_at=sent_at,
            prompt_message_id=tracking.get("message_id"),
            prompt_kind="daily_heartbeat",
            status="failed",
            metadata={"error": str(e)},
        )


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
            await add_to_history(user_id, "user", transcribed_text)
            
            # Get conversation history
            history = await get_history(user_id)
            
            # Generate response
            current_model = get_user_model(user_id)
            current_time = update.message.date.strftime("%I:%M %p on %B %d, %Y") if update.message and update.message.date else None
            system_prompt = build_generation_system_prompt(
                user_id,
                personal_mode=personal_mode,
                response_mode="voice",
                current_time=current_time,
            )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": transcribed_text})
            
            response = openai_client.chat.completions.create(
                **build_chat_completion_kwargs(
                    model=current_model,
                    messages=messages,
                    max_output_tokens=500,
                )
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
            await add_to_history(user_id, "assistant", response_text)
            
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
            await add_to_history(user_id, "system", context_message)
            
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
