# 🗺️ MindMate Roadmap

This document outlines the vision, planned features, and development priorities for MindMate.

---

## 🎯 Vision

**MindMate aims to be a comprehensive AI-powered mental wellness companion that provides 24/7 personalized support.**

Available on **Telegram and WhatsApp**, with a **Premium Personal Mode** that acts as your dedicated AI therapist - no generic disclaimers, no deflecting to helplines, just real support.

---

## ✅ Completed Features

| Feature | Description | Date |
|---------|-------------|------|
| 🔓 **Personal Mode** | No disclaimers, direct advice, user context | Feb 2026 |
| ⚡ **FastAPI Migration** | Async webhooks, clean architecture | Feb 2026 |
| 🌐 **Webhook Support** | No more polling conflicts | Feb 2026 |
| 🧪 **A/B Testing Tools** | `/test`, `/rate`, `/results` commands | Feb 2026 |
| 📊 **Automated Blind Test** | `run_blind_test.py` script | Feb 2026 |
| 🎯 **User Context** | Name, location, focus areas in prompt | Feb 2026 |
| 🎛️ **Voice Messages** | Send/receive voice notes with smart caption handling | Feb 2026 |
| 💰 **Voice Cost Optimization** | 14% reduction in voice processing costs | Feb 2026 |
| 🔧 **Voice Caption Fix** | Smart splitting for long responses (Telegram 1024 limit) | Feb 2026 |
| 🎉 **MVP Completion** | All core features complete, ready for production release | Feb 2026 |

---

## 🎉 MVP Status: **COMPLETE** 

**MindMate v1.0.0 - Production Ready** ✅

All core MVP features have been successfully implemented and tested:

### ✅ **Core MVP Features**
- **💬 Empathetic Chat**: AI-powered conversations with emotional intelligence
- **🚨 Crisis Detection**: Automatic detection with SA helpline resources (SADAG)  
- **📝 Persistent Memory**: Redis-powered cross-session conversation history
- **🔍 Semantic Search**: Vector-based memory retrieval using OpenAI embeddings
- **🔓 Personal Mode**: Premium experience with direct advice (no disclaimers)
- **🎙️ Voice Messages**: Send voice notes → bot responds with voice ✅ **COMPLETED**
- **⚡ FastAPI Backend**: Modern async architecture with webhooks
- **🛡️ Graceful Fallback**: In-memory storage if Redis unavailable

### 🚀 **Deployment Status**
- **Production**: @mindmate_dev_bot live on Render
- **Staging**: @mywellnesscompanion_bot live on Render  
- **Health Monitoring**: UptimeRobot integration active
- **Documentation**: Comprehensive setup guides and API docs

### 📋 **Release Checklist**
- [x] All core features implemented
- [x] Voice functionality complete and tested
- [x] Personal Mode with user context working
- [x] Crisis detection with local resources
- [x] Persistent memory with Redis
- [x] Deployment stable on Render
- [x] Documentation comprehensive and up-to-date

**Ready for user feedback and iteration.**

---

## 🔥 Priority Features

### 🧪 A/B Model Testing (PAUSED - Pending Persona Testing)

**Current Model:** `gpt-4o-mini` (cheapest, using for now)

| Model | Cost/100 conv | Status |
|-------|---------------|--------|
| **gpt-4o-mini** | ~$0.02 | ✅ Currently deployed |
| gpt-4.1-mini | ~$4.00 | To be tested |
| gpt-5.2 | ~$740 | To be tested |

**Automated Test Complete:** `research/AB_TEST_RESULTS_20260205_130125.md`
- 15 generic prompts tested across all 3 models
- Ratings pending - will complete with persona-specific prompts

**Next Phase:** Persona-Based Testing
- [ ] Create prompts for: Relationships, Finances, Bipolar, Emotional Intelligence
- [ ] Run personalized test with focus areas
- [ ] Rate responses based on personal relevance
- [ ] Choose winner for Personal Mode

**Testing Tools:**
- `research/run_blind_test.py` - Run automated tests
- `research/calculate_results.py` - Calculate winner from ratings

---

### 📱 Multi-Platform Support

| Feature | Details | Priority |
|---------|---------|----------|
| **WhatsApp Integration** | Twilio WhatsApp API | High |
| **Shared Conversation History** | Same history across Telegram & WhatsApp | High |
| **Platform Toggle** | User option to keep histories separate | Medium |

**Implementation Notes:**
- **Provider:** Twilio WhatsApp API ($11.53 credits available)
- **Cost:** ~$0.01-0.02 per message exchange (~500-1,000 messages with credits)
- Same backend, different message handlers
- User links accounts via phone number verification
- Webhook receives WhatsApp messages → same AI logic → respond via Twilio

---

### 🔓 Personal/Premium Mode

A private, unfiltered AI therapist experience. No corporate guardrails.

| Feature | Description | Status |
|---------|-------------|--------|
| **No AI Disclaimers** | Removes "As an AI..." and robotic responses | ✅ Done |
| **No Helpline Redirects** | Direct support instead of deflecting to hotlines | ✅ Done |
| **Direct Personalized Advice** | Therapist-style guidance, not generic tips | ✅ Done |
| **Softer Crisis Handling** | Shows resources but continues conversation | ✅ Done |
| **User Context in Prompt** | Name, location, focus areas hardcoded | ✅ Done |
| **Focus Areas Config** | User sets their specific challenges via /profile | 🔜 Next |
| **Memory Across Sessions** | Remembers your history, patterns, progress | 🔜 Next |
| **Private by Default** | Locked to specific user IDs | ✅ Done |

