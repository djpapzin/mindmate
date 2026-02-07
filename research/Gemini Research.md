The Architecture of Omni-Modality: A Technical Analysis of OpenAI’s Audio-Native Transformers and the Evolution of Real-Time Generative Intelligence
The transition from modular, task-specific artificial intelligence to unified multimodal architectures represents one of the most significant shifts in computational linguistics and digital signal processing. Historically, the integration of audio into large language models (LLMs) was achieved through cascaded pipelines, which sequentially linked automatic speech recognition (ASR), text-based reasoning, and text-to-speech (TTS) synthesis. This fragmented approach introduced inherent bottlenecks, including error propagation across modules and significant latency that precluded natural human-computer interaction.1 The emergence of GPT-4o, where the "o" designates "omni," signifies the development of a flagship model designed for natural interaction by reasoning across audio, vision, and text in real time.1 By training a single neural network end-to-end across these modalities, the industry has moved toward a paradigm where all inputs and outputs are processed through the same transformer-based architecture, preserving the rich, paralinguistic nuances of human communication that were previously discarded in transcription-based systems.4
The Technical Genesis of End-to-End Audio Modeling
The core innovation of the GPT-4o architecture is its ability to directly ingest and generate audio tokens without an intermediate text representation. In previous iterations, such as the Voice Mode in ChatGPT powered by GPT-4 Turbo, the system relied on a three-model pipeline: an initial model transcribed audio to text, the main LLM processed the text, and a third model converted the output back to audio.1 This methodology meant that critical acoustic features—including tone of voice, emotional inflection, multiple speakers, and background environmental sounds—were fundamentally invisible to the reasoning engine.1
From Cascaded Pipelines to Unified Transformers
The architectural limitations of cascaded systems resulted in average latencies of  seconds for GPT-3.5 and  seconds for GPT-4, far exceeding the typical human conversational response gap of approximately  milliseconds.5 GPT-4o addresses this by achieving an average audio response latency of  milliseconds, with some responses occurring as rapidly as  milliseconds.4 This sub-second responsiveness is made possible by the unified architecture, which allows for streaming inputs and outputs where the model begins generating responses before the user has even finished their prompt—a capability known as duplex interaction.8
The move to an end-to-end model also mitigates the "intelligence loss" found in text-only reasoning. Because the model observes the raw audio signal (represented as discrete tokens), it can perceive and respond to laughter, sarcasm, and singing.1 This unified approach allows the model to retain prosodic information that dictates meaning in many contexts. For example, the same string of text can be interpreted as a sincere statement or a sarcastic remark depending entirely on the acoustic delivery, a distinction that GPT-4o can navigate natively.5
Multimodal Tokenization and Linguistic Efficiency
A pivotal component of this unified model is the development of a more efficient tokenizer. GPT-4o introduces a new tokenization scheme that significantly reduces the number of tokens required to represent various languages, particularly those using non-Latin scripts.1 This improvement has direct implications for both cost and performance, as a lower token count per word allows for faster processing and a more effective utilization of the model's  token context window.10
Language
Token Reduction Factor (vs. Previous Models)
Previous Token Count (Example)
New Token Count (Example)
Gujarati
4.4x
145
33
Telugu
3.5x
159
45
Tamil
3.3x
116
35
Hindi
2.9x
-
-
Marathi
2.9x
-
-
Chinese
1.4x
-
-
Japanese
1.4x
-
-
English
1.1x
27
24

The reduction in token counts for Indic and East Asian languages indicates a strategic shift toward global accessibility, allowing the model to perform complex reasoning tasks in these languages with a computational efficiency that previously was only possible in English.1
Neural Audio Codecs and the Tokenization of Sound
To integrate audio into a transformer, the continuous acoustic waveform must be discretized into a sequence of tokens that the model can process alongside text and visual data. This is achieved through a neural audio codec, which serves as the bridge between raw audio and the latent space of the transformer.12 While text is typically discretized using byte-pair encoding, audio requires a more complex compression strategy to manage the high sample rates of raw sound.12
Hierarchical Tokens and Multi-Scale Modeling
The technical implementation likely involves hierarchical tokenization, similar to the Multi-Scale Neural Audio Codec (SNAC).8 In such a system, audio is compressed into multiple levels of tokens. Coarse tokens, sampled at a lower frequency (e.g., ), capture the broad structure and prosody of the audio, while fine tokens, sampled at higher frequencies, capture the specific timbral and acoustic details.13 This hierarchical approach is essential for long-form audio modeling; for instance, with coarse tokens covering a broader time span, a model with a context window of  tokens can effectively maintain coherence in an audio track for approximately three minutes.13

