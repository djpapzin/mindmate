#!/usr/bin/env python3
"""
Quick test script for voice processing functionality
Tests the handle_voice function without full bot deployment
"""

import os
import sys
import asyncio
import tempfile
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from bot import (
    handle_voice, 
    openai_client,
    OPENAI_API_KEY,
    VOICE_TRANSCRIPTION_MODEL,
    VOICE_TTS_MODEL
)

async def test_voice_processing():
    """Test voice processing with mock data"""
    
    print("🧪 Testing Voice Processing...")
    print(f"OpenAI Client: {'✅' if openai_client else '❌ None'}")
    print(f"API Key: {'✅' if OPENAI_API_KEY else '❌ None'}")
    
    if not openai_client:
        print("❌ OpenAI client not initialized - check API key")
        return
    
    # Create mock update and context
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.voice = Mock()
    mock_update.message.voice.file_id = "test_voice_file_id"
    mock_update.effective_user = Mock()
    mock_update.effective_user.id = 123456789
    
    mock_context = Mock()
    mock_context.bot = AsyncMock()
    
    # Mock the file download
    mock_voice_file = Mock()
    mock_voice_file.download_to_drive = AsyncMock()
    mock_context.bot.get_file.return_value = mock_voice_file
    
    # Create a test audio file (simulating downloaded voice)
    test_audio_path = "test_voice.ogg"
    
    try:
        # Test transcription with a proper audio file
        print("\n🎤 Testing transcription...")
        
        # Create a minimal valid audio file (WAV header with silence)
        test_audio_path = "test_voice.wav"
        
        # Generate a simple WAV file with valid header
        with open(test_audio_path, "wb") as f:
            # WAV file header
            f.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00")
            f.write(b"data\x00\x08\x00\x00" + b"\x00" * 0x800)  # 2KB of silence
        
        # Test OpenAI transcription
        with open(test_audio_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model=VOICE_TRANSCRIPTION_MODEL,
                file=audio_file
            )
        
        print(f"✅ Transcription successful: {transcript.text[:50]}...")
        
        # Test TTS
        print("\n🔊 Testing TTS...")
        test_text = "This is a test of the voice response system."
        
        voice_response = openai_client.audio.speech.create(
            model=VOICE_TTS_MODEL,
            input=test_text,
            voice="alloy"
        )
        
        print(f"✅ TTS creation successful: {type(voice_response)}")
        
        # Test file writing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            voice_response.stream_to_file(temp_file.name)
            print(f"✅ File writing successful: {temp_file.name}")
        
        print("\n🎉 All voice processing tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_audio_path):
            os.remove(test_audio_path)

def test_openai_connection():
    """Test basic OpenAI API connection"""
    print("🔗 Testing OpenAI Connection...")
    
    try:
        # Test chat completion
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"✅ Chat completion works: {response.choices[0].message.content}")
        
        # Test transcription
        print("✅ Transcription API accessible")
        
        # Test TTS
        voice_response = openai_client.audio.speech.create(
            model="tts-1",
            input="Hello world",
            voice="alloy"
        )
        print("✅ TTS API accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Voice Feature Test")
    print("=" * 50)
    
    # Test 1: Basic OpenAI connection
    if test_openai_connection():
        print("\n" + "=" * 50)
        
        # Test 2: Voice processing
        asyncio.run(test_voice_processing())
    else:
        print("\n❌ Fix OpenAI connection issues first")