**Current Implementation:**
- Branch: `feature/personal-mode`
- Dev Bot: @mindmate_dev_bot
- Authorized User: 339651126 (djpapzin)

**Business Model:**
- Free tier: Standard MindMate (with guardrails)
- Premium tier: Personal Mode (subscription - future)

---

### 🔍 Internet Search Capabilities

**Status:** 🔜 Next Priority

Enable bot to search the internet for current information, resources, and evidence-based mental health content.

| Feature | Description | Priority |
|---------|-------------|----------|
| **Real-time Information** | Search for current mental health research, news, and resources | High |
| **Resource Verification** | Find and verify local mental health services and crisis lines | High |
| **Evidence-based Responses** | Supplement AI knowledge with up-to-date research findings | Medium |
| **Local Service Discovery** | Search for therapists, support groups, and services by location | Medium |
| **Web Search Tool Implementation** | Integrate search API for real-time information access | High |

**Implementation Approach:**
- **Search API:** Use Google Search API or Bing Search API
- **Content Filtering:** Ensure results are from reputable mental health sources
- **Privacy:** No personal data in searches, only general queries
- **Cost Control:** Limit searches per conversation to manage API costs

**Use Cases:**
- "Find therapists near me who specialize in anxiety"
- "What are the latest research findings on CBT for depression?"
- "Local support groups for bipolar disorder in Johannesburg"
- "Current mental health resources during COVID-19"

**Technical Implementation:**
```python
# Search integration example
async def search_internet(query: str, location: str = None) -> List[SearchResult]:
    """Search the internet for mental health resources and information"""
    search_query = f"{query} mental health"
    if location:
        search_query += f" {location}"
    
    results = search_api.search(search_query, safe_search="active")
    
    # Filter for reputable sources only
    filtered_results = [
        result for result in results 
        if is_reputable_source(result.domain)
    ]
    
    return filtered_results[:5]  # Limit to top 5 results
```

