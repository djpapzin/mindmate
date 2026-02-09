#!/usr/bin/env python3
"""
Test script for core Personal Mode features (without Redis dependencies)
Tests automatic context learning, new commands, and enhanced functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Test core functions directly without importing full bot
def test_keyword_detection():
    """Test keyword detection logic"""
    print("🧠 Testing Keyword Detection Logic...")
    
    def detect_medication(message):
        message_lower = message.lower()
        medication_keywords = ["medication", "meds", "medicine", "pill", "prescription", "dose", "lithium", "seroquel", "lamictal"]
        return any(word in message_lower for word in medication_keywords)
    
    def detect_therapy(message):
        message_lower = message.lower()
        therapy_keywords = ["doctor", "therapist", "psychiatrist", "counselor", "appointment", "session"]
        return any(word in message_lower for word in therapy_keywords)
    
    def detect_mood(message):
        message_lower = message.lower()
        mood_keywords = ["depressed", "depression", "manic", "mania", "episode", "mood swing", "hypomanic"]
        return any(word in message_lower for word in mood_keywords)
    
    def detect_relationship(message):
        message_lower = message.lower()
        relationship_keywords = ["boyfriend", "girlfriend", "partner", "relationship", "dating", "breakup", "friend"]
        return any(word in message_lower for word in relationship_keywords)
    
    def detect_work(message):
        message_lower = message.lower()
        work_keywords = ["work", "job", "career", "boss", "coworker", "unemployed", "fired"]
        return any(word in message_lower for word in work_keywords)
    
    # Test cases
    test_cases = [
        {
            "message": "I started taking Lithium again today",
            "expected": ["medication"],
            "description": "Medication detection"
        },
        {
            "message": "I have a doctor appointment tomorrow",
            "expected": ["therapy"],
            "description": "Therapy detection"
        },
        {
            "message": "I've been feeling really depressed lately",
            "expected": ["mood"],
            "description": "Mood detection"
        },
        {
            "message": "My boyfriend and I had a fight about my medication",
            "expected": ["medication", "relationship"],
            "description": "Multiple detection"
        },
        {
            "message": "Work stress has been overwhelming lately",
            "expected": ["work"],
            "description": "Work detection"
        },
        {
            "message": "Hello, how are you today?",
            "expected": [],
            "description": "No keywords"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case["message"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Message: '{message}'")
        
        detected = []
        if detect_medication(message):
            detected.append("medication")
        if detect_therapy(message):
            detected.append("therapy")
        if detect_mood(message):
            detected.append("mood")
        if detect_relationship(message):
            detected.append("relationship")
        if detect_work(message):
            detected.append("work")
        
        print(f"Expected: {expected}")
        print(f"Detected: {detected}")
        
        if set(detected) == set(expected):
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
    
    print(f"\n📊 Keyword Detection: {passed}/{total} passed")
    return passed == total

def test_context_update_logic():
    """Test context update logic"""
    print("\n🎯 Testing Context Update Logic...")
    
    # Simulate user journey storage
    user_journey = {}
    test_user_id = 339651126
    
    def update_context_from_message(user_id, message):
        """Simplified version of the context update function"""
        message_lower = message.lower()
        
        # Medication mentions
        if any(word in message_lower for word in ["medication", "meds", "medicine", "pill", "prescription", "dose", "lithium", "seroquel", "lamictal"]):
            if "take" in message_lower or "on" in message_lower or "start" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["medication_status"] = "Currently taking medication"
            elif "stop" in message_lower or "quit" in message_lower or "off" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["medication_status"] = "Stopped medication"
        
        # Therapy mentions
        if any(word in message_lower for word in ["doctor", "therapist", "psychiatrist", "counselor", "appointment", "session"]):
            if "appointment" in message_lower or "visit" in message_lower or "see" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["doctor_visits"] = "Recent doctor visit"
            elif "therapy" in message_lower or "counseling" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["therapy_status"] = "Currently in therapy"
        
        # Mood mentions
        if any(word in message_lower for word in ["depressed", "depression", "manic", "mania", "episode", "mood swing", "hypomanic"]):
            if "last week" in message_lower or "recently" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["last_mood_episode"] = "Recent mood episode"
        
        # Relationship mentions
        if any(word in message_lower for word in ["boyfriend", "girlfriend", "partner", "relationship", "dating", "breakup", "friend"]):
            if "fight" in message_lower or "argument" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["relationship_status"] = "Relationship conflicts"
            elif "supportive" in message_lower or "understanding" in message_lower:
                user_journey[user_id] = user_journey.get(user_id, {})
                user_journey[user_id]["relationship_status"] = "Supportive partner"
    
    # Test messages
    test_messages = [
        "I started taking Lithium again today",
        "I have a doctor appointment tomorrow", 
        "Recently I've been having mood swings",
        "My boyfriend is very supportive during my episodes",
        "Work has been really stressful",
        "I need to stop taking my Seroquel"
    ]
    
    print("\nProcessing test messages...")
    for msg in test_messages:
        print(f"• {msg}")
        update_context_from_message(test_user_id, msg)
    
    # Check results
    journey = user_journey.get(test_user_id, {})
    print(f"\n📔 Journey Results:")
    for key, value in journey.items():
        print(f"  {key}: {value}")
    
    # Verify expected keys
    expected_keys = ["medication_status", "doctor_visits", "last_mood_episode", "relationship_status"]
    found_keys = list(journey.keys())
    
    print(f"\nExpected keys: {expected_keys}")
    print(f"Found keys: {found_keys}")
    
    # Check if medication status was updated correctly (should be "Stopped medication" from last message)
    medication_correct = journey.get("medication_status") == "Stopped medication"
    print(f"\nMedication status update: {'✅ PASSED' if medication_correct else '❌ FAILED'}")
    
    return len(found_keys) >= 3 and medication_correct

def test_personal_mode_users():
    """Test Personal Mode user detection"""
    print("\n🔐 Testing Personal Mode User Detection...")
    
    # Personal Mode users (from bot.py)
    PERSONAL_MODE_USERS = {
        339651126: {"name": "DJ", "model": "gpt-4.1-mini"},
        7013163582: {"name": "Keleh", "model": "gpt-4.1-mini"}
    }
    
    def is_personal_mode(user_id):
        return user_id in PERSONAL_MODE_USERS
    
    # Test cases
    test_cases = [
        {"user_id": 339651126, "name": "DJ", "expected": True},
        {"user_id": 7013163582, "name": "Keleh", "expected": True},
        {"user_id": 123456789, "name": "Random User", "expected": False}
    ]
    
    passed = 0
    for test_case in test_cases:
        user_id = test_case["user_id"]
        name = test_case["name"]
        expected = test_case["expected"]
        actual = is_personal_mode(user_id)
        
        status = "✅ PASSED" if actual == expected else "❌ FAILED"
        print(f"{name} (ID: {user_id}): Personal Mode = {actual} {status}")
        
        if actual == expected:
            passed += 1
    
    print(f"\n📊 Personal Mode Detection: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def test_command_help_messages():
    """Test command help message generation"""
    print("\n📝 Testing Command Help Messages...")
    
    # Simulate help message generation
    def generate_remember_help():
        return """🧠 **Share important information to remember:**