Codec Feature
Technical Detail
Impact on Performance
Sampling Rate
 (standard for Realtime API)
High-fidelity voice and sound reconstruction 14
Quantization
Residual Vector Quantization (RVQ)
Progressive refinement of audio quality across levels 12
Format Support
PCM, G.711 mu-law, G.711 A-law
Compatibility with various telephony and web standards 15
Token Mapping
1 token per  (input)
Balances computational load with acoustic granularity 16

The use of a neural codec allows the model to "predict" the next audio token in the same way it predicts the next word in a sentence. This autoregressive property enables the generation of speech that is not just a playback of pre-recorded phonemes but is dynamically synthesized based on the context of the conversation, including the ability to match the speaker's emotional state or adapt to interruptions.8
Self-Play and Distillation in Model Training
The efficiency of smaller models, such as GPT-4o mini, is bolstered by advanced distillation methodologies. OpenAI leverages its largest audio models to train smaller, more efficient versions by transferring knowledge through advanced self-play.18 This involves using large models to generate realistic conversational dynamics, which the smaller models then learn to replicate. This targeted approach to pretraining on audio-centric datasets ensures that even the smaller models—despite having fewer parameters—can maintain a deep insight into speech nuances and provide state-of-the-art transcription accuracy.18
Comprehensive Benchmarking of Audio-Native Intelligence
The evaluation of multimodal models requires a departure from traditional NLP benchmarks. While GPT-4o maintains elite performance on text-based evaluations like MMLU (scoring ) and HumanEval (), its true capability is measured through its performance on audio-specific benchmarks such as Dynamic-SUPERB and MMAU.1
The Dynamic-SUPERB Phase 2 Evaluation
Dynamic-SUPERB serves as a massive, collaboratively expanding benchmark designed to assess the instruction-following capabilities of voice models across  diverse tasks contributed by the global research community.2 This benchmark categorizes tasks into  domains, ranging from basic speech recognition to complex musical analysis.

Domain
GPT-4o Performance Trend
Key Observations
Intent Classification
High
Strong semantic understanding of spoken commands 2
Multilingual ASR
State-of-the-Art
Excellent performance across  languages in FLEURS 18
Singing Analysis
Strong
Capable of analyzing melody and vocal performance 2
Audio Reasoning
High
Excels in semantic and grammatical audio reasoning 2
Duration Prediction
Struggling
Difficulty in accurately estimating precise time intervals in audio 2
Instrument Classification
Struggling
Challenges in distinguishing complex musical textures 2

The performance on Dynamic-SUPERB indicates that while GPT-4o is a "universal" spoken language model, its strengths are currently skewed toward linguistic and semantic tasks. The struggle with audio duration and instrument classification suggests that while the model has a deep "conceptual" understanding of sound, its purely "acoustic" or "perceptual" resolution for non-speech sounds is an area for future refinement.2
ASR and Transcription Advancements
OpenAI's latest generation of audio models, including gpt-4o-transcribe and gpt-4o-mini-transcribe, have set new records in Word Error Rate (WER) across benchmarks like FLEURS.18 These models integrate a reinforcement learning (RL)-heavy paradigm that significantly reduces hallucinations in complex recognition scenarios, such as noisy environments or audio containing heavy accents.18
Model
English ASR (WER)
German ASR (WER)
French ASR (WER)
Whisper v3 (Legacy)
-
-
-
Lightning ASR



GPT-4o Mini Transcribe



Deepgram Nova 3