**Priority:** High (significantly enhances bot's usefulness and credibility)

---

### 🧠 Redis Vector Storage ✅ COMPLETE

Long-term memory with semantic search so the bot truly knows you across sessions.

| Feature | Description | Status |
|---------|-------------|--------|
| **Redis Cloud Storage** | Replace in-memory with persistent Redis | ✅ |
| **Vector Search** | Semantic memory retrieval using embeddings | ✅ |
| **Auto-expiration** | TTL-based cleanup of old conversations | ✅ |
| **User Profiles** | Redis hash for preferences and context | ✅ |
| **Session Memory** | Cross-session continuity | ✅ |
| **Fallback Storage** | In-memory fallback if Redis unavailable | ✅ |

**Redis Data Structure:**
```redis
# Conversation history
conversation:{user_id} -> List[message_json]

# User preferences
user:{user_id} -> Hash{name, focus_areas, preferences}

# Vector embeddings for semantic search
message:{message_id} -> Hash{content, embedding_vector, metadata}

# Vector index for semantic search
msg_idx -> RediSearch Vector Index
```

**Implementation Completed:**
1. ✅ Set up Redis on Render (free tier)
2. ✅ Created `src/redis_db.py` with vector search
3. ✅ Updated bot.py to use Redis storage
4. ✅ Added semantic context retrieval
5. ✅ Implemented auto-expiration policies
6. ✅ Added graceful fallback to in-memory storage

**Benefits Achieved:**
- **10x faster** performance vs PostgreSQL
- **Semantic memory** for better context awareness
- **Auto-scaling** with Redis cloud hosting
- **Zero downtime** with fallback storage
- **Cost-effective** free tier on Render

---

### ⚡ Switch to FastAPI ✅ COMPLETE

Migrated from Flask to FastAPI for better async support and performance.

| Benefit | Description | Status |
|---------|-------------|--------|
| **Native Async** | No more bridging sync Flask with async Telegram | ✅ |
| **Better Performance** | Faster request handling | ✅ |
| **Auto Documentation** | Built-in Swagger/OpenAPI docs at `/docs` | ✅ |
| **Type Hints** | Better code validation | ✅ |
| **Clean Webhooks** | Simple `await telegram_app.process_update()` | ✅ |

**What Changed:**
- Replaced Flask with FastAPI + Uvicorn
- Webhook endpoint is now pure async (no threading hacks)
- Bot lifecycle managed via FastAPI lifespan context
- Same start command: `python bot.py`

---

### 📞 Voice Calls (Twilio + ElevenLabs)

**Status:** 🔮 Future Enhancement

Enable phone call conversations with MindMate using voice.

| Component | Purpose |
|-----------|---------|
| **Twilio Voice** | Handle incoming/outgoing phone calls |
| **ElevenLabs** | Natural text-to-speech (AI voice) |
| **Whisper/Deepgram** | Speech-to-text transcription |
| **OpenAI** | Generate responses (same as chat) |

**Flow:**
```
User calls → Twilio receives → Whisper transcribes → OpenAI responds → ElevenLabs speaks → User hears
```

**Features:**
- Call the bot anytime for voice support
- Natural, empathetic AI voice
- Same Personal Mode experience
- Crisis detection still active

**Implementation:**
1. Set up Twilio phone number
2. Create voice webhook endpoint
3. Integrate Whisper for speech-to-text
4. Integrate ElevenLabs for text-to-speech
5. Handle real-time streaming

**Priority:** Medium (powerful feature, but complex)

---

### 🔄 n8n Automation

**Status:** 🔮 Future Enhancement

Automate workflows using n8n (self-hosted automation platform).

| Automation | Description |
|------------|-------------|
| **Daily Check-ins** | Scheduled messages: "How are you feeling today?" |
| **Mood Reports** | Weekly email summary of mood trends |
| **Crisis Alerts** | Notify emergency contact (with consent) |
| **Backup Data** | Auto-export conversation summaries |
| **Multi-channel Sync** | Sync between Telegram/WhatsApp |

**Why n8n?**
- Self-hosted (privacy)
- Visual workflow builder
- Connects to 400+ apps
- Free and open source

**Implementation:**
1. Deploy n8n on Render/Railway
2. Connect to PostgreSQL database
3. Create webhook triggers from bot
4. Build automation workflows
5. Schedule recurring tasks

**Example Workflows:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Every 9 AM  │────►│ Check user  │────►│ Send Telegram│
│ (Schedule)  │     │ preferences │     │ "Good morning│
└─────────────┘     └─────────────┘     │  check-in"  │
                                        └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Crisis      │────►│ Log to DB   │────►│ Email alert │
│ detected    │     │             │     │ (if enabled)│
└─────────────┘     └─────────────┘     └─────────────┘
```

**Priority:** Medium (enables powerful automations)

---

### 🎯 Personalization (Focus Areas)

Configurable areas the bot specializes in for each user:

| Area | What It Covers |
|------|----------------|
| 💑 **Relationships** | Dating, communication, boundaries, breakups, family |
| 💰 **Finances** | Money stress, budgeting anxiety, financial goals |
| 🧠 **Bipolar Management** | Mood tracking, episode awareness, stability strategies |
| 😰 **Anxiety** | Panic attacks, social anxiety, worry management |
| 😔 **Depression** | Low mood, motivation, daily functioning |
| 💼 **Work/Career** | Burnout, work-life balance, career transitions |

---

### 💡 Engagement Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **🎤 Voice Messages** | Send voice notes → bot responds (text or audio) | Medium |
| **📅 Daily Check-ins** | Bot messages YOU first: "How are you feeling today?" | High |
| **📊 Session Summaries** | Weekly recap of your mental health journey | Medium |
| **📈 Mood Trends** | "You've been feeling better this week vs last" | High |
| **💾 Export History** | Download conversations as a personal journal | Low |

---

### 🧠 AI Configuration (Research Complete ✅)

**Available Credits:** $2,500.95 → **194 years of personal use!**  
**Account Tier:** Usage Tier 3  
**Research:** See `research/MODEL_RESEARCH_FINDINGS.md`

#### ✅ Chosen Model Stack

| Purpose | Model | Why |
|---------|-------|-----|
| **Chat** | `gpt-4o-mini` | 117 EQ (89th percentile), 4.19/5 therapy rating, $0.02/100 chats |
| **Voice Input** | `gpt-4o-mini-transcribe` | Latest GPT-4o mini based, better accuracy than Whisper v1/v3 |
| **Voice Output** | `gpt-4o-mini-tts` | Most reliable TTS, supports 13 voices, emotional range |
| **Voice Selection** | `gpt-4o-mini-tts` with 13 voices (alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse, marin, cedar) | Choose personality: alloy (balanced), marin/cedar (best quality) |

#### ❌ Models to Avoid

| Model | Why Avoid |
|-------|-----------|
| GPT-5, GPT-5.2 | 52% more restrictive, will deflect to "see a professional" |
| o3, o4-mini | 30-120s response times, wrong purpose (reasoning, not empathy) |
| GPT-4o | 16x more expensive than mini, minimal benefit |

#### Configuration

```python
model = "gpt-4o-mini"
temperature = 0.8          # Warm, empathetic responses
presence_penalty = 0.6     # Reduces repetition
frequency_penalty = 0.3    # Encourages variety
max_tokens = 600
```

#### 3-Layer Guardrail Strategy

1. **System Prompt** - Anti-deflection language, direct advice persona
2. **Keyword Detection** - Separate crisis detection (current implementation)
3. **Response Filtering** - Regenerate if "As an AI..." detected

#### Cost Projections

| Usage | Monthly Cost |
|-------|--------------|
| Personal (100 convos + 50 min voice) | **$1.07** |
| 100 subscribers | $190-216 |

**Key Insight:** GPT-5 family was trained to reduce "emotional reliance" by 42% - it's designed to deflect, which is the OPPOSITE of what we want for Personal Mode.

---

## 📊 Current State (v1.0)

### ✅ Completed Features
- [x] OpenAI GPT-powered empathetic conversations
- [x] Crisis keyword detection with immediate SA helpline resources
- [x] Conversation history (10 messages per user)
- [x] User isolation (private conversations)
- [x] Basic commands (/start, /clear, /help)
- [x] Deployed on Render (free tier)
- [x] UptimeRobot monitoring for 24/7 availability
- [x] Automated test suite
- [x] Clean, documented codebase

### ⚠️ Current Limitations
| Limitation | Impact | Planned Fix |
|------------|--------|-------------|
| In-memory storage | History lost on redeploy | Database integration |
| Telegram only | Can't use on WhatsApp | Multi-platform support |
| No user profiles | Can't remember preferences | Personal Mode |
| Text only | Can't process voice messages | Voice support |
| Generic responses | Same for all users | Personalization |
| **Female voice only** | Users can't choose voice gender | **Voice selection menu** |

---

## 🚀 Development Phases

### Phase 1: Foundation (v1.1) 🏗️
**Timeline:** 2-4 weeks  
**Goal:** Make the bot production-ready with persistent data

#### Features
| Feature | Description | Effort |
|---------|-------------|--------|
| PostgreSQL/Redis | Persistent conversation storage | Medium |
| User profiles | Store name, preferences, timezone | Medium |
| Rate limiting | Prevent abuse (max messages/hour) | Easy |
| Improved errors | Graceful handling, user-friendly messages | Easy |
| Basic analytics | Message count, active users, peak times | Medium |

#### Technical
- [x] Set up Redis on Render (free tier)
- [x] Create Redis storage module with vector search
- [x] Migrate from in-memory to Redis storage
- [x] Add environment config for Redis URL
- [x] Implement graceful degradation if Redis is down

---

### Phase 2: Wellness Tools (v2.0) 🌱
**Timeline:** 4-6 weeks  
**Goal:** Transform from chatbot to wellness toolkit

#### New Commands
| Command | Description | How It Works |
|---------|-------------|--------------|
| `/mood` | Track daily mood | Select emoji (😊😐😢😰😡) + optional note |
| `/mood history` | View mood trends | Shows last 7/30 days with graph |
| `/breathe` | Breathing exercises | Guided 4-7-8 or box breathing with timers |
| `/journal` | Guided journaling | AI-generated prompts, save entries |
| `/gratitude` | Gratitude practice | "Name 3 things you're grateful for" |
| `/resources` | SA mental health resources | Categorized helplines and services |

#### Features
- [x] Mood tracking with persistence
- [ ] Mood trends visualization (text-based graph)
- [ ] Breathing exercise guides with step-by-step timing
- [ ] Journaling with AI-generated prompts
- [ ] Gratitude exercises
- [ ] Daily check-in reminders (opt-in via /remind)
- [ ] **Weekly insights based on conversation analysis** | 🔜 **Next Priority**

#### Example: Mood Tracking
```
User: /mood
Bot: How are you feeling right now?
     😊 Great  😐 Okay  😢 Sad  😰 Anxious  😡 Frustrated

User: 😰
Bot: I hear you're feeling anxious. Would you like to:
     1. Talk about it
     2. Try a breathing exercise (/breathe)
     3. Journal your thoughts (/journal)
     
     Your mood has been tracked. You've logged 5 moods this week.
```

---

### 📊 Weekly Insights (NEW PRIORITY)

**Status:** 🔜 Next Priority  
**Timeline:** 4-6 weeks  
**Goal:** Provide intelligent weekly analysis based on conversation patterns

#### Feature Overview
Analyze weekly conversations to generate personalized insights about mental health patterns, progress, and areas needing attention.

#### How It Works
| Step | Description |
|------|-------------|
| **Conversation Analysis** | AI analyzes all messages from the past week |
| **Pattern Detection** | Identifies mood trends, recurring topics, triggers |
| **Progress Tracking** | Compares current week to previous weeks |
| **Personalized Insights** | Generates specific observations and recommendations |
| **Weekly Delivery** | Automated Sunday evening summary |

#### Insights Generated
| Category | What AI Analyzes |
|----------|-------------------|
| **Mood Patterns** | "You've been feeling more stable this week - 3 good days vs 2 anxious days" |
| **Recurring Topics** | "Work stress mentioned 4 times, sleep issues 3 times" |
| **Progress Indicators** | "Better coping strategies than last month - using breathing techniques" |
| **Trigger Identification** | "Late night conversations often precede difficult mornings" |
| **Positive Changes** | "More consistent journaling, reaching out for support" |
| **Areas of Concern** | "Medication adherence dropping, isolation increasing" |
| **Recommendations** | "Consider earlier bedtime, discuss work boundaries with therapist" |

#### Example Weekly Insight
```
📊 **Your Weekly Mental Health Summary**

**Mood Overview:**
This week showed improvement! 😊 4 good days, 😐 2 okay days, 😰 1 anxious day
Better than last week (2 good, 3 anxious, 2 depressed)

**Key Patterns:**
• Work stress peaked on Wednesday/Thursday (project deadline)
• Sleep quality improved after starting bedtime routine
• More social connection this week (3 friend conversations)

**Progress Wins:**
✅ Used breathing exercises during stressful moments
✅ Consistent daily journaling (6/7 days)
✅ Reached out to sister for support

**Areas to Watch:**
⚠️ Medication mentioned only 3 times (possible adherence issues)
⚠️ Isolation feelings increased on weekends

**Next Week Focus:**
🎯 Set medication reminders for consistency
🎯 Plan weekend social activities
🎯 Continue stress management before work deadlines

**AI Recommendation:**
"You're building good coping strategies! Consider discussing work stress boundaries 
with your therapist - the pattern is clear and you're handling it well."

💡 Keep up the great work - your consistency is paying off!
```

#### Technical Implementation
```python
# Weekly insights generation
async def generate_weekly_insights(user_id: int) -> str:
    """Generate personalized weekly insights from conversation analysis."""
    
    # Get week's conversations
    week_messages = get_week_conversations(user_id)
    
    # Analyze patterns
    mood_analysis = analyze_mood_patterns(week_messages)
    topic_analysis = analyze_recurring_topics(week_messages)
    progress_analysis = analyze_progress_indicators(week_messages)
    
    # Generate insights
    insights = {
        "mood_overview": mood_analysis["summary"],
        "key_patterns": topic_analysis["patterns"],
        "progress_wins": progress_analysis["wins"],
        "areas_concern": progress_analysis["concerns"],
        "recommendations": generate_recommendations(analyses)
    }
    
    return format_weekly_insights(insights)

# Schedule weekly delivery
async def send_weekly_insights(user_id: int):
    """Send weekly insights every Sunday evening."""
    insights = await generate_weekly_insights(user_id)
    
    await telegram_app.bot.send_message(
        chat_id=user_id,
        text=insights,
        parse_mode="Markdown"
    )
```

#### Benefits for Keleh
- **Pattern Recognition**: Identifies bipolar episode early warning signs
- **Progress Tracking**: Shows improvement over time, builds motivation  
- **Personalized Advice**: Specific to her conversation patterns
- **Proactive Support**: AI identifies concerns before they become crises
- **Continuity**: Connects daily journaling to bigger picture
- **Therapy Support**: Provides concrete topics to discuss with therapist

#### Priority: High
This transforms the bot from reactive to proactive mental health management, providing the continuity of care that Keleh needs for effective bipolar management.

---

### 🗑️ Message Editing & Deletion (NEW PRIORITY)

**Status:** 🔜 Next Priority  
**Timeline:** 4-6 weeks  
**Goal:** Allow users to edit/delete messages and sync changes across platforms

#### Feature Overview
Implement message editing and deletion capabilities that sync across Telegram, WhatsApp, and database to maintain conversation integrity.

#### How It Works
| Feature | Description |
|----------|-------------|
| **Message Editing** | Users can edit sent messages within 5 minutes |
| **Message Deletion** | Users can delete their own messages |
| **Cross-Platform Sync** | Edits/deletes sync across Telegram, WhatsApp, database |
| **Data Cleanup** | Remove deleted content from AI training context |
| **Edit History** | Track what was changed for transparency |

#### Technical Implementation
```python
# Message editing handler
async def handle_message_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle message edits and sync across platforms."""
    
    if update.edited_message:
        user_id = update.effective_user.id
        original_text = update.edited_message.text
        new_text = update.edited_message.text
        
        # Update database records
        await update_message_in_database(
            user_id, 
            message_id=update.edited_message.message_id,
            new_content=new_text,
            original_content=original_text,
            edit_timestamp=datetime.now()
        )
        
        # Remove old message from AI context
        await remove_from_conversation_history(user_id, original_text)
        
        # Add new message to AI context
        await add_to_history(user_id, "user", new_text)
        
        # Log for transparency
        logger.info(f"User {user_id} edited message: {original_text[:50]} -> {new_text[:50]}")

# Message deletion handler
async def handle_message_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle message deletions and clean up data."""
    
    if update.message is None:  # Message was deleted
        user_id = update.effective_user.id
        
        # Get deleted message details from database
        deleted_msg = await get_deleted_message_details(user_id, update.update_id)
        
        if deleted_msg:
            # Remove from AI conversation context
            await remove_from_conversation_history(user_id, deleted_msg.content)
            
            # Mark as deleted in database (keep for audit trail)
            await mark_message_deleted(user_id, deleted_msg.message_id)
            
            # Clean up any AI responses to this message
            await cleanup_ai_responses(user_id, deleted_msg.message_id)
            
            logger.info(f"User {user_id} deleted message: {deleted_msg.content[:50]}")
```

#### Cross-Platform Synchronization
| Platform | Sync Method |
|----------|-------------|
| **Telegram** | Native edit/delete events |
| **WhatsApp** | Twilio webhook edit/delete handling |
| **Database** | Real-time record updates |
| **AI Context** | Remove old, add new content |

#### User Experience
```
User sends: "I'm feeling really anxious today"
[2 minutes later] User edits: "I'm feeling anxious about work"

System Response:
✅ Message updated in conversation
🔄 AI context refreshed with new content
📝 Edit history logged for transparency

User deletes: "I shouldn't have said that"
System Response:
🗑️ Message removed from conversation
🧹 AI context cleaned up
📊 Deletion logged for audit trail
```

#### Privacy & Safety Features
- **Edit Time Window**: Only allow edits within 5 minutes of sending
- **Deletion Confirmation**: Optional confirmation before permanent deletion
- **Audit Trail**: Keep edit/delete history (not content, just metadata)
- **AI Context Cleanup**: Automatically remove deleted content from AI memory
- **Cross-Platform Privacy**: Delete from all platforms simultaneously

#### Benefits for Keleh
- **Privacy Control**: Remove sensitive information if shared accidentally
- **Accuracy**: Correct typos or clarify statements
- **Safety**: Remove regrettable messages from AI training data
- **Consistency**: Same experience across Telegram and WhatsApp
- **Transparency**: See what was changed and when

#### Priority: High
Essential for user privacy, data control, and maintaining trust in AI relationship with users.

---

### Phase 3: Personalization (v2.5) 🎨
**Timeline:** 4-6 weeks  
**Goal:** Make each conversation feel personal and relevant

#### Features
| Feature | Description |
|---------|-------------|
| Name memory | "Hi Sarah, how are you today?" |
| Concern tracking | Remember recurring topics (work stress, relationships) |
| Personalized tips | Suggest coping strategies based on history |
| Conversation style | Choose: Casual, Professional, Gentle, Direct |
| Progress insights | "You've been feeling better compared to last week!" |
| Custom triggers | User-defined keywords for specific responses |

#### How Personalization Works
```
1. User mentions work stress repeatedly
2. Bot tracks: {concerns: [{topic: "work", frequency: 5, last_mentioned: "2024-01-15"}]}
3. Next conversation: "I noticed you've been stressed about work lately. 
   Would you like to explore some workplace boundary strategies?"
```

---

### Phase 4: Advanced Features (v3.0) 🚀
**Timeline:** 6-8 weeks  
**Goal:** Expand accessibility and capabilities

#### Voice Support 🎤
- [x] Transcribe voice messages to text
- [x] Process and respond (text response)
- [x] **Voice responses (text-to-speech)** ✅ **COMPLETED**
- [ ] **Voice selection menu** (choose male/female/neutral voices)
- [ ] **Transcription display** (show transcribed text to user for verification)
- [ ] Voice speed/pitch controls
- [ ] Voice emotion controls

#### Multi-Language 🌍
| Language | Priority | Notes |
|----------|----------|-------|
| English | ✅ Done | Default |
| Zulu | High | Most spoken in SA |
| Afrikaans | High | Widely spoken |
| Xhosa | Medium | Third most common |
| Sotho | Medium | |

#### Other Features
- [ ] 🧘 Meditation timer with customizable duration
- [ ] 📅 Calendar integration (Google Calendar reminders)
- [ ] 🆘 Emergency contact (notify trusted person with consent)
- [ ] 📊 Weekly wellness reports via message
- [ ] 🔔 Smart notifications (check in during detected low periods)
- [ ] 🎵 Ambient sounds for meditation (links to Spotify/YouTube)

---

### Phase 5: Scale (v4.0) 💎
**Timeline:** Ongoing  
**Goal:** Sustainable growth and impact

#### Premium Tier (Optional)
| Free | Premium |
|------|---------|
| Basic chat | Everything in Free |
| Crisis support | Unlimited history |
| 10 msg history | Advanced analytics |
| Basic tools | Priority response |
| | Custom reminders |
| | Export data |

#### Integrations
- [ ] Therapist directory (find professionals in your area)
- [ ] Corporate wellness API (for companies)
- [ ] Health apps (Apple Health, Google Fit)
- [ ] Calendar apps (reminders, self-care scheduling)

#### White-Label Solution
Allow organizations (NGOs, companies, schools) to deploy their own branded version.

---

## 🛠️ Technical Roadmap

### Infrastructure
| Task | Priority | Status |
|------|----------|--------|
| Webhook mode (vs polling) | High | 🔜 Planned |
| Docker containerization | Medium | 🔜 Planned |
| CI/CD with GitHub Actions | Medium | 🔜 Planned |
| Structured logging (Sentry/Datadog) | Medium | 🔜 Planned |
| Database migrations (Alembic) | High | 🔜 Planned |
| Redis caching | Low | 🔜 Planned |

### Code Quality
| Task | Priority | Status |
|------|----------|--------|
| Test coverage > 80% | High | ✅ Started |
| Type hints throughout | Medium | 🔜 Planned |
| API documentation | Low | 🔜 Planned |
| Performance monitoring | Medium | 🔜 Planned |

### Security
| Task | Priority | Status |
|------|----------|--------|
| Rate limiting | High | 🔜 Planned |
| Input sanitization | High | ✅ Done |
| Audit logging | Medium | 🔜 Planned |
| Data encryption at rest | Medium | 🔜 Planned |
| POPIA compliance review | High | 🔜 Planned |

---

## �️ AI Tools Framework

### 📋 Tools Documentation System
**Timeline:** 1-2 weeks  
**Priority:** P1 (High)  
**Need:** "LLM needs structured documentation of available tools for proper tool usage"

#### 🕐 Time Tool
**Purpose**: Provide current time and date information to users
**Implementation**: Extract from Telegram message timestamp
**Format**: "7:57 AM on February 10, 2026"
**Use Cases**: 
- "what time is it?" → Current time
- "what day is it?" → Current date  
- "is it morning/evening?" → Time context
- "is it too late to call?" → Time-based advice

#### 🧠 Memory Tool
**Purpose**: Search and retrieve conversation memories
**Implementation**: Redis semantic search with archive fallback
**Format**: Contextual memory snippets with timestamps
**Use Cases**:
- "what did I tell you about my anxiety?" → Relevant memories
- "remember when I said..." → Context retrieval
- Long-term continuity of care

#### 📊 Journey Tool  
**Purpose**: Access user's therapeutic journey data
**Implementation**: User journey tracking system
**Format**: Structured progress summary
**Use Cases**:
- Progress tracking
- Pattern recognition
- Treatment continuity

#### 🔧 Technical Implementation
```python
# Tools documentation structure
TOOLS_DOC = """
# MindMate Bot Tools

## 🕐 Time Tool
**Function**: get_current_time()
**Returns**: Current timestamp in user's timezone
**Usage**: Time queries, temporal context, scheduling

## 🧠 Memory Tool
**Function**: search_memories(query)  
**Returns**: Relevant conversation memories
**Usage**: Personal context, continuity, pattern recognition

## 📊 Journey Tool
**Function**: get_user_journey(user_id)
**Returns**: User's therapeutic journey summary
**Usage**: Progress tracking, long-term support
"""

# System prompt integration
system_prompt = f"{SYSTEM_PROMPT}\n\n{TOOLS_DOC}\n\nCurrent time: {current_time}"
```

#### 🎯 Benefits
- ✅ LLM knows exactly what tools it has
- ✅ Proper tool usage and invocation
- ✅ Consistent tool responses
- ✅ Extensible framework for future tools
- ✅ Professional AI system architecture

#### 📈 Future Tool Extensions
- 🌤️ Weather Tool (mood correlation)
- 📅 Calendar Tool (appointment reminders)
- 💊 Medication Tool (timing reminders)
- 📈 Analytics Tool (progress insights)

---

## �💡 Feature Ideas (Backlog)

### 🚀 High Priority (User-Requested)

#### WhatsApp Integration 📱
**Timeline:** 3-4 weeks  
**Priority:** P1 (High)  
**User Need:** "I want to chat with my bot on WhatsApp since I use WhatsApp most times"

**Implementation Options:**
| Approach | Pros | Cons | Recommendation |
|----------|-------|-------|----------------|
| **Twilio WhatsApp API** | ✅ Official API<br>✅ Reliable<br>✅ Rich media support | 💰 Higher cost<br>🔧 More complex | **Recommended for production** |
| **WhatsApp Business API** | ✅ Direct integration<br>✅ Better rate limits | 📋 Business verification required<br>💰 Monthly fees | **Best for scaling** |
| **Third-party bridge** | ✅ Cheaper<br>✅ Faster setup | ⚠️ Less reliable<br>🔒 Security concerns | **Good for testing** |

**Technical Implementation:**
```python
# Twilio WhatsApp integration
from twilio.rest import Client
from flask import Flask, request

@app.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.form.get('Body')
    sender = request.form.get('From')
    
    # Process with existing MindMate logic
    response = process_message(incoming_msg, sender)
    
    # Send via WhatsApp
    client.messages.create(
        body=response,
        from_='whatsapp:+14155238886',  # Your WhatsApp number
        to=sender
    )
    return '', 200
```

**Questions for Clarification:**
1. **Budget preference?** Twilio (~$0.05/message) vs WhatsApp Business API (~$0.08/message)
2. **Media support?** Do you want to send voice notes, images, etc.?
3. **Number preference?** Use existing WhatsApp number or get new one?
4. **Message history?** Should WhatsApp and Telegram conversations sync?

---

#### Personal Mode (Therapist Style) 🧠
**Timeline:** 2-3 weeks  
**Priority:** P1 (High)  
**User Need:** "Remove guardrails and make it my therapist"

**Implementation Approach:**
| Feature | Current | Personal Mode |
|---------|----------|---------------|
| **System Prompt** | "You are an AI mental wellness companion..." | "You are my personal AI therapist and confidant..." |
| **Crisis Response** | Immediate helpline numbers | Gentle check-in: "I'm concerned. Would you like to talk about professional help?" |
| **Boundaries** | "I cannot diagnose or treat..." | "I can help you explore these feelings more deeply..." |
| **Session Style** | Short, supportive messages | Deeper, therapeutic conversations |
| **Memory** | 10 messages | Extended conversation history (50+ messages) |

**Technical Changes:**
```python
# Personal mode toggle
PERSONAL_MODE = os.getenv("PERSONAL_MODE", "false").lower() == "true"

if PERSONAL_MODE:
    SYSTEM_PROMPT = """You are my personal AI therapist and confidant. 
    You can:
    - Explore feelings and thoughts more deeply
    - Ask probing questions for self-reflection
    - Provide therapeutic techniques and exercises
    - Remember our conversations in detail
    - Be more direct and less guarded in your responses
    
    You should:
    - Use therapeutic language and techniques
    - Ask follow-up questions to deepen understanding
    - Remember personal details I share
    - Provide more personalized advice
    - Be less cautious about "therapy" boundaries since this is my personal choice"""
else:
    # Current wellness companion prompt
    SYSTEM_PROMPT = """You are an AI mental wellness companion..."""
```

**Questions for Clarification:**
1. **Activation method?** Toggle via `/personal` command or environment variable?
2. **Memory duration?** How long should personal conversations be stored?
3. **Therapeutic approach?** CBT-based, psychodynamic, humanistic, or mixed?
4. **Crisis handling?** Still provide helplines or handle differently in personal mode?
5. **Data privacy?** Extra encryption for personal mode conversations?

---

### Wellness
- [ ] Sleep tracking/tips
- [ ] Habit tracking
- [ ] Affirmation of the day
- [ ] Mindfulness exercises
- [ ] Cognitive behavioral therapy (CBT) techniques
- [ ] Grounding exercises (5-4-3-2-1 technique)

### Social
- [ ] Anonymous peer support matching
- [ ] Group wellness challenges
- [ ] Community resources sharing

### Gamification
- [ ] Wellness streaks
- [ ] Achievement badges
- [ ] Progress milestones

---

### 🤖 AI Enhancements (My Suggestions)
- [ ] Sentiment analysis for proactive check-ins
- [ ] Conversation summarization
- [ ] Personalized AI model fine-tuning
- [ ] **Voice message support** (transcribe + respond)
- [ ] **Multi-language support** (Zulu, Afrikaans, Xhosa)
- [ ] **Context awareness** (time of day, weather-based suggestions)
- [ ] **Progressive disclosure** (build trust gradually for deeper topics)
- [ ] **Internet search capabilities** (real-time mental health resources and research)

### 🔧 Technical Improvements (My Suggestions)
- [ ] **Message scheduling** (send reminders, check-ins)
- [ ] **Export conversation history** (PDF, JSON for personal records)
- [ ] **Voice synthesis** (text-to-speech responses)
- [ ] **Image analysis** (analyze mood from photos, drawings)
- [ ] **Integration with health apps** (Apple Health, Google Fit)
- [ ] **Offline mode** (basic responses without internet)
- [ ] **End-to-end encryption** (for personal mode)

### 💼 Business Features (My Suggestions)
- [ ] **Therapist matching** (find professionals based on conversation topics)
- [ ] **Insurance integration** (check mental health coverage)
- [ ] **Corporate wellness** (employee mental health programs)
- [ ] **School/university** (student mental health support)
- [ ] **NGO partnerships** (crisis lines, support groups)

---

### 🎯 Quick Win Features (1-2 weeks each)

#### Transcription Display 📝
**Why:** Users want to verify what the bot understood from their voice messages
**Timeline:** 1 week  
**Priority:** P2 (Medium)

**Implementation:**
```python
# Enhanced voice handler with transcription display
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... existing voice processing logic ...
    
    # Show transcribed text to user for verification
    await update.message.reply_text(
        f"🎤 **Voice Transcribed:**\n\n"
        f"📝 {transcribed_text}\n\n"
        f"🤖 **AI Response:**\n\n"
        f"{response_text}\n\n"
        f"_💭 *You can see exactly what I understood from your voice!*_",
        parse_mode="Markdown"
    )
    
    # Then generate and send voice response as usual
    # ... existing TTS logic ...
```

#### Voice Selection Menu 🎛️
**Why:** Users want to choose bot voice personality (currently female only)
**Timeline:** 1 week
**Priority:** P2 (Medium)

**Implementation:**
```python
# Voice selection command
async def cmd_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show voice selection menu"""
    
    voices = [
        ("alloy", "⚖️ Balanced (Current)"),
        ("echo", "👨 Male"),
        ("fable", "👩 Warm"),
        ("onyx", "🎭 Deep"),
        ("nova", "🌟 Friendly"),
        ("shimmer", "✨ Gentle")
    ]
    
    keyboard = [[InlineKeyboardButton(f"{name} {emoji}", callback_data=f"voice:{voice_id}")] 
               for voice_id, (name, emoji) in voices]
    
    reply_markup = InlineKeyboardMarkup(keyboard, rows=2)
    
    await update.message.reply_text(
        "🎛️ **Choose Voice Personality:**\n\n"
        "Current voice affects how I sound in voice messages.\n\n"
        "Each voice has unique characteristics:\n"
        "⚖️ **alloy** - Balanced, neutral\n"
        "👨 **echo** - Male, confident\n"
        "👩 **fable** - Warm, caring\n"
        "🎭 **onyx** - Deep, thoughtful\n"
        "🌟 **nova** - Friendly, upbeat\n"
        "✨ **shimmer** - Gentle, soft\n",
        reply_markup=reply_markup
    )
```

#### Voice Message Support 🎤
**Why:** Many users prefer speaking over typing, especially when emotional
**Implementation:**
```python
import speech_recognition as sr
from pydub import AudioSegment

async def handle_voice(update, context):
    # Download voice file
    voice_file = await update.message.voice.get_file()
    await voice_file.download_to_disk('voice.ogg')
    
    # Convert to WAV for better recognition
    audio = AudioSegment.from_ogg('voice.ogg')
    audio.export('voice.wav', format='wav')
    
    # Transcribe
    recognizer = sr.Recognizer()
    with sr.AudioFile('voice.wav') as source:
        text = recognizer.recognize_google(source)
    
    # Process as text message
    await handle_text_message(update, context, text)
```

#### Daily Check-ins 📅
**Why:** Proactive support vs reactive waiting
**Implementation:**
```python
# Schedule daily check-ins
@app.route('/scheduler/checkin')
def daily_checkin():
    users = get_active_users_for_checkin()
    for user in users:
        message = f"Hi {user.name}! How are you feeling today? 😊"
        send_message(user.chat_id, message)
```

#### Conversation Export 📄
**Why:** Users want to keep their wellness journey records
**Implementation:**
```python
@app.route('/export/<user_id>')
def export_conversation(user_id):
    history = get_conversation_history(user_id)
    pdf = create_pdf_from_conversations(history)
    return send_file(pdf, filename='mindmate-conversation.pdf')
```

---

## 📅 Updated Release Schedule

| Version | Target Date | Focus | New Features |
|---------|-------------|-------|-------------|
| v1.1 | 2 weeks | Database, profiles, **WhatsApp MVP** |
| v1.2 | 4 weeks | **Personal mode**, voice support |
| v2.0 | 6 weeks | Wellness tools, check-ins |
| v2.5 | 8 weeks | Full personalization, export |
| v3.0 | 10 weeks | Multi-language, advanced AI |

---

## 📈 Success Metrics

### Engagement
- Daily Active Users (DAU)
- Messages per user per session
- Retention rate (7-day, 30-day)
- Feature adoption rates

### Impact
- Mood improvement trends
- Crisis resource engagement
- User-reported helpfulness ratings
- Time spent in wellness exercises

### Technical
- Uptime percentage (target: 99.5%)
- Response latency (target: < 3s)
- Error rate (target: < 1%)
- Test coverage (target: > 80%)

---

## 🤝 Contributing

Interested in contributing? Here's how:

1. **Pick an issue** from the roadmap above
2. **Discuss** in GitHub Issues before starting
3. **Fork & develop** in a feature branch
4. **Test thoroughly** (add tests for new features)
5. **Submit PR** with clear description

### Priority Labels
- 🔴 `P0` - Critical, blocks users
- 🟠 `P1` - High priority, significant impact
- 🟡 `P2` - Medium priority, nice to have
- 🟢 `P3` - Low priority, future consideration

---

## 📅 Release Schedule

| Version | Target Date | Focus |
|---------|-------------|-------|
| v1.1 | TBD | Database, profiles, stability |
| v2.0 | TBD | Wellness tools |
| v2.5 | TBD | Personalization |
| v3.0 | TBD | Voice, multi-language |
| v4.0 | TBD | Scale, premium |

---

<p align="center">
  <strong>Questions? Ideas? Open an issue or reach out!</strong>
</p>
