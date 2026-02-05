"""
MindMate Bot Test Script
Tests core functionality without needing Telegram
Run: python test_bot.py
"""

import sys

# Import bot functions
from bot import (
    detect_crisis_keywords,
    get_conversation_history,
    add_to_history,
    clear_conversation_history,
    conversation_history,
    CRISIS_KEYWORDS,
    MAX_HISTORY_LENGTH
)


def test_crisis_detection():
    """Test crisis keyword detection."""
    print("\n" + "="*50)
    print("TEST 1: Crisis Keyword Detection")
    print("="*50)
    
    # Should trigger crisis response
    crisis_messages = [
        "I want to kill myself",
        "feeling suicidal today",
        "I want to end it all",
        "thinking about self-harm",
        "no reason to live anymore",
        "I WANT TO DIE",  # Test case insensitivity
    ]
    
    # Should NOT trigger crisis response
    safe_messages = [
        "I'm feeling stressed",
        "I had a bad day",
        "I'm anxious about work",
        "feeling down lately",
        "I killed it at my presentation!",  # False positive check
    ]
    
    print("\n🚨 Messages that SHOULD trigger crisis response:")
    all_passed = True
    for msg in crisis_messages:
        result = detect_crisis_keywords(msg)
        status = "✅ PASS" if result else "❌ FAIL"
        if not result:
            all_passed = False
        print(f"  {status}: '{msg[:40]}...' → Detected: {result}")
    
    print("\n✅ Messages that should NOT trigger crisis response:")
    for msg in safe_messages:
        result = detect_crisis_keywords(msg)
        status = "✅ PASS" if not result else "❌ FAIL"
        if result:
            all_passed = False
        print(f"  {status}: '{msg[:40]}' → Detected: {result}")
    
    return all_passed


def test_conversation_history():
    """Test conversation history management."""
    print("\n" + "="*50)
    print("TEST 2: Conversation History Management")
    print("="*50)
    
    # Clear any existing history
    conversation_history.clear()
    
    user_id_1 = 111111
    user_id_2 = 222222
    
    all_passed = True
    
    # Test 1: Empty history
    print("\n📝 Test empty history:")
    history = get_conversation_history(user_id_1)
    if history == []:
        print("  ✅ PASS: New user has empty history")
    else:
        print("  ❌ FAIL: New user should have empty history")
        all_passed = False
    
    # Test 2: Add messages
    print("\n📝 Test adding messages:")
    add_to_history(user_id_1, "user", "Hello, my name is Alice")
    add_to_history(user_id_1, "assistant", "Hello Alice! How can I help?")
    
    history = get_conversation_history(user_id_1)
    if len(history) == 2:
        print(f"  ✅ PASS: User 1 has {len(history)} messages")
    else:
        print(f"  ❌ FAIL: Expected 2 messages, got {len(history)}")
        all_passed = False
    
    # Test 3: User isolation
    print("\n📝 Test user isolation:")
    add_to_history(user_id_2, "user", "Hi, I'm Bob")
    add_to_history(user_id_2, "assistant", "Hello Bob!")
    
    history_1 = get_conversation_history(user_id_1)
    history_2 = get_conversation_history(user_id_2)
    
    if len(history_1) == 2 and len(history_2) == 2:
        print(f"  ✅ PASS: User 1 has {len(history_1)} msgs, User 2 has {len(history_2)} msgs")
    else:
        print("  ❌ FAIL: Users should have separate histories")
        all_passed = False
    
    # Check content isolation
    if "Alice" in str(history_1) and "Bob" not in str(history_1):
        print("  ✅ PASS: User 1 only sees Alice's conversation")
    else:
        print("  ❌ FAIL: User histories are mixed!")
        all_passed = False
    
    # Test 4: History limit
    print(f"\n📝 Test history limit (max {MAX_HISTORY_LENGTH} messages):")
    test_user = 333333
    for i in range(15):
        add_to_history(test_user, "user", f"Message {i}")
        add_to_history(test_user, "assistant", f"Response {i}")
    
    history = get_conversation_history(test_user)
    if len(history) == MAX_HISTORY_LENGTH:
        print(f"  ✅ PASS: History limited to {MAX_HISTORY_LENGTH} messages")
        # Check that oldest messages were dropped
        if "Message 0" not in str(history):
            print("  ✅ PASS: Oldest messages were correctly dropped")
        else:
            print("  ❌ FAIL: Old messages should be dropped")
            all_passed = False
    else:
        print(f"  ❌ FAIL: Expected {MAX_HISTORY_LENGTH}, got {len(history)}")
        all_passed = False
    
    # Test 5: Clear history
    print("\n📝 Test clear history:")
    clear_conversation_history(user_id_1)
    history = get_conversation_history(user_id_1)
    if history == []:
        print("  ✅ PASS: History cleared successfully")
    else:
        print("  ❌ FAIL: History should be empty after clear")
        all_passed = False
    
    # Verify other user unaffected
    history_2 = get_conversation_history(user_id_2)
    if len(history_2) == 2:
        print("  ✅ PASS: Other user's history unaffected")
    else:
        print("  ❌ FAIL: Clearing one user affected another!")
        all_passed = False
    
    return all_passed


def test_message_format():
    """Test that history is formatted correctly for OpenAI."""
    print("\n" + "="*50)
    print("TEST 3: Message Format for OpenAI")
    print("="*50)
    
    conversation_history.clear()
    user_id = 444444
    
    add_to_history(user_id, "user", "Hello")
    add_to_history(user_id, "assistant", "Hi there!")
    add_to_history(user_id, "user", "How are you?")
    
    history = get_conversation_history(user_id)
    
    all_passed = True
    
    # Check format
    print("\n📝 Checking message format:")
    expected_roles = ["user", "assistant", "user"]
    for i, msg in enumerate(history):
        if "role" in msg and "content" in msg:
            if msg["role"] == expected_roles[i]:
                print(f"  ✅ PASS: Message {i+1} has correct format: {msg}")
            else:
                print(f"  ❌ FAIL: Wrong role order at message {i+1}")
                all_passed = False
        else:
            print(f"  ❌ FAIL: Message missing 'role' or 'content' keys")
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "🤖 "*20)
    print("   MINDMATE BOT TEST SUITE")
    print("🤖 "*20)
    
    results = {
        "Crisis Detection": test_crisis_detection(),
        "Conversation History": test_conversation_history(),
        "Message Format": test_message_format(),
    }
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        if not passed:
            all_passed = False
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Review above for details")
    print("="*50 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
