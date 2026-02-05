# 🗺️ MindMate Roadmap

This document outlines the vision, planned features, and development priorities for MindMate.

---

## 🎯 Vision

**MindMate aims to be the most accessible, empathetic, and effective AI-powered mental wellness companion for South Africans.**

Our goal is to provide 24/7 support that bridges the gap between feeling overwhelmed and accessing professional help - while always encouraging users to seek professional support when needed.

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

### ⚠️ Current Limitations
| Limitation | Impact | Planned Fix |
|------------|--------|-------------|
| In-memory storage | History lost on redeploy | Phase 1: Add database |
| No user profiles | Can't remember names/preferences | Phase 1: User profiles |
| English only | Excludes non-English speakers | Phase 4: Multi-language |
| Text only | Can't process voice messages | Phase 4: Voice support |
| No analytics | Can't measure impact | Phase 1: Analytics |

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

Ideas to consider for future phases:

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

### AI Enhancements
- [ ] Sentiment analysis for proactive check-ins
- [ ] Conversation summarization
- [ ] Personalized AI model fine-tuning

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
