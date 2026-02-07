# 📁 MindMate Project Structure

## 📂 Directory Overview

```
mindmate/
├── 📁 src/                    # Source code
│   ├── 🤖 bot.py             # Main bot application (voice ✅)
│   ├── 🗄️ database.py        # PostgreSQL connection & models
│   └── 📄 config.py           # Configuration constants
├── 📋 requirements.txt          # Python dependencies
├── 🐳 Dockerfile              # Container configuration
├── 📄 Procfile               # Render deployment config
├── 📄 render.yaml            # Render service settings
├── 📄 .env.example           # Environment variables template
├── 📄 .gitignore             # Git ignore patterns
├── 📚 docs/                  # Documentation
│   ├── ARCHITECTURE.md      # System design
│   ├── POSTGRESQL_INTEGRATION_CHECKLIST.md
│   └── 📁 voice/             # Voice feature documentation
│       └── VOICE_IMPLEMENTATION_TODO.md   # Voice implementation checklist
├── 🔬 research/               # Research findings
│   ├── MODEL_RESEARCH_FINDINGS.md
│   ├── CHATGPT_RESEARCH_FINDINGS.md
│   ├── GEMINI_RESEARCH_FINDINGS.md
│   └── OPENAI_DIRECT_AUDIO_RESEARCH.md
├── 📝 scripts/               # Utility scripts
│   ├── test_voice.py        # Voice testing utilities
│   └── test_bot.py          # Core bot functionality tests
├── 📊 logs/                  # Application logs
└── 🗂️ .windsurf/           # IDE configuration
```

## 📁 Core Files

### 🤖 `src/bot.py`
**Purpose**: Main bot application with FastAPI + Telegram integration
**Key Features**:
- ✅ **Voice Messages**: Transcribe + respond with voice
- ✅ **Personal Mode**: Therapeutic conversations
- ✅ **Crisis Detection**: Immediate helpline resources
- ✅ **Command Menu**: User-friendly interface
- ✅ **Conversation History**: Persistent memory

**Voice Implementation**:
```python
# Voice processing constants
VOICE_TRANSCRIPTION_MODEL = "whisper-1"
VOICE_TTS_MODEL = "tts-1"

# Voice handler
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Download voice → Transcribe with Whisper → Process with GPT → Generate TTS → Send voice
```

### 🗄️ `src/database.py`
**Purpose**: PostgreSQL connection and data models
**Features**:
- User profiles and preferences
- Conversation history storage
- Voice selection persistence
- Graceful fallback to in-memory

### 📋 `requirements.txt`
**Key Dependencies**:
```
python-telegram-bot==21.0      # Telegram bot framework
openai>=1.12.0,<2.0.0        # OpenAI API (Whisper + GPT + TTS)
python-dotenv                   # Environment variables
fastapi                         # Web framework
uvicorn[standard]              # ASGI server
aiofiles>=23.0.0,<24.0.0    # Async file operations for voice
asyncpg                        # PostgreSQL driver
pydantic                        # Data validation
```

## 🚀 Deployment

### 🌐 Render Configuration
- **Platform**: Render.com (free tier)
- **Architecture**: FastAPI + Uvicorn + Webhook mode
- **Database**: PostgreSQL (free tier)
- **Webhook**: `https://mindmate-dev.onrender.com/webhook`

### 🐳 Container Support
- **Base**: Python 3.12 slim
- **Process**: Single `python src/bot.py` command
- **Port**: 10000 (Render standard)

## 📚 Documentation

### 📋 Core Docs
- **README.md**: Project overview and setup
- **ARCHITECTURE.md**: System design and patterns
- **ROADMAP.md**: Feature planning and timeline

### 🔬 Research Docs
- **MODEL_RESEARCH_FINDINGS.md**: AI model evaluation and selection
- **OPENAI_DIRECT_AUDIO_RESEARCH.md**: Direct audio-to-audio model research

### 📝 Implementation Docs
- **VOICE_IMPLEMENTATION_TODO.md**: Voice feature implementation checklist → **docs/voice/**
- **VOICE_ERROR_ANALYSIS.md**: Voice debugging and fixes → **docs/voice/**

## 🎯 Current Status

### ✅ **Completed Features**
- [x] **Voice Messages**: Full voice-to-voice conversation
- [x] **Personal Mode**: Therapeutic AI conversations
- [x] **Crisis Detection**: Automatic resource provision
- [x] **Command Menu**: Enhanced UX with emoji labels
- [x] **Conversation History**: PostgreSQL + in-memory fallback

### 🚧 **Current Limitations**
- [ ] **Voice Selection**: Currently only female voice (alloy)
- [ ] **Voice Controls**: No speed/pitch/emotion adjustments
- [ ] **Multi-language**: English only

### 🎛️ **Next: Voice Selection**
**Priority**: P2 (Medium)
**Timeline**: 1 week
**Goal**: Allow users to choose voice personality

**Available Voices**:
- ⚖️ **alloy** (current) - Balanced, neutral
- 👨 **echo** - Male, confident
- 👩 **fable** - Warm, caring
- 🎭 **onyx** - Deep, thoughtful
- 🌟 **nova** - Friendly, upbeat
- ✨ **shimmer** - Gentle, soft

---

**Last Updated**: 2026-02-07  
**Version**: v1.2 (Voice Support Complete)
