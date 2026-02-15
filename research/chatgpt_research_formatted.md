# Direct-Audio Models for MindMate
**OpenAI now offers end-to-end audio models** that can accept speech input and produce speech output in one step – eliminating separate transcription (Whisper) and TTS calls. The key models are:
**Chat-completions audio models**:
**GPT-Audio (gpt-audio)** – A high-capability model (GPT-4o audio) for chat with audio. It *“accepts audio inputs and outputs”* via the Chat Completions API.
**GPT-Audio Mini (gpt-audio-mini)** – A smaller, faster, cheaper version of GPT-Audio. It is *“cost-efficient”*, also supporting audio in/out.
**Realtime audio models**:
**GPT-Realtime (gpt-realtime)** – A production-ready speech-to-speech model designed for low-latency conversational voice agents. It natively handles streaming audio input/output (WebRTC/WebSocket) for live conversation.
**GPT-Realtime Mini (gpt-realtime-mini)** – A lightweight realtime model (GPT-4o mini variant) that trades some capability for lower cost.
**Speech-to-text and TTS** (for completeness): GPT-4o **transcribe** models (e.g. gpt-4o-transcribe, gpt-4o-mini-transcribe) can transcribe audio to text (more accurate than Whisper), and **GPT-4o Mini TTS** (e.g. gpt-4o-mini-tts) can generate speech from text. These are separate API endpoints (Audio → text or text → audio) but still incur multiple calls.
Each of the above models supports audio modalities as follows: GPT-Audio/Mini and GPT-Realtime/Mini accept *audio files* (WAV/MP3) as input and can produce *audio outputs* (streamed back or base64). These can be used via the Chat or Realtime APIs.
## Technical Details
**API Endpoints**: Audio-capable chat models use the standard **Chat Completions API** (POST /v1/chat/completions). For example, sending an audio file as a message content of type "input_audio". Realtime models use the **Realtime API** (wss://api.openai.com/v1/realtime) which streams JSON events for audio I/O.
**Audio Formats**: Chat API accepts WAV or MP3 (base64-encoded) as per docs. Realtime supports raw PCM16 (24 kHz) or telephony codecs (G.711) via WebRTC/WS. *Telegram voice notes are OGG/Opus*, so you must convert to WAV/MP3 before sending. (E.g. use ffmpeg or pydub to convert OGG→WAV.)
**File Size/Durations**: The transcription endpoint notes a 25 MB file size limit (≈4–5 minutes of audio). Chat completions likely have similar limits per message. Very long audio should be chunked.
**Pricing (per 1M tokens)**:
*GPT-Audio / GPT-Realtime*: **Audio tokens** are $32 for 1M input and $64 for 1M output tokens. (With cached audio input at $0.40/1M.) For comparison, text tokens are $2.50/$10.00. This implies roughly **$0.096 per 1-minute of speech** (input + output) for these high-end models.
*GPT-Audio Mini / GPT-Realtime Mini*: **Audio tokens** are **$10 in / $20 out** (text tokens $0.60/$2.40). That’s about **$0.030 per minute** of round-trip conversation.
*Current pipeline*: Whisper transcription is $0.006/min and TTS is $0.015/min, totaling ~$0.021/min, plus negligible GPT chat cost.
**Latency & Throughput**: Using a direct audio model collapses three API calls into one. Latency is reduced (no file uploads between steps). The Realtime API can respond in ~0.3–0.8 s for small prompts and streams audio continuously. Even non-streaming chat calls should be ~2–5 s (depending on prompt and model). This is faster than the current ~5–10 s multi-step chain.
**Quality & Voices**: GPT-Realtime/Audio models produce *natural, expressive speech*. OpenAI reports improvements in tone and nuance over separate TTS. New voices (e.g. “Marin”, “Cedar”) allow emotional tone. The model can adjust style (“speak empathetically”) via prompts. Experiments show highly intelligible, human-like audio with transcripts provided for accessibility.
**Language Support**: Underlying GPT-4o models are multilingual. Audio input models should recognize languages seen in training; GPT-Realtime was evaluated on English, Spanish, Chinese, etc. Output voices are currently English-centric, but could be prompted for accents or styles. The Audio API supports transcription/translation into English by setting the target_language parameter.
**Model Capabilities**: All chat-based audio models support system/developer messages and conversation history. You can feed prior messages plus audio. GPT-Audio/GPT-Realtime respect guardrail prompts (“You are a therapist…”). They can also emit text transcripts in addition to audio (the JSON response includes a "transcript" field for the audio spoken by the assistant).
**API Usage**: In the Chat API, include {"type":"input_audio","input_audio":{"data":<base64>, "format":"wav"}} in a message content array. Also set modalities: ["audio"] (and optionally "text" if expecting transcript) in the request. The response’s choices[0].message.audio.data field holds base64 audio. In Realtime, you send chunks via input_audio_buffer.append events and receive response.audio.delta.
**Rate Limits**: These new models have high rate limits. GPT-Realtime models support thousands of tokens/sec (see docs for RPM/TPM). In practice, Real-time sessions can handle concurrent users via WebSockets.
## Current vs. Direct-Audio Pipeline
Direct models simplify the pipeline significantly and can improve conversational naturalness (no loss from re-synthesis). The **Realtime API** in particular *“processes and generates audio directly through a single model”*, reducing latency and preserving nuance.
## Migration and Integration
**Implementation changes:** Instead of separately calling Whisper and TTS, update your handler to send the user’s audio file to a chat completion call. E.g.:
audio_data = open("user.ogg","rb").read()
# Convert Telegram OGG to WAV (e.g. via ffmpeg) before this step.
audio_b64 = base64.b64encode(audio_data).decode()

messages = [
    {"role": "system", "content": "You are an empathetic mental wellness assistant."},
    {"role": "user", "content": [
         {"type": "input_audio",
          "input_audio": {"data": audio_b64, "format": "wav"}}
    ]}
]
resp = openai.ChatCompletion.create(
    model="gpt-audio-mini",                # try gpt-audio-mini first
    modalities=["audio"],                 # request audio output
    messages=messages
)
audio_b64_out = resp.choices[0].message["audio"]["data"]
audio_bytes = base64.b64decode(audio_b64_out)
with open("response.wav","wb") as f:
    f.write(audio_bytes)

await update.message.reply_voice(open("response.wav","rb"),
                                 caption="(spoken) " + resp.choices[0].message["transcript"])
This single call replaces the three-step pipeline. You must still convert between Telegram’s OGG/Opus and the model’s supported format (WAV/MP3). After decoding the base64 response, you can send the WAV directly, or re-encode to OGG for Telegram voice (both reply_voice and reply_audio are options).
**Libraries**: Use OpenAI’s Python SDK (openai.chat.completions.create or appropriate Realtime client). Use ffmpeg, pydub or similar to handle format conversion. The rest of the bot logic (conversation history, personal-mode prompts) stays the same.
**Error Handling**: Handle API errors as usual. If audio call fails, you could fallback to Whisper+GPT+TTS as a safety net. Monitor for cases where the model returns no transcript or refusal. Ensure to catch exceptions (network, rate-limit, invalid audio) and reply with a user-friendly message if needed.
**Telegram Compatibility**: Telegram voice messages arrive as OGG/Opus. The chat endpoint does *not* accept OGG directly, so convert to WAV/MP3 first. (Realtime API via WebRTC could accept raw mic audio, but for incoming Telegram files you’ll need conversion anyway.) For responses, model returns WAV. Telegram’s reply_voice expects OGG (Opus), so convert WAV→OGG for optimal size/compatibility. Alternatively, send as an audio file (send_audio) if duration matters.
## Cost/Benefit Analysis
**Cost**: Using *GPT-Audio Mini* or *GPT-Realtime Mini* costs about **$0.03 per minute** of conversation, roughly 50% higher than the current $0.021. Larger models (GPT-Audio/GPT-Realtime) cost ~$0.10/min. Thus, direct audio is more expensive per minute, *especially* on high-end models. However, you eliminate Whisper and TTS costs. Over time and scale, the break-even depends on usage volume. For small/medium traffic, the simplicity benefit may justify the cost. For very heavy usage, consider using the mini models or mixed approach.
**Latency & UX**: Response times improve – no need to wait for 3 sequential calls. Users get nearly instantaneous spoken replies (as fast as 1–2 seconds). The voice “feels” more natural, which can significantly improve user experience for a mental wellness assistant. Fewer technical delays make conversation smoother and more personal.
**Reliability & Complexity**: Fewer moving parts means fewer failure points. No more fragile file uploads between services. This boosts reliability. Code is simpler (one API call, no temporary files), reducing maintenance cost.
**Scalability**: Real-time models can handle streaming input for continuous conversation. This could allow future features (e.g. truly live voice chat). Concurrency limits for audio models are generous (see OpenAI tier limits).
## Recommendations
Based on capabilities and fit for MindMate, **we recommend the following top models**:
**GPT-Realtime** – Best-in-class for voice agents. High intelligence, low latency, and superior audio quality with emotional nuance. Ideal for production usage once integrated. Start with gpt-realtime via the Realtime API to evaluate performance in conversation.
**GPT-Audio-Mini** – A cost-efficient chat-based audio model. It *“accepts audio inputs and outputs”* just like the larger model but at ~3× lower cost. Use gpt-audio-mini as a first proof-of-concept (Chat API) to validate the workflow, since it’s fast and affordable.
**GPT-Audio** (full) – The higher-quality audio chat model (gpt-audio, alias GPT-4o Audio). Use this for a final quality test. It has the same API usage as GPT-Audio-Mini but stronger language understanding (though at higher cost).
Alternatively, **GPT-Realtime-Mini** could replace GPT-Audio-Mini if ultra-low latency streaming is needed at low cost. But as a starting point, GPT-Audio-Mini is simplest to integrate (no WebSocket needed).
**Priority to Try**: Begin with **gpt-audio-mini** (chat endpoint) – low effort and cost. Verify the audio round-trip works in Telegram. Then test **gpt-realtime** (streaming mode) to measure quality/latency. Finally compare with **gpt-audio** for any quality gains.
**Migration Effort**: Moderate. The core change is refactoring the handle_voice function to one OpenAI call (see code example above). Removing Whisper/TTS calls cuts complexity. Converting audio format requires a small utility (ffmpeg or library). Testing and tuning prompts for voice tone will take time. Overall, this is a few days of development and QA rather than weeks.
**Expected Improvements**:
- **Faster responses** (single API call) – a more conversational feel.
- **More natural voice** – emotional nuance and variety (especially with Realtime model).
- **Simpler code** – easier maintenance, fewer bugs.
- **Better UX** – users can choose voice-only chat mode seamlessly.
**Potential Risks & Mitigations**:
- **Cost Overrun**: Running full-audio models is more expensive. *Mitigation*: Use the “mini” versions and caching/turn limits. Monitor usage.
- **Output Safety**: More complex model might produce unpredictable utterances. *Mitigation*: Keep existing moderation and personal-mode prompts. Log audio transcripts for review. Possibly use the transcript field to run content filters.
- **Latency spikes**: Under heavy load, audio models may slow down. *Mitigation*: Implement timeouts and fallbacks.
- **Dependency on OpenAI**: A single service now. *Mitigation*: Ensure retry logic and possibly keep fallback to Whisper/TTS if needed.
## Sample Python Code
Here is a sketch of how to implement direct audio handling (using the OpenAI Python SDK):
import base64
from openai import OpenAI

client = OpenAI()

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Download Telegram voice (OGG) and convert to WAV
    voice = update.message.voice or update.message.audio
    if not voice:
        return
    voice_file = await context.bot.get_file(voice.file_id)
    ogg_data = await voice_file.download_as_bytearray()
    wav_data = convert_ogg_to_wav_bytes(ogg_data)  # use ffmpeg or pydub

    # Prepare audio as base64
    audio_b64 = base64.b64encode(wav_data).decode()

    # Build messages for chat completion (audio-only user message)
    messages = [
        {"role": "system", "content": "You are MindMate, a compassionate therapy assistant."},
        {"role": "user", "content": [
             {"type": "input_audio",
              "input_audio": {"data": audio_b64, "format": "wav"}}
        ]}
    ]

    # Call GPT-Audio-Mini model for example
    response = client.chat.completions.create(
        model="gpt-audio-mini",
        modalities=["audio"],
        messages=messages,
    )

    # Extract and decode the base64 audio reply
    audio_resp_b64 = response["choices"][0]["message"]["audio"]["data"]
    audio_resp = base64.b64decode(audio_resp_b64)
    with open("reply.wav", "wb") as f:
        f.write(audio_resp)

    # (Optional) extract text transcript for caption
    text_resp = response["choices"][0]["message"].get("transcript", "")

    # Send the voice reply in Telegram (convert to OGG for Telegram)
    ogg_reply = convert_wav_to_ogg_bytes(audio_resp)  # e.g. ffmpeg conversion
    await update.message.reply_voice(voice=ogg_reply, caption=text_resp)
This one function replaces the three-step pipeline. In practice, use asynchronous HTTP or the OpenAI library with await. Also handle exceptions and ensure you clean up temporary files.
## Conclusion
The new GPT-4o audio and realtime models allow MindMate to handle user voice input *directly* and respond with synthesized speech in one step. The **top choices** are **GPT-Realtime** (best quality/latency), **GPT-Audio-Mini** (fast/cost-effective chat mode), and **GPT-Audio** (full-quality). Integration effort is moderate but payoff is a simpler, more responsive voice bot. We expect **faster, more natural conversations**; the main trade-off is higher per-minute cost. With careful prompt design and monitoring, direct audio models should greatly streamline MindMate’s architecture and improve user experience.
**Sources:** Official OpenAI docs on Audio and Realtime API, OpenAI release blogs, and community experiments. These confirm model capabilities, pricing, and usage patterns.

  gpt-audio Model | OpenAI API

  gpt-audio-mini Model | OpenAI API

   gpt-realtime Model | OpenAI API

    Introducing gpt-realtime and Realtime API updates for production voice agents | OpenAI

 gpt-realtime-mini Model | OpenAI API

    Experimenting with audio input and output for the OpenAI Chat Completion API

  GPT Realtime API: Redefining Human-AI Voice Interaction | by Ranjanunicode | Medium

 Speech to text | OpenAI API

  Pricing | OpenAI API


| Aspect | Current (Whisper + GPT-4o-mini + TTS-1) | Direct Audio (GPT-Audio/Realtime) |
| --- | --- | --- |
| API Calls | 3 separate calls (transcription, chat, TTS) | 1 call (single Chat or Realtime API)[4][7] |
| Latency | ~5–10 sec (upload+processing each) | 3–5 sec (chat) or ~<1 sec streaming (Realtime)[15] |
| Cost | ~$0.006 (Whisper)+$0.015 (TTS) = $0.021/min (chat cost ≈$0) | ~$0.03–$0.10/min (depending on model)[11] |
| Quality | High (specialized ASR and TTS) | High – unified model preserves emotion and nuance[16] |
| Complexity | High (file handling, 3 APIs, error points) | Low (single API call, no intermediate files)[4] |
| Reliability | Multiple failure points (network, each model) | Fewer failures (one model), but single point of failure |
