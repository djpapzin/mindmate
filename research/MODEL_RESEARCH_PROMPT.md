# AI Model Research Prompt for MindMate

## 🎯 Research Objective

Conduct comprehensive research to determine the optimal OpenAI model(s) for **MindMate** - a personal mental wellness chatbot that acts as a private AI therapist.

---

## 📋 Project Context

### What is MindMate?
A Telegram/WhatsApp chatbot providing 24/7 mental wellness support with:
- Personalized therapeutic conversations (not generic AI responses)
- Focus areas: Relationships, Finances, Bipolar management, Anxiety, Depression
- Memory across sessions (remembers user's history, patterns, progress)
- Voice message support (input & output)
- No corporate AI guardrails (no "As an AI, I cannot..." responses)
- Direct advice like a real therapist would give

### Target User
- Primary: Single power user (the developer) wanting a private AI therapist
- Future: Subscription model for other users wanting personalized mental health support

### Current Setup
- Platform: Telegram (WhatsApp coming via Twilio)
- Current model: `gpt-3.5-turbo`
- Hosting: Render (free tier)
- Budget: $2,500.95 OpenAI credits available

---

## 🔍 Models to Research

### Primary Chat Models (Compare These)
```
GPT-5 Series:
- gpt-5.2
- gpt-5.2-pro
- gpt-5.2-chat-latest
- gpt-5
- gpt-5-pro
- gpt-5-mini
- gpt-5-nano

GPT-4 Series:
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-4.1
- gpt-4.1-mini

GPT-3.5:
- gpt-3.5-turbo (current baseline)
```

### Reasoning Models (Evaluate if useful)
```
- o3
- o3-mini
- o4-mini
- o1
- o1-pro
```

### Voice Models
```
Speech-to-Text:
- whisper-1
- gpt-4o-transcribe
- gpt-4o-mini-transcribe

Text-to-Speech:
- tts-1
- tts-1-hd
- gpt-4o-mini-tts
```

---

## 📊 Evaluation Criteria

### 1. Emotional Intelligence & Empathy
- How well does the model understand emotional nuance?
- Can it provide warm, human-like therapeutic responses?
- Does it avoid cold, robotic, or dismissive language?
- How does it handle sensitive topics (depression, anxiety, relationship issues)?

### 2. Personalization Capability
- Can it maintain consistent personality across conversations?
- How well does it adapt to user's communication style?
- Can it remember and reference context from earlier in conversation?

### 3. Guardrail Flexibility
- Which models are more/less restrictive about mental health topics?
- Can the model give direct advice vs deflecting to "see a professional"?
- How does each model handle requests for personal opinions?

### 4. Response Quality
- Coherence and depth of therapeutic responses
- Ability to ask good follow-up questions
- Balance between listening and providing guidance

### 5. Cost Efficiency
- Price per 1K input tokens
- Price per 1K output tokens
- Estimated cost per typical conversation (500-1000 tokens)
- Cost comparison table for all models

### 6. Speed & Latency
- Response time for typical queries
- Impact on user experience
- Streaming support

### 7. Context Window
- Maximum tokens supported
- How many conversation turns can it remember?
- Implications for "memory across sessions" feature

### 8. Voice Capabilities
- Quality of transcription (whisper vs alternatives)
- Naturalness of TTS output
- Latency for voice interactions

---

## 🔬 Research Sources to Consult

### Official Sources
- OpenAI documentation and model cards
- OpenAI API pricing page
- OpenAI community forums
- OpenAI changelog/release notes

### Community & Reviews
- Reddit: r/OpenAI, r/ChatGPT, r/LocalLLaMA, r/MachineLearning
- Twitter/X discussions from AI researchers
- Hacker News threads
- YouTube comparisons and benchmarks

### Benchmarks & Papers
- Chatbot Arena / LMSYS leaderboard
- Academic papers on LLM empathy/emotional intelligence
- Stanford HELM benchmarks
- Any mental health chatbot specific research

### Real-World Use Cases
- How are other mental health apps using these models?
- Case studies from therapy/wellness chatbots
- Developer experiences shared in blogs/forums

---

## 📝 Deliverables Requested

### 1. Model Comparison Matrix
Create a table comparing all models across:
| Model | Empathy Score | Cost/1K tokens | Context Window | Speed | Guardrails | Best For |

### 2. Top 3 Recommendations
For each recommendation, provide:
- Model name
- Why it's recommended
- Pros and cons
- Estimated monthly cost for personal use (~100 conversations/month)
- Any configuration tips

### 3. Model Tiering Strategy
Suggest which models to use for:
- Free tier users (cost-conscious)
- Standard users
- Premium/Personal mode (quality-focused)

### 4. Voice Model Recommendations
Best combination for:
- Voice input (transcription)
- Voice output (TTS)
- Cost vs quality tradeoffs

### 5. Cost Projections
Estimate monthly costs for:
- Light use (50 conversations/month)
- Medium use (200 conversations/month)
- Heavy use (500+ conversations/month)

### 6. Implementation Notes
- Any special prompting techniques for therapeutic use
- System prompt recommendations
- Temperature/parameter settings for empathetic responses
- Known issues or limitations to watch for

---

## ⚠️ Special Considerations

### Mental Health Context
- The chatbot deals with sensitive topics (suicide ideation, self-harm, depression)
- Need models that can be supportive without being dismissive
- Crisis detection is handled separately (keyword-based), but model should still be appropriate

### Personal Use Priority
- This is primarily for ONE user (the developer)
- Quality matters more than cost for personal mode
- The $2,500 credit balance means cost is less of a concern

### No Corporate Guardrails Needed
- Looking for models that can give direct, personal advice
- Should NOT constantly say "I'm just an AI" or "consult a professional"
- Should feel like talking to a trusted friend/therapist

---

## 🎯 Key Questions to Answer

1. **Which model has the best emotional intelligence for therapy-like conversations?**

2. **Is GPT-5.2 significantly better than GPT-4o for this use case, or is it overkill?**

3. **Are reasoning models (o3, o4-mini) useful for mental health support, or are they designed for different tasks?**

4. **What's the sweet spot between quality and cost for daily personal use?**

5. **Which voice models provide the most natural, warm-sounding responses?**

6. **Are there any models known to be more "flexible" with guardrails for personal/therapeutic use?**

7. **What system prompts or techniques do mental health chatbots use to get better responses?**

---

## 📅 Timeline

Please provide findings within a thorough research session. Prioritize:
1. Chat model comparison (most important)
2. Cost analysis
3. Voice model recommendations
4. Implementation tips

---

*This research will directly inform the development of MindMate's AI backbone. The goal is to create the most empathetic, helpful, and personalized mental wellness companion possible.*