(Note: Benchmarks like Lightning ASR often prioritize latency over raw accuracy, but GPT-4o models remain highly competitive in multilingual contexts.21)
The Frontier of Synthetic Voice: Voice Engine
Separate from the general-purpose omni-models is "Voice Engine," a specialized research project focused on high-fidelity voice cloning. Developed in late 2022, Voice Engine can generate natural-sounding speech from a single 15-second audio sample.22
Diffusion Processes in Audio Synthesis
Unlike traditional text-to-speech models that rely on concatenative synthesis, Voice Engine utilizes a diffusion process.23 The model does not require speaker-specific fine-tuning; instead, it learns to predict the most probable sounds a speaker will make based on the paired audio and transcriptions it was trained on. By starting with random noise and progressively de-noising it to match the vocal profile of the -second reference, the model can generate audio that reflects the original speaker's accent, cadence, and unique vocal timbre.23
Applications and Ethical Cautions
The capabilities of Voice Engine have been demonstrated in diverse fields, including:
Reading Assistance: Providing natural, personalized voices for educational content.22
Content Translation: Translating a speaker's voice into multiple languages while preserving their native accent and vocal identity.24
Accessibility: Helping non-verbal individuals or patients recovering from voice loss to communicate with a voice that sounds like their own.22
However, the potential for misuse—such as election-related deepfakes or bypassing voice-based bank authentication—has led OpenAI to restrict its wide release.22 Current deployments are limited to "trusted partners" who must adhere to strict usage policies, including informed consent from original speakers and clear disclosure to audiences that the voice is AI-generated.23
Developer Implementation and the Realtime API
For builders, the transition to audio-native models is facilitated by a suite of new APIs. The Realtime API is specifically designed for low-latency, multimodal applications, providing a single endpoint to handle speech-to-speech, text, and audio inputs and outputs.14
Connection Methods and Interruption Handling
The Realtime API supports three primary connection protocols, each suited for different architectural needs:
WebRTC: Optimized for browser-based and client-side interactions, often using the Agents SDK for simplified integration.17
WebSockets: Ideal for server-to-server communication where a consistent, low-latency connection is required.27
SIP: Targeted at VoIP and traditional telephony systems, allowing AI agents to handle phone calls with human-like latency.17
A critical feature for conversational agents is the "server_vad" (Voice Activity Detection) mechanism. This allows the model to automatically detect when a user has started or stopped speaking, based on configurable parameters such as volume threshold and silence duration.14

Parameter
Default Value
Description
threshold

Activation threshold for detecting speech; higher values filter more noise 28
prefix_padding_ms

Amount of audio to include before detected speech for context 28
silence_duration_ms

Time of silence before the model concludes a user turn and responds 28

Advanced Transcriptions and Diarization
For use cases not requiring real-time response, the Audio API provides specialized models like gpt-4o-transcribe-diarize. This model is capable of identifying multiple speakers in a recording and mapping their segments to specific labels.29 Developers can provide up to four short audio references to map segments onto known speakers, a feature particularly useful for meeting summarization and legal documentation.29
Economic Modeling of Multimodal Contexts
The cost of operating audio-native models is calculated across two meters: audio duration and text tokens. This represents a more complex billing model than traditional LLMs, reflecting the significant compute required for audio processing.16
Token Costs and Optimization Strategies
Realtime API billing is accrued based on input and output tokens across text and audio modalities. To control costs, developers are encouraged to use strategies such as truncation and prompt caching.14
Modality
Input Cost (per 1M tokens)
Output Cost (per 1M tokens)
Cached Input Cost (per 1M tokens)
Text



Audio



Image

-


(Note: GPT-4o mini variants are significantly cheaper, with audio input at  and output at  per million tokens.31)
For a typical 10-minute conversation, costs can be estimated as follows:
Audio Input:  per minute.30
Audio Output:  per minute.30
Context Optimization: Silence in a continuous stream still counts toward input tokens unless VAD is utilized to filter "dead air".16
Truncation strategies are essential for managing context limits. A  context model with  max output tokens can only include  tokens in the context before older messages are dropped.14 Setting a retention_ratio of  ensures that when truncation occurs,  of the context is preserved, helping to maintain conversational memory while improving cache hit rates.14
Case Study: Visual and Auditory Accessibility with Be My Eyes
The deployment of GPT-4o within the "Be My Eyes" platform provides a compelling case study for the real-world impact of multimodal models. Since 2012, Be My Eyes has connected blind and low-vision users with human volunteers. The introduction of the "Virtual Volunteer," powered by GPT-4o, has transformed this service into an always-available assistive tool.32
Environmental Awareness and Proactive Perception
Unlike previous image-to-text tools, GPT-4o can maintain a conversation about visual input. In the "VisAssistDaily" benchmark, GPT-4o achieved the highest task success rate (TSR) across basic skills, home life, and social tasks.33
Task Category
GPT-4o TSR (English)
GPT-4o TSR (Chinese)
VITA-1.5 TSR (English)
Basic Skills



Home Life Tasks



Social Life Tasks




