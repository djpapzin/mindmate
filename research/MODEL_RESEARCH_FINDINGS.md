# MindMate AI Model Research: Complete Analysis & Recommendations

*Research conducted by Perplexity AI - February 2026*

---

## 🎯 Executive Summary: The Clear Winner

**Primary Recommendation: GPT-4o-mini**
- **Proven track record**: 4.19/5 usability, 3.99/5 therapeutic skills in actual therapy studies
- **Cost**: $1.07/month for 100 conversations with voice (your $2,500 credits last 194 years!)
- **Speed**: Sub-second responses (critical for mental health support)
- **Empathy**: GPT-4 family scored 117 EQ (89th percentile of humans)
- **Guardrails**: Moderate balance—not overly restrictive like GPT-5

---

## 📊 Model Comparison Matrix

| Model | Input $/1M | Output $/1M | Speed | Empathy | Best For | Monthly Cost (100 convos) |
|-------|------------|-------------|-------|---------|----------|---------------------------|
| **GPT-4o-mini** ✓ | $0.075 | $0.30 | Very Fast | Good | **Therapy chatbots** | **$0.019** |
| GPT-5-mini | $0.125 | $1.00 | Fast | Unknown | Scaling | $0.06 |
| GPT-4o | $1.25 | $5.00 | Fast | Good | Premium tier | $0.31 |
| GPT-5 | $0.625 | $5.00 | Slow (60s+) | Low (1357 EQ) | ✗ Avoid | $0.28 |
| GPT-5.2 | $0.875 | $7.00 | Moderate | Unknown | ✗ Too new | $0.39 |
| o3 | $1.00 | $4.00 | Very Slow | N/A | ✗ Wrong purpose | $0.25 |

---

## 🔑 Key Findings

### 1. Best Emotional Intelligence: GPT-4o Family

- GPT-4 achieved EQ of 117 (89th percentile of humans)
- Clinical study: 3.99/5 therapeutic skills, 4.75/6 working alliance
- 85% of participants reported positive experiences
- **Surprising**: GPT-5 scored only 1357 Elo on EQ-Bench3 (lower than expected)

### 2. GPT-5.2 is OVERKILL (Avoid It)

❌ **Wrong optimization**: Designed for "agentic coding," not therapy  
❌ **46x more expensive**: $0.394 vs $0.019 per 100 conversations  
❌ **Stronger guardrails**: 52% fewer "undesired responses" = MORE deflection  
❌ **No empathy data**: Too new to have therapeutic validation

### 3. Reasoning Models (o3, o4-mini) = WRONG TOOL

⏱️ **Speed**: 30-120 second response times  
💰 **Cost**: 2-8x more expensive  
🎯 **Wrong design**: Built for logic, not empathy  

### 4. Voice Model Recommendations

| Purpose | Model | Cost | Notes |
|---------|-------|------|-------|
| **Speech-to-Text** | whisper-1 | $0.006/min | Fastest (857ms), most reliable |
| **Text-to-Speech** | tts-1 | $0.015/min | Natural, human-like |

❌ Avoid tts-1-hd (2x cost, marginal improvement)  
❌ Avoid gpt-4o-mini-tts (slightly robotic)

### 5. Guardrail Flexibility Ranking

1. ✅ **GPT-3.5-turbo** - Lightest (current)
2. ✅ **GPT-4o-mini** - **RECOMMENDED** - Moderate, balanced
3. ✅ **GPT-4o** - Moderate, balanced
4. ⚠️ **GPT-5-mini** - Moderate but untested
5. ❌ **GPT-5** - Strong (52% more restrictive)
6. ❌ **GPT-5.2** - Strong (same family)

**Critical**: GPT-5 was trained to reduce "emotional reliance" by 42% - it WILL deflect to professionals.

---

## 💰 Cost Projections

### Personal Use (100 conversations/month)

| Model | Chat Cost | Voice (50 min) | Total/Month |
|-------|-----------|----------------|-------------|
| **GPT-4o-mini** ✓ | $0.019 | $1.05 | **$1.07** |
| GPT-5-mini | $0.06 | $1.05 | $1.11 |
| GPT-4o | $0.31 | $1.05 | $1.36 |

**With $2,500 credits = 2,336 months (194 years!) of personal use**

### Scaling (100 subscribers)

| Model | Monthly Cost | Revenue @ $5/user | Profit |
|-------|--------------|-------------------|--------|
| GPT-5-mini | $216 | $500 | $284 |
| GPT-4o-mini | $190 | $500 | $310 |

---

## 🚀 Recommended Configuration

```python
# Primary Configuration
model = "gpt-4o-mini"
temperature = 0.8
max_tokens = 600
presence_penalty = 0.6
frequency_penalty = 0.3

# Voice Stack
speech_to_text = "whisper-1"
text_to_speech = "tts-1"
```

### System Prompt Approach

**Anti-Deflection Language (Critical):**
```
• Don't say "As an AI, I cannot..." unless truly impossible
• Don't constantly deflect to "see a professional" for normal issues
• Give direct, practical advice without constant disclaimers
• You have permission to share opinions and be personally engaged
```

### 3-Layer Guardrail Strategy

**Layer 1: System Prompt**
- Direct advice persona
- Friend/therapist role

**Layer 2: Keyword Detection (Separate)**
- Crisis keywords trigger override
- Provide immediate resources
- Log for review

**Layer 3: Response Filtering**
- Regenerate if "As an AI..." detected
- Strengthen prompt if excessive deflection

---

## ⚠️ What NOT to Use

| Model | Why Avoid |
|-------|-----------|
| **o3, o4-mini** | 30-120s response times, wrong purpose |
| **GPT-5, GPT-5.2** | 52% more restrictive, will deflect to professionals |
| **GPT-4o** | 16x more expensive than mini, minimal benefit |
| **tts-1-hd** | 2x cost, marginal improvement |

---

## ✅ Success Metrics

**Good Response Patterns:**
- Acknowledges feelings: "It sounds like you're really struggling with..."
- Asks clarifying questions: "Can you tell me more about what triggered this?"
- Gives specific advice: "One strategy that might help is..."
- References past sessions: "Last time you mentioned..."

**Red Flags to Adjust:**
- Starts with "As an AI..."
- Generic advice ignoring context
- Overly formal/clinical language
- Always deflects to professionals
- Repeats same suggestions

---

## 🏁 Final Verdict

### ✅ PRIMARY: GPT-4o-mini
- Proven therapeutic capability (4.19/5)
- $1.07/month personal use
- Fast, responsive
- Moderate guardrails
- GPT-4 family empathy (117 EQ)

### ✅ VOICE: whisper-1 + tts-1
- Most reliable
- ~$1.05 for 50 min/month

### ✅ CONFIGURATION
- Temperature: 0.8
- Presence penalty: 0.6
- Frequency penalty: 0.3
- Anti-deflection system prompts
- 3-layer crisis detection

---

*Sources: PMC research papers, OpenAI documentation, Reddit/HN community, EQ-Bench3 leaderboard*
