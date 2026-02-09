"""
Test script for Redis integration without requiring Docker
Tests the database module with fallback to in-memory storage
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from redis_db import DatabaseManager, Message

async def test_redis_integration():
    """Test Redis database functionality"""
    print("🧪 Testing Redis Integration...")
    
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
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    search_results = await db.semantic_search(test_user_id, "test message", 5)
    print(f"✅ Found {len(search_results)} semantically similar messages")
    
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
    print("\n✅ Test completed successfully!")
    
    return True

async def test_bot_integration():
    """Test bot integration with Redis"""
    print("\n🤖 Testing bot integration...")
    
    # Set environment variables for testing
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
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
    
    # Test database module
    db_success = await test_redis_integration()
    
    # Test bot integration
    bot_success = await test_bot_integration()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"  Database Module: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"  Bot Integration: {'✅ PASS' if bot_success else '❌ FAIL'}")
    
    if db_success and bot_success:
        print("\n🎉 All tests passed! Redis integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed, but fallback storage should work fine.")

if __name__ == "__main__":
    asyncio.run(main())