The model’s environmental awareness is demonstrated in its ability to identify "orange lights" on taxis, recognize "royal standard flags" flying over Buckingham Palace, and advise users on when to wave down a vehicle.34 However, researchers have identified a "Proactive Perception" challenge, where models occasionally struggle to perceive potential hazards in dynamic environments, such as recognizing stairs or oncoming obstacles.33 To address this, the "SafeVid" dataset has been introduced to help models proactively detect environmental risks through polling mechanisms.33
Safety, Red Teaming, and Risk scorecard
OpenAI’s Preparedness Framework governs the evaluation of frontier risks across four primary categories. Before its general release, GPT-4o underwent extensive external red teaming involving over  experts in social psychology, bias, and misinformation.1
Preparedness Framework Risk Levels
The model's risk profile remains "Low" in most critical categories, with "Persuasion" being the only category to reach a borderline "Medium" score.36
Risk Category
Pre-Mitigation Score
Post-Mitigation Score
Cybersecurity
Low
Low
CBRN (Chemical, Biological, etc.)
Low
Low
Persuasion
Medium
Medium
Model Autonomy
Low
Low

The "Medium" score in persuasion reflects the potential for multimodal models to be more convincing than text-only models due to their emotional resonance and vocal tone.36 Mitigations include post-training the model to refuse to generate disallowed content, such as erotic speech, violent content, or ungrounded sensitive trait attribution (e.g., attributing personality traits based on voice).6
Mitigating Unauthorized Voice Generation
To prevent the model from being used as a tool for impersonation, GPT-4o is strictly limited to preset voices like Breeze, Cove, Ember, Juniper, and Shimmer.10 OpenAI employs a standalone output classifier that runs in a streaming fashion to detect if the model’s output deviates from these approved presets. Internal evaluations show this classifier catches  of meaningful deviations in English, effectively neutralizing the risk of unintentional voice cloning.6
The 2025-2026 Model Horizon: GPT-5 and Beyond
As of early 2026, the artificial intelligence landscape has been further transformed by the release of the GPT-5 series. While GPT-4o remains a "beloved model" for its warm personality and real-time voice stability, GPT-5 has established a new frontier in reasoning and enterprise utility.38
Architectural Advances in GPT-5
GPT-5 introduces a dual-mode reasoning architecture, allowing users to choose between "Instant" and "Thinking" modes. This approach addresses the inherent trade-off between response speed and analytical depth.39
Feature
GPT-4o (Omni)
GPT-5 (2025/2026)
Release Date
May 2024
August 2025
Context Window (API)
 tokens
 tokens
Context Window (ChatGPT)
 tokens
 tokens
Reasoning Paradigm
Single Model
Dual-Mode (Fast + Deep)
Hallucination Rate
Baseline
 Reduction (vs. 4o)
Primary Strength
Creative / Emotional
Technical / Enterprise

