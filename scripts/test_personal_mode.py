#!/usr/bin/env python3
"""
Test script for Personal Mode features
Tests automatic context learning, new commands, and enhanced functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bot import (
    update_context_from_message, 
    get_user_journey_summary,
    user_journey,
    is_personal_mode,
    PERSONAL_MODE_USERS
)

def test_automatic_context_learning():
    """Test automatic context learning from messages"""
    print("🧠 Testing Automatic Context Learning...")
    
    # Test user ID (DJ - Personal Mode)
    test_user_id = 339651126
    
    # Clear existing journey for clean test
    if test_user_id in user_journey:
        del user_journey[test_user_id]
    
    # Test medication detection
    print("\n💊 Testing medication detection...")
    update_context_from_message(test_user_id, "I started taking Lithium again today")
    update_context_from_message(test_user_id, "I miss my meds sometimes when I'm busy")
    
    # Test therapy detection  
    print("\n👨‍⚕️ Testing therapy detection...")
    update_context_from_message(test_user_id, "I have a doctor appointment tomorrow")
    update_context_from_message(test_user_id, "My therapy session went well today")
    
    # Test mood detection
    print("\n😔 Testing mood detection...")
    update_context_from_message(test_user_id, "I've been feeling really depressed lately")
    update_context_from_message(test_user_id, "Last week I had a manic episode")
    
    # Test relationship detection
    print("\n💕 Testing relationship detection...")
    update_context_from_message(test_user_id, "My boyfriend and I had a fight about my medication")
    update_context_from_message(test_user_id, "My partner is very supportive during my episodes")
    
    # Test work detection
    print("\n💼 Testing work detection...")
    update_context_from_message(test_user_id, "Work stress has been overwhelming lately")
    update_context_from_message(test_user_id, "I'm feeling overwhelmed at my job")
    
    # Get journey summary
    summary = get_user_journey_summary(test_user_id)
    print(f"\n📔 Journey Summary:\n{summary}")
    
    return summary

def test_personal_mode_detection():
    """Test Personal Mode user detection"""
    print("\n🔐 Testing Personal Mode Detection...")
    
    # Test DJ (should be Personal Mode)
    dj_user_id = 339651126
    dj_personal = is_personal_mode(dj_user_id)
    print(f"DJ (ID: {dj_user_id}) - Personal Mode: {dj_personal} ✅" if dj_personal else f"DJ (ID: {dj_user_id}) - Personal Mode: {dj_personal} ❌")
    
    # Test Keleh (should be Personal Mode)  
    keleh_user_id = 7013163582
    keleh_personal = is_personal_mode(keleh_user_id)
    print(f"Keleh (ID: {keleh_user_id}) - Personal Mode: {keleh_personal} ✅" if keleh_personal else f"Keleh (ID: {keleh_user_id}) - Personal Mode: {keleh_personal} ❌")
    
    # Test random user (should NOT be Personal Mode)
    random_user_id = 123456789
    random_personal = is_personal_mode(random_user_id)
    print(f"Random User (ID: {random_user_id}) - Personal Mode: {random_personal} ✅" if not random_personal else f"Random User (ID: {random_user_id}) - Personal Mode: {random_personal} ❌")
    
    return dj_personal and keleh_personal and not random_personal

def test_context_update_patterns():
    """Test specific context update patterns"""
    print("\n🎯 Testing Context Update Patterns...")
    
    test_user_id = 339651126
    
    # Clear existing journey
    if test_user_id in user_journey:
        del user_journey[test_user_id]
    
    test_cases = [
        {
            "message": "I need to stop taking my Seroquel",
            "expected_key": "medication_status",
            "expected_value": "Stopped medication"
        },
        {
            "message": "I started therapy with Dr. Smith",
            "expected_key": "therapy_status", 
            "expected_value": "Currently in therapy"
        },
        {
            "message": "Recently I've been having mood swings",
            "expected_key": "last_mood_episode",
            "expected_value": "Recent mood episode"
        },
        {
            "message": "My sister helps me when I'm depressed",
            "expected_key": "family_support",
            "expected_value": "Has family support"
        },
        {
            "message": "I live alone in my apartment",
            "expected_key": "living_situation",
            "expected_value": "Living independently"
        },
        {
            "message": "Work has been really stressful",
            "expected_key": "career_status",
            "expected_value": "Work stress affecting mental health"
        },
        {
            "message": "My girlfriend doesn't understand my bipolar",
            "expected_key": "relationship_status",
            "expected_value": "Relationship conflicts"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case["message"]
        expected_key = test_case["expected_key"]
        expected_value = test_case["expected_value"]
        
        print(f"\nTest {i}: {message}")
        update_context_from_message(test_user_id, message)
        
        # Check if expected key and value are in journey
        journey = user_journey.get(test_user_id, {})
        actual_value = journey.get(expected_key)
        
        if actual_value == expected_value:
            print(f"✅ PASSED: {expected_key} = {actual_value}")
            passed_tests += 1
        else:
            print(f"❌ FAILED: Expected {expected_key} = {expected_value}, got {actual_value}")
    
    print(f"\n📊 Context Update Tests: {passed_tests}/{total_tests} passed")
    return passed_tests == total_tests

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n⚠️ Testing Edge Cases...")
    
    test_user_id = 339651126
    
    # Test empty message
    print("\nTesting empty message...")
    try:
        update_context_from_message(test_user_id, "")
        print("✅ Empty message handled gracefully")
    except Exception as e:
        print(f"❌ Empty message caused error: {e}")
        return False
    
    # Test message with no keywords
    print("\nTesting message with no keywords...")
    initial_journey_size = len(user_journey.get(test_user_id, {}))
    update_context_from_message(test_user_id, "Hello, how are you today?")
    final_journey_size = len(user_journey.get(test_user_id, {}))
    
    if initial_journey_size == final_journey_size:
        print("✅ No-keyword message handled correctly (no changes)")
    else:
        print("❌ No-keyword message caused unexpected changes")
        return False
    
    # Test case sensitivity
    print("\nTesting case sensitivity...")
    update_context_from_message(test_user_id, "I take LITHIUM every day")
    journey = user_journey.get(test_user_id, {})
    if "medication_status" in journey:
        print("✅ Case insensitive keyword detection works")
    else:
        print("❌ Case insensitive keyword detection failed")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Personal Mode Feature Tests")
    print("=" * 50)
    
    # Test Personal Mode detection
    personal_mode_test = test_personal_mode_detection()
    
    # Test automatic context learning
    context_learning_summary = test_automatic_context_learning()
    
    # Test context update patterns
    context_patterns_test = test_context_update_patterns()
    
    # Test edge cases
    edge_cases_test = test_edge_cases()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Personal Mode Detection: {'✅ PASSED' if personal_mode_test else '❌ FAILED'}")
    print(f"Context Learning: {'✅ WORKING' if context_learning_summary else '❌ FAILED'}")
    print(f"Context Patterns: {'✅ PASSED' if context_patterns_test else '❌ FAILED'}")
    print(f"Edge Cases: {'✅ PASSED' if edge_cases_test else '❌ FAILED'}")
    
    all_passed = personal_mode_test and context_patterns_test and edge_cases_test
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if context_learning_summary:
        print(f"\n📔 Sample Journey Output:\n{context_learning_summary}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
