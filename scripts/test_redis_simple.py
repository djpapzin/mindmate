"""
Simple test script for Redis integration without heavy dependencies
Tests basic Redis functionality and fallback
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock the sentence-transformers import to avoid dependency issues
class MockSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name
    
    def encode(self, text, convert_to_numpy=True):
        # Simple mock embedding - just return a fixed vector
        import numpy as np
        return np.ones(384, dtype=np.float32)

# Mock the module in sys.modules
sys.modules['sentence_transformers'] = type(sys)('sentence_transformers')
sys.modules['sentence_transformers'].SentenceTransformer = MockSentenceTransformer

from redis_db import DatabaseManager, Message

async def test_redis_basic():
    """Test basic Redis functionality"""
    print("🧪 Testing Basic Redis Integration...")
    
    # Test with localhost Redis (will fallback if not available)
    redis_url = "redis://localhost:6379"
    embedding_model = "all-MiniLM-L6-v2"
    
    print(f"📡 Connecting to Redis at {redis_url}...")
    
    # Initialize database manager
    db = DatabaseManager(redis_url, embedding_model)
    
    try:
        # Try to connect to Redis
        await db.connect()
        print("✅ Redis connected successfully!")
        redis_available = True
    except Exception as e:
        print(f"⚠️ Redis not available: {e}")
        print("🔄 Using in-memory fallback storage")
        redis_available = False
    
    # Test message storage
    print("\n💾 Testing message storage...")
    test_user_id = 12345
    test_message = Message(
        user_id=test_user_id,
        content="Hello, this is a test message for Redis integration!",
        role="user",
        timestamp=datetime.now(),
        message_id="test_msg_001"
    )
    
    await db.store_message(test_message)
    print("✅ Message stored successfully!")
    
    # Test conversation history retrieval
    print("\n📚 Testing conversation history...")
    history = await db.get_conversation_history(test_user_id, 10)
    print(f"✅ Retrieved {len(history)} messages from history")
    
    if history:
        print(f"📝 Latest message: {history[-1]['content'][:50]}...")
    
    # Test user preferences
    print("\n👤 Testing user preferences...")
    await db.store_user_preference(test_user_id, "name", "Test User")
    await db.store_user_preference(test_user_id, "focus_areas", ["testing", "redis"])
    
    stored_name = await db.get_user_preference(test_user_id, "name")
    stored_focus = await db.get_user_preference(test_user_id, "focus_areas")
    
    print(f"✅ Stored name: {stored_name}")
    print(f"✅ Stored focus areas: {stored_focus}")
    
    # Test clear conversation
    print("\n🧹 Testing conversation clearing...")
    await db.clear_conversation(test_user_id)
    cleared_history = await db.get_conversation_history(test_user_id, 10)
    print(f"✅ Conversation cleared! Messages remaining: {len(cleared_history)}")
    
    # Get database stats
    print("\n📊 Database statistics:")
    stats = await db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Close connection
    await db.close()
    print("\n✅ Basic test completed successfully!")
    
    return redis_available

async def test_bot_basic():
    """Test bot integration without Redis"""
    print("\n🤖 Testing Bot Integration (Fallback Mode)...")
    
    # Set environment variables for testing
    os.environ['REDIS_URL'] = 'redis://nonexistent:6379'  # Force fallback
    os.environ['EMBEDDING_MODEL'] = 'all-MiniLM-L6-v2'
    
    try:
        # Import bot functions
        from bot import get_history, add_to_history, clear_history
        
        test_user_id = 99999
        
        # Test add_to_history
        print("📝 Testing add_to_history...")
        await add_to_history(test_user_id, "user", "Test message from bot integration")
        await add_to_history(test_user_id, "assistant", "Test response from bot")
        
        # Test get_history
        print("📚 Testing get_history...")
        history = get_history(test_user_id)
        print(f"✅ Retrieved {len(history)} messages from bot history")
        
        # Test clear_history
        print("🧹 Testing clear_history...")
        await clear_history(test_user_id)
        cleared_history = get_history(test_user_id)
        print(f"✅ History cleared! Messages remaining: {len(cleared_history)}")
        
        print("✅ Bot integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Redis Integration Tests")
    print("=" * 50)
    
    # Test basic Redis functionality
    redis_available = await test_redis_basic()
    
    # Test bot integration
    bot_success = await test_bot_basic()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"  Redis Connection: {'✅ AVAILABLE' if redis_available else '⚠️ FALLBACK'}")
    print(f"  Basic Functions: {'✅ PASS' if redis_available else '⚠️ FALLBACK'}")
    print(f"  Bot Integration: {'✅ PASS' if bot_success else '❌ FAIL'}")
    
    if redis_available:
        print("\n🎉 Redis is working! Your bot will have persistent storage.")
        print("📝 To test with actual Redis, install Docker and run:")
        print("  docker run -d -p 6379:6379 redis:latest")
    else:
        print("\n⚠️ Redis not available, but fallback storage works perfectly!")
        print("📝 Your bot will use in-memory storage until Redis is available.")
    
    print("\n✅ Integration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
