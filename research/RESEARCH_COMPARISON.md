# Research Comparison: Perplexity vs Gemini vs ChatGPT

## 🔍 Three AI Research Agents, Different Conclusions

| Aspect | Perplexity | Gemini | ChatGPT |
|--------|------------|--------|---------|
| **Primary Pick** | `gpt-4o-mini` | `gpt-4.1-mini` | `gpt-5.2` |
| **Empathy Benchmark** | EQ-Bench3 | Empathy Bench | User reports |
| **Empathy Ranking** | GPT-4o-mini: Good | GPT-4.1-mini: #3 | GPT-5.2: "friend-like" |
| **Temperature** | 0.8 | 0.6-0.7 | 0.7-0.8 |
| **Voice Input** | whisper-1 | whisper-1 | GPT-4o-transcribe |
| **Voice Output** | tts-1 | Hume AI EVI | ElevenLabs/tts-1-hd |
| **Reasoning Models** | ❌ Avoid | ✅ o4-mini for journals | ❌ Too strict |
| **Personal Mode** | gpt-5-mini | gpt-5.2-thinking | GPT-5.2 + GPT-4.1 |
| **Memory Focus** | 10 messages | 100K sliding window | 1M context (GPT-4.1) |

---

## 🎯 Key Disagreements

### 1. Primary Model Choice
- **Perplexity:** GPT-4o-mini (proven in therapy studies, cheapest)
- **Gemini:** GPT-4.1-mini (highest Empathy Bench score #3)
- **ChatGPT:** GPT-5.2 (newest flagship, "friend-like")

**Resolution:** A/B test GPT-4o-mini vs GPT-4.1-mini first. Consider GPT-5.2 for premium.

### 2. Temperature Setting
- **Perplexity:** 0.8 (warmer, more varied)
- **Gemini:** 0.6-0.7 (grounded but human-like)
- **ChatGPT:** 0.7-0.8 (balanced)

**Resolution:** Use 0.7-0.8 (consensus range).

### 3. Voice Input (STT)
- **Perplexity:** whisper-1 (fastest, reliable)
- **Gemini:** whisper-1 (same)
- **ChatGPT:** GPT-4o-transcribe (best accuracy)

**Resolution:** Test GPT-4o-transcribe vs whisper-1. ChatGPT cites it has lowest error rate.

### 4. Voice Output (TTS)
- **Perplexity:** tts-1 (cheaper, natural)
- **Gemini:** Hume AI EVI (emotional prosody)
- **ChatGPT:** ElevenLabs or tts-1-hd

**Resolution:** tts-1-hd for standard, Hume/ElevenLabs for premium.

### 5. Memory Strategy
- **Perplexity:** 10 messages in-memory
- **Gemini:** 100K sliding window + profile summary
- **ChatGPT:** 1M context (GPT-4.1) + PostgreSQL

**Resolution:** GPT-4.1's 1M context is a game-changer for memory. Use it!

---

## ✅ Areas of Agreement (All 3)

| Topic | Consensus |
|-------|-----------|
| **Avoid o1/o3 for chat** | All agree - too strict, too slow |
| **Crisis detection** | Don't rely on model guardrails alone |
| **System prompt** | Empathetic persona, anti-deflection language |
| **Temperature** | 0.7-0.8 range |
| **Tiered approach** | Different models for free/standard/premium |

---

## 🚀 Final Recommended Action Plan

### Phase 1: A/B Testing (IMMEDIATE)
```python
# Test A: Current (Perplexity's choice)
model = "gpt-4o-mini"
temperature = 0.8

# Test B: Gemini's choice  
model = "gpt-4.1-mini"
temperature = 0.7

# Test C: ChatGPT's choice (if budget allows)
model = "gpt-5.2"
temperature = 0.7
```

### Phase 2: Voice Integration
- **STT:** GPT-4o-transcribe (ChatGPT) or whisper-1 (Perplexity/Gemini)
- **TTS:** tts-1-hd standard, Hume AI EVI for premium

### Phase 3: Memory Upgrade
- Move to GPT-4.1 or GPT-4.1-mini for **1M token context**
- Implement session summaries in PostgreSQL
- Consider vector store for semantic memory

---

## 📊 Final Model Strategy (Synthesized)

| Tier | Chat Model | Context | Voice | Cost/100 conv |
|------|------------|---------|-------|---------------|
| **Free** | gpt-3.5-turbo | 16K | - | ~$0.15 |
| **Standard** | gpt-4.1-mini | **1M** | whisper + tts-1 | ~$4.00 |
| **Premium** | gpt-5.2 | 400K | GPT-4o-transcribe + ElevenLabs | ~$740 |
| **Personal** | gpt-5.2 + gpt-4.1 | 1M | Hume AI EVI | Quality > Cost |

---

## 💡 Key Insights from All Reports

1. **GPT-4.1-mini has 1M context** - Massive advantage for memory across sessions!
2. **GPT-4.1-mini ranks #3 on Empathy Bench** - 45% better than GPT-4o-mini
3. **GPT-5.2 is "friend-like"** but expensive (~$740/100 conv)
4. **All agree: Avoid o-series** for casual chat (too strict/slow)
5. **Temperature consensus: 0.7-0.8** for warmth without incoherence
6. **GPT-4o-transcribe** may be better than whisper-1 (test it!)

---

## 🎯 Immediate Next Steps

1. **A/B Test:** GPT-4o-mini vs GPT-4.1-mini (20 convos each)
2. **If budget allows:** Also test GPT-5.2 for premium tier
3. **Voice:** Test GPT-4o-transcribe vs whisper-1
4. **Memory:** Plan migration to GPT-4.1-mini for 1M context
5. **Document:** Results in `research/AB_TEST_RESULTS.md`
