# Research Comparison: Perplexity vs Gemini

## 🔍 Two AI Research Agents, Different Conclusions

| Aspect | Perplexity | Gemini | Winner |
|--------|------------|--------|--------|
| **Recommended Chat Model** | `gpt-4o-mini` | `gpt-4.1-mini` | **Needs Testing** |
| **Empathy Benchmark Used** | EQ-Bench3 | Empathy Bench | Different metrics |
| **Empathy Ranking** | GPT-4o-mini: Good | GPT-4.1-mini: #3 (best) | GPT-4.1-mini |
| **Temperature** | 0.8 | 0.6-0.7 | Test both |
| **Voice Output** | tts-1 | tts-1-hd / Hume AI EVI | Hume for premium |
| **Reasoning Models** | ❌ Avoid | ✅ o4-mini for journals | Gemini |
| **Personal Mode Model** | gpt-5-mini | gpt-5.2-thinking | Gemini (more detailed) |

---

## 🎯 Key Disagreements

### 1. Primary Model Choice
- **Perplexity:** GPT-4o-mini (proven in therapy studies)
- **Gemini:** GPT-4.1-mini (higher Empathy Bench score)

**Resolution:** GPT-4.1-mini appears to be newer and potentially better. Worth testing!

### 2. Temperature Setting
- **Perplexity:** 0.8 (warmer, more varied)
- **Gemini:** 0.6-0.7 (grounded but human-like)

**Resolution:** Start with 0.7 (middle ground), adjust based on responses.

### 3. Reasoning Models
- **Perplexity:** Avoid o3/o4-mini entirely
- **Gemini:** Use o4-mini for deep journal analysis

**Resolution:** Gemini's approach is smarter - use o4-mini for specific deep analysis tasks, not real-time chat.

### 4. Voice Output
- **Perplexity:** tts-1 (cheaper, natural)
- **Gemini:** tts-1-hd or Hume AI EVI (emotional prosody)

**Resolution:** Use tts-1 for standard, consider Hume AI EVI for premium emotional voice.

---

## ✅ Areas of Agreement

| Topic | Consensus |
|-------|-----------|
| **Avoid GPT-5/5.2 for chat** | Both agree - too restrictive |
| **Voice Input** | Both recommend `whisper-1` |
| **Crisis detection** | Both say don't rely on model guardrails alone |
| **System prompt structure** | Both recommend anti-deflection language |
| **Memory approach** | Both suggest sliding window + summaries |

---

## 🚀 Recommended Action Plan

### Immediate (Test Both Models)
```python
# Option A: Perplexity's choice (current)
model = "gpt-4o-mini"
temperature = 0.8

# Option B: Gemini's choice
model = "gpt-4.1-mini"  
temperature = 0.7
```

### Testing Protocol
1. Run 20 conversations with GPT-4o-mini
2. Run 20 conversations with GPT-4.1-mini
3. Compare: empathy, directness, helpfulness
4. Choose winner for production

### Future Enhancements
- Add o4-mini for "Deep Analysis" mode (journal entries)
- Consider Hume AI EVI for voice emotional detection
- Implement gpt-5.2-thinking for premium sessions

---

## 📊 Updated Model Strategy

| Tier | Chat Model | Voice | Deep Analysis |
|------|------------|-------|---------------|
| **Free** | gpt-3.5-turbo | - | - |
| **Standard** | gpt-4o-mini OR gpt-4.1-mini | whisper-1 + tts-1 | - |
| **Premium** | gpt-5.2-thinking | whisper-1 + Hume EVI | o4-mini |

---

## 💡 Key Insight

**Gemini found a model Perplexity missed:** GPT-4.1-mini ranks #3 on Empathy Bench with 40.8% score, while GPT-4o-mini only ranks #11 with 28.1%.

That's a **45% improvement in empathy** - significant for a therapy bot!

**Recommendation:** Test GPT-4.1-mini as potential upgrade from GPT-4o-mini.
