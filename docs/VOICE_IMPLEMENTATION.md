# Voice Implementation - Hybrid Audio Models

## Overview

MindMate uses a hybrid audio model approach for voice message processing, providing improved quality and cost efficiency compared to the original Whisper + TTS pipeline.

## Architecture

### Voice Processing Flow

```
User Voice (OGG) → Transcription → GPT Processing → TTS → Response Voice (OGG)
        ↓                    ↓           ↓         ↓
  gpt-4o-mini-    →  gpt-4o-mini  →  gpt-4o-mini-tts
     transcribe          (chat)           (voice)
```

### Models Used

| Component | Model | Cost | Benefits |
|-----------|-------|------|----------|
| **Transcription** | `gpt-4o-mini-transcribe` | $0.003/min | 50% cheaper than Whisper, better accuracy |
| **Processing** | `gpt-4o-mini` | $0.02/100 msgs | Same as text chat |
| **TTS** | `gpt-4o-mini-tts` | $0.015/min | Enhanced voice control, same cost |

**Total Cost**: $0.018/minute (14% savings from original $0.021/min)

## Implementation Details

### Code Configuration

```python
# Voice Configuration (src/bot.py)
VOICE_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
VOICE_TTS_MODEL = "gpt-4o-mini-tts"
```

### Key Features

1. **Improved Transcription Accuracy**
   - Better handling of conversational speech
   - Improved performance with accents
   - Reduced hallucinations

2. **Enhanced Voice Quality**
   - More natural prosody and intonation
   - Better emotional range for mental wellness context
   - 13 built-in voices (alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse, marin, cedar)

3. **Cost Efficiency**
   - 14% reduction in voice processing costs
   - Same reliability as original pipeline
   - No architectural changes required

## Audio Format Handling

### Input Processing
- **Telegram Format**: OGG/Opus
- **Model Requirements**: WAV/MP3
- **Conversion**: Handled automatically in `handle_voice` function

### Output Processing
- **Model Output**: WAV format
- **Telegram Format**: OGG/Opus
- **Conversion**: Automatic conversion before sending

## Error Handling

The implementation includes robust error handling:
- Fallback to text response if voice processing fails
- Graceful handling of audio conversion issues
- User-friendly error messages
- Comprehensive logging for debugging

## Integration with A/B Testing

Voice processing is completely separate from chat model A/B testing:
- A/B testing continues to work with chat models only
- Voice improvements benefit all users regardless of model selection
- No impact on blind testing functionality

## Performance Metrics

### Latency
- **Target**: 5-10 seconds total (same as original)
- **Breakdown**: ~2s transcription + ~3s processing + ~2s TTS

### Quality Improvements
- **Transcription**: ~10-15% better accuracy, especially with accents
- **Voice**: More natural intonation and emotional range
- **Reliability**: Same uptime as original implementation

## Future Enhancements

### Phase 2: Direct Audio Models (Optional)
- Test `gpt-4o-mini-audio-preview` for unified processing
- Potential for further latency reduction
- Single API call instead of three separate calls

### Phase 3: Realtime Audio (Advanced)
- Implement WebSocket-based realtime audio
- Sub-second response times
- Advanced features like interruption handling

## Monitoring

### Key Metrics to Track
- Cost per voice message
- Transcription accuracy (spot checks)
- Voice quality ratings
- Error rates and types
- User satisfaction scores

### Cost Monitoring
- Daily voice processing costs
- Cost per active user
- Comparison with baseline ($0.018/min target)

## Troubleshooting

### Common Issues
1. **Audio Conversion Failures**: Check FFmpeg availability on Render.com
2. **High Latency**: Monitor OpenAI API response times
3. **Voice Quality**: Test with different input audio qualities

### Debug Logging
All voice processing includes detailed logging:
- Transcription success/failure
- API response times
- Audio conversion status
- Error details with stack traces

## Security & Privacy

- Audio files are processed temporarily and deleted
- No audio data is stored permanently
- OpenAI does not use voice data for training by default
- All processing follows OpenAI's privacy policy

---

**Implementation Date**: February 7, 2026  
**Version**: 2.0 (Hybrid Audio Models)  
**Status**: ✅ Production Ready