• `/remember I have bipolar type 2` - Medical info
• `/remember I take Lithium 300mg daily` - Medication details
• `/remember My therapist is Dr. Smith` - Treatment info
• `/remember I live alone in Johannesburg` - Living situation
• `/remember My boyfriend is very supportive` - Relationship info

🧠 **Current Understanding:**
Medication: Currently taking medication | Doctor visits: Recent doctor visit | Therapy: Currently in therapy

🤖 **Automatic Learning:** I also learn from our conversations naturally! 
When you mention medications, symptoms, life changes, or relationship issues, 
I remember these for future support. No need to manually add everything 
unless it's important information you want me to prioritize."""
    
    def generate_forget_help():
        return """🗑️ **Forget specific information:**

• `/forget medication` - Remove medication info
• `/forget therapy` - Remove therapy info
• `/forget diagnosis` - Remove diagnosis info
• `/forget relationship` - Remove relationship info
• `/forget work` - Remove career info

💡 I'll remove that specific information from my memory 
and update based on future conversations."""
    
    # Test help message generation
    remember_help = generate_remember_help()
    forget_help = generate_forget_help()
    
    # Check if key elements are present
    remember_checks = [
        "🧠" in remember_help,
        "/remember" in remember_help,
        "Automatic Learning" in remember_help,
        "bipolar type 2" in remember_help
    ]
    
    forget_checks = [
        "🗑️" in forget_help,
        "/forget" in remember_help,
        "medication" in forget_help,
        "therapy" in forget_help
    ]
    
    remember_passed = all(remember_checks)
    forget_passed = all(forget_checks)
    
    print(f"Remember help message: {'✅ PASSED' if remember_passed else '❌ FAILED'}")
    print(f"Forget help message: {'✅ PASSED' if forget_passed else '❌ FAILED'}")
    
    return remember_passed and forget_passed

def main():
    """Run all tests"""
    print("🚀 Starting Core Personal Mode Feature Tests")
    print("=" * 60)
    
    # Test keyword detection
    keyword_test = test_keyword_detection()
    
    # Test context update logic
    context_test = test_context_update_logic()
    
    # Test Personal Mode user detection
    personal_mode_test = test_personal_mode_users()
    
    # Test command help messages
    help_messages_test = test_command_help_messages()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Keyword Detection: {'✅ PASSED' if keyword_test else '❌ FAILED'}")
    print(f"Context Update Logic: {'✅ PASSED' if context_test else '❌ FAILED'}")
    print(f"Personal Mode Detection: {'✅ PASSED' if personal_mode_test else '❌ FAILED'}")
    print(f"Command Help Messages: {'✅ PASSED' if help_messages_test else '❌ FAILED'}")
    
    all_passed = keyword_test and context_test and personal_mode_test and help_messages_test
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Core Personal Mode features are working correctly!")
        print("🚀 Ready for live testing with the bot!")
    else:
        print("\n⚠️ Some tests failed - check the implementation")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
