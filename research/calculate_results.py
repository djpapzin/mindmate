#!/usr/bin/env python3
"""
Calculate results from the blind test markdown file.
Reads ratings and reveals which model won!
"""

import os
import re
import glob
from collections import defaultdict

def find_latest_test_file():
    """Find the most recent test results file."""
    pattern = os.path.join(os.path.dirname(__file__), "AB_TEST_RESULTS_*.md")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def parse_results(filepath: str) -> dict:
    """Parse the markdown file for ratings and mappings."""
    
    with open(filepath, "r") as f:
        content = f.read()
    
    # Extract ratings
    # Look for patterns like "**Rating:** 4 /5" or "**Rating:** 4/5" or "**Rating:** _4_ /5"
    rating_pattern = r"\*\*Rating:\*\*\s*_?(\d)_?\s*/5"
    ratings_raw = re.findall(rating_pattern, content)
    
    # Extract hidden mapping
    mapping_match = re.search(r"MAPPING_START\n(.*?)MAPPING_END", content, re.DOTALL)
    if not mapping_match:
        print("❌ Could not find mapping data in file!")
        return None
    
    mapping_lines = mapping_match.group(1).strip().split("\n")
    mappings = {}
    for line in mapping_lines:
        if "=" in line:
            key, value = line.split("=")
            mappings[key.strip()] = value.strip()
    
    # Count tests
    test_count = len([k for k in mappings if k.endswith("_A")]) 
    
    if len(ratings_raw) != test_count * 3:
        print(f"⚠️  Warning: Expected {test_count * 3} ratings, found {len(ratings_raw)}")
        print("   Make sure you rated all responses!")
        if len(ratings_raw) == 0:
            print("\n❌ No ratings found. Please edit the file and add ratings.")
            print("   Format: **Rating:** 4 /5")
            return None
    
    # Map ratings to models
    model_scores = defaultdict(list)
    
    for i in range(test_count):
        test_num = i + 1
        for j, letter in enumerate(["A", "B", "C"]):
            rating_idx = i * 3 + j
            if rating_idx < len(ratings_raw):
                rating = int(ratings_raw[rating_idx])
                model = mappings.get(f"TEST_{test_num}_{letter}", "Unknown")
                model_scores[model].append(rating)
    
    return {
        "test_count": test_count,
        "ratings_found": len(ratings_raw),
        "model_scores": dict(model_scores)
    }

def display_results(data: dict):
    """Display the final results."""
    
    print("\n" + "="*50)
    print("🏆 BLIND TEST RESULTS - REVEALED!")
    print("="*50 + "\n")
    
    print(f"📊 Total tests: {data['test_count']}")
    print(f"📝 Ratings collected: {data['ratings_found']}\n")
    
    # Calculate averages
    averages = {}
    for model, scores in data['model_scores'].items():
        if scores:
            averages[model] = sum(scores) / len(scores)
        else:
            averages[model] = 0
    
    # Sort by average
    sorted_models = sorted(averages.items(), key=lambda x: x[1], reverse=True)
    
    print("📈 Rankings:\n")
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (model, avg) in enumerate(sorted_models):
        medal = medals[i] if i < 3 else "  "
        scores = data['model_scores'][model]
        score_str = ", ".join(map(str, scores))
        print(f"{medal} {model}")
        print(f"   Average: {avg:.2f}/5")
        print(f"   Scores: [{score_str}]")
        print(f"   Total ratings: {len(scores)}")
        print()
    
    # Winner
    if sorted_models:
        winner = sorted_models[0][0]
        winner_avg = sorted_models[0][1]
        print("="*50)
        print(f"🎯 WINNER: {winner}")
        print(f"   with average score of {winner_avg:.2f}/5")
        print("="*50)
        
        # Recommendation
        print("\n📋 Recommendation:")
        print(f"   Update bot.py to use: model=\"{winner}\"")
        print()
        
        # Score breakdown
        print("📊 Score Distribution:")
        for model, scores in data['model_scores'].items():
            if scores:
                dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for s in scores:
                    dist[s] += 1
                print(f"   {model}:")
                for score in range(5, 0, -1):
                    bar = "█" * dist[score]
                    print(f"      {score}★: {bar} ({dist[score]})")
                print()

def main():
    print("🔍 Looking for test results file...")
    
    filepath = find_latest_test_file()
    if not filepath:
        print("❌ No test results file found!")
        print("   Run 'python run_blind_test.py' first.")
        return
    
    print(f"📄 Found: {os.path.basename(filepath)}")
    
    data = parse_results(filepath)
    if data:
        display_results(data)

if __name__ == "__main__":
    main()
