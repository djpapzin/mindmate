# 🗺️ MindMate Roadmap

This document outlines the vision, planned features, and development priorities for MindMate.

---

## 🎯 Vision

**MindMate aims to be a comprehensive AI-powered mental wellness companion that provides 24/7 personalized support.**

Available on **Telegram and WhatsApp**, with a **Premium Personal Mode** that acts as your dedicated AI therapist - no generic disclaimers, no deflecting to helplines, just real support.

---

## 🔥 Priority Features (Brainstorm)

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

| Feature | Description |
|---------|-------------|
| **No AI Disclaimers** | Removes "As an AI..." and robotic responses |
| **No Helpline Redirects** | Direct support instead of deflecting to hotlines |
| **Direct Personalized Advice** | Therapist-style guidance, not generic tips |
| **Focus Areas Config** | User sets their specific challenges |
| **Memory Across Sessions** | Remembers your history, patterns, progress |
| **Private by Default** | Locked to specific user IDs |

**Business Model:**
- Free tier: Standard MindMate (with guardrails)
- Premium tier: Personal Mode (subscription - future)

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
| **Voice Input** | `whisper-1` | Fastest (857ms), most reliable |
| **Voice Output** | `tts-1` | Natural, human-like, $0.015/min |

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
- [ ] Set up PostgreSQL on Render (free tier)
- [ ] Create user and message models
- [ ] Migrate from in-memory to database storage
- [ ] Add environment config for database URL
- [ ] Implement graceful degradation if DB is down

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
- [ ] Mood tracking with persistence
- [ ] Mood trends visualization (text-based graph)
- [ ] Breathing exercise guides with step-by-step timing
- [ ] Journaling with AI-generated prompts
- [ ] Gratitude exercises
- [ ] Daily check-in reminders (opt-in via /remind)
- [ ] Weekly mood summary

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
- [ ] Transcribe voice messages to text
- [ ] Process and respond (text response)
- [ ] Future: Voice responses (text-to-speech)

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

## 💡 Feature Ideas (Backlog)

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