GPT-5’s "Thinking" mode allows it to solve PhD-level science questions (scoring  vs.  for 4o) and dominate coding benchmarks like SWE-bench Verified ( vs. ).39 However, users have noted that GPT-5 often feels more "robotic" and "corporate" compared to GPT-4o’s warm, therapeutic tone, leading OpenAI to reintroduce GPT-4o for paid subscribers who preferred its conversational aesthetic.10
The Emergence of Agentic AI: GPT-5.3 Codex
The most recent evolution, GPT-5.3 Codex (released February 2026), marks a step-change from simple code generation to general-purpose coding agents.41 This model is the first to combine the Codex and GPT-5 training stacks, enabling it to actively steer multi-step coding workflows, check documentation, and debug with minimal human intervention.39 This suggests that the future of audio models lies in "agentic" interaction, where voice interfaces serve as the control layer for autonomous systems that can execute complex tasks on behalf of the user.
Future Outlook and Technological Convergence
The trajectory of direct audio models is moving toward a total synthesis of sensory data and reasoning. As unsupervised learning continues to scale, models are developing a deeper "world model," reducing hallucinations and improving associative thinking.37 The integration of "Instruction Hierarchies" in GPT-4.5 and GPT-5 helps models better prioritize safety instructions over adversarial user prompts, making them more robust for sensitive applications in healthcare and finance.37
Cognitive and Emotional Intelligence (EQ)
The next generation of models is characterized by increased "EQ"—the ability to recognize subtle emotional cues and implicit expectations.37 GPT-4.5, for instance, is trained to know when to offer advice, when to defuse frustration, or when to simply listen.37 This emotional alignment is critical for use cases in mental health support and education, where the "how" of a response is often as important as the "what."
The Retirement of Legacy Systems
By February 2026, OpenAI had begun retiring legacy models, including the original GPT-5 (Instant and Thinking) and GPT-4o from the ChatGPT interface, to focus on the more unified GPT-5.2 and 5.3 ecosystems.41 However, the "omni" paradigm established by GPT-4o remains the foundational architecture for all subsequent releases, proving that the move away from cascaded pipelines was a permanent and necessary step toward truly intelligent human-machine collaboration.
Conclusions and Practical Recommendations
The research into OpenAI’s audio-native models confirms that end-to-end multimodal training is the definitive path forward for real-time AI. For organizations and developers, several key conclusions emerge:
Latency is the Critical Variable: The transition from  seconds to  milliseconds of latency is not just a performance boost; it is a qualitative shift that enables entirely new categories of applications, from real-time translation to accessibility tools for the visually impaired.5
Multimodal Training Preserves Information: By avoiding intermediate text transcriptions, models can reason about the "hidden" signals in audio, such as emotion, sarcasm, and environment, which are vital for nuanced communication.1
Safety is an Architectural Priority: The use of preset voices, output classifiers, and post-training refusals is essential for mitigating the high risks associated with synthetic voice generation and impersonation.6
Efficiency Drives Global Adoption: New tokenization strategies have made advanced AI economically viable for non-Latin languages, opening markets that were previously underserved by high-token-cost models.1
As we look toward the further evolution of the GPT-5 series and the integration of agentic capabilities, the focus will likely shift from simple "chat" interfaces to "omni-agents" that can perceive the world with human-like fidelity and act with expert-level precision. The technical groundwork laid by GPT-4o remains the most significant milestone in this journey toward a unified, intelligent, and responsive digital companion.
Works cited
Hello GPT-4o | OpenAI, accessed February 7, 2026, https://openai.com/index/hello-gpt-4o/
A Preliminary Exploration with GPT-4o Voice Mode - arXiv, accessed February 7, 2026, https://arxiv.org/html/2502.09940v1
What Is GPT-4o? | IBM, accessed February 7, 2026, https://www.ibm.com/think/topics/gpt-4o
[2410.21276] GPT-4o System Card - arXiv, accessed February 7, 2026, https://arxiv.org/abs/2410.21276
GPT-4o Guide: How it Works, Use Cases, Pricing, Benchmarks | DataCamp, accessed February 7, 2026, https://www.datacamp.com/blog/what-is-gpt-4o
GPT-4o System Card - arXiv, accessed February 7, 2026, https://arxiv.org/html/2410.21276v1
GPT-4 vs GPT-4o | Better Stack Community, accessed February 7, 2026, https://betterstack.com/community/guides/ai/gpt-4-vs-gpt-4o/
Mini-Omni2: Towards Open-source GPT-4o Model with Vision, Speech and Duplex - arXiv, accessed February 7, 2026, https://arxiv.org/html/2410.11190v1
OpenAI Realtime API Use Cases 2025: 10 Real Examples - Skywork ai, accessed February 7, 2026, https://skywork.ai/blog/ai-agent/openai-realtime-api-use-cases-2025-10-real-examples/
GPT-4o - Wikipedia, accessed February 7, 2026, https://en.wikipedia.org/wiki/GPT-4o
GPT-4o Audio Model | OpenAI API, accessed February 7, 2026, https://platform.openai.com/docs/models/gpt-4o-audio-preview
Neural audio codecs: how to get audio into LLMs - Kyutai, accessed February 7, 2026, https://kyutai.org/codec-explainer
hubertsiuzdak/snac: Multi-Scale Neural Audio Codec (SNAC) compresses audio into discrete codes at a low bitrate - GitHub, accessed February 7, 2026, https://github.com/hubertsiuzdak/snac
Realtime | OpenAI API Reference, accessed February 7, 2026, https://platform.openai.com/docs/api-reference/realtime
Calls | OpenAI API Reference, accessed February 7, 2026, https://platform.openai.com/docs/api-reference/realtime-calls
Managing costs | OpenAI API, accessed February 7, 2026, https://platform.openai.com/docs/guides/realtime-costs
Top 5 Real-Time Speech-to-Speech APIs and Libraries To Build Voice Agents, accessed February 7, 2026, https://getstream.io/blog/speech-apis/
Introducing next-generation audio models in the API | OpenAI, accessed February 7, 2026, https://openai.com/index/introducing-our-next-generation-audio-models/
毓翔 林 - alphaXiv, accessed February 7, 2026, https://www.alphaxiv.org/@yu-xiang-lin
A Preliminary Exploration with GPT-4o Voice Mode - ResearchGate, accessed February 7, 2026, https://www.researchgate.net/publication/389056271_A_Preliminary_Exploration_with_GPT-4o_Voice_Mode
Comparative Analysis of Streaming ASR Systems: A Technical Benchmark Study, accessed February 7, 2026, https://smallest.ai/blog/comparative-analysis-of-streaming-asr-systems-a-technical-benchmark-study
Voice Engine - Navigating the Challenges and Opportunities of Synthetic Voices, accessed February 7, 2026, https://community.openai.com/t/voice-engine-navigating-the-challenges-and-opportunities-of-synthetic-voices/701714
Expanding on how Voice Engine works and our safety research - OpenAI, accessed February 7, 2026, https://openai.com/index/expanding-on-how-voice-engine-works-and-our-safety-research/
OpenAI holds back wide release of voice-cloning tech due to misuse concerns - Reddit, accessed February 7, 2026, https://www.reddit.com/r/technology/comments/1bqvuyq/openai_holds_back_wide_release_of_voicecloning/
OpenAI unveils its Voice Engine tool that can replicate people's voices - YouTube, accessed February 7, 2026, https://www.youtube.com/watch?v=qidszBIfkpc
OpenAI Promised and Failed to Launch Its Voice Cloning Tool - AutoGPT, accessed February 7, 2026, https://autogpt.net/openai-promised-and-failed-to-launch-its-voice-cloning-tool/
Realtime API | OpenAI API - OpenAI Platform, accessed February 7, 2026, https://platform.openai.com/docs/guides/realtime
Realtime Beta session tokens | OpenAI API Reference, accessed February 7, 2026, https://platform.openai.com/docs/api-reference/realtime-beta-sessions
Speech to text | OpenAI API, accessed February 7, 2026, https://platform.openai.com/docs/guides/speech-to-text
OpenAI Realtime API Pricing 2025: Cost Calculator - Skywork.ai, accessed February 7, 2026, https://skywork.ai/blog/agent/openai-realtime-api-pricing-2025-cost-calculator/
API Pricing - OpenAI, accessed February 7, 2026, https://openai.com/api/pricing/
Be My Eyes - Transforming visual accessibility - OpenAI, accessed February 7, 2026, https://openai.com/index/be-my-eyes/
“I Can See Forever!”: Evaluating Real-time VideoLLMs for Assisting Individuals with Visual Impairments - arXiv, accessed February 7, 2026, https://arxiv.org/html/2505.04488v1
Be My Eyes Accessibility with GPT-4o - YouTube, accessed February 7, 2026, https://www.youtube.com/watch?v=Zq710AKC1gg
Be My Eyes Accessibility with GPT-4o - YouTube, accessed February 7, 2026, https://www.youtube.com/watch?v=KwNUJ69RbwY
GPT-4o System Card | OpenAI, accessed February 7, 2026, https://openai.com/index/gpt-4o-system-card/
OpenAI GPT-4.5 System Card, accessed February 7, 2026, https://cdn.openai.com/gpt-4-5-system-card-2272025.pdf
What are the differences between OpenAI's GPT 5 and GPT 4o? - Panda Security, accessed February 7, 2026, https://www.pandasecurity.com/en/mediacenter/what-are-the-differences-between-openais-gpt-5-and-gpt-4o/
GPT-5 vs GPT-4o: Which OpenAI Model Is Better in 2025? - Belsterns Technologies, accessed February 7, 2026, https://blog.belsterns.com/post/gpt-5-vs-gpt-4o-which-openai-model-is-better-in-2025
GPT-5 vs GPT-4o: Is the latest OpenAI model better than its most beloved one? - Analytics Vidhya, accessed February 7, 2026, https://www.analyticsvidhya.com/blog/2025/08/gpt-5-vs-gpt-4o/
Model Release Notes | OpenAI Help Center, accessed February 7, 2026, https://help.openai.com/en/articles/9624314-model-release-notes
Introducing GPT-4.5 - OpenAI, accessed February 7, 2026, https://openai.com/index/introducing-gpt-4-5/
ChatGPT — Release Notes - OpenAI Help Center, accessed February 7, 2026, https://help.openai.com/en/articles/6825453-chatgpt-release-notes
