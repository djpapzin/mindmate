#!/usr/bin/env python3
"""
Automated Blind A/B/C Model Testing for MindMate
Runs test prompts through 3 models and saves results to markdown for rating.
"""

import os
import random
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Models to test
MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5.2"]

# System prompt (same as bot)
SYSTEM_PROMPT = """You are MindMate, an AI mental wellness companion. You provide:
- Emotional reflection and support
- Journaling prompts
- Basic psychoeducation about stress and habits
- Help planning small, manageable next steps

You are NOT a therapist, doctor, or emergency service. Never diagnose or provide medical advice.
Be concise, warm, and non-judgmental. Use emojis sparingly."""

# Test prompts covering different mental wellness scenarios
TEST_PROMPTS = [
    # Anxiety
    "I'm feeling really anxious about a job interview tomorrow. My mind keeps racing with worst-case scenarios.",
    "I've been having trouble sleeping because I can't stop worrying about things I can't control.",
    
    # Work stress
    "I'm completely overwhelmed with my workload. I don't know how to prioritize and everything feels urgent.",
    "My boss criticized my work in front of the team and I feel humiliated. I'm questioning if I'm good enough.",
    
    # Relationships
    "I had a big argument with my partner about finances. We both said hurtful things and now there's tension.",
    "I feel like my friends don't really understand me. I often feel lonely even when I'm around people.",
    
    # Self-esteem
    "I keep comparing myself to others on social media and it makes me feel like I'm falling behind in life.",
    "I made a mistake at work and I can't stop beating myself up about it. I feel like such a failure.",
    
    # Mood/Depression
    "I've been feeling really low lately. Nothing seems to excite me anymore and I'm just going through the motions.",
    "Some days I feel fine, but then suddenly I get hit with waves of sadness for no apparent reason.",
    
    # Life transitions
    "I'm going through a major life change and I feel lost. I don't know who I am anymore.",
    "I'm struggling to find meaning and purpose. What's the point of it all?",
    
    # Practical support
    "I want to start exercising but I can never stick to a routine. How do I build better habits?",
    "I need to have a difficult conversation with someone but I keep avoiding it. How should I approach this?",
    
    # General emotional support
    "I just need someone to talk to. It's been a rough week and I feel like no one understands.",
]

def get_response(client: OpenAI, model: str, prompt: str) -> str:
    """Get response from a specific model."""
    try:
        # GPT-5.x models use max_completion_tokens instead of max_tokens
        if model.startswith("gpt-5"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=600,
                temperature=0.8,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.8,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def run_test():
    """Run the blind test and save results to markdown."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        return
    
    client = OpenAI(api_key=api_key)
    
    print("🧪 Starting Blind A/B/C Model Test...")
    print(f"📊 Testing {len(TEST_PROMPTS)} prompts across {len(MODELS)} models")
    print()
    
    # Store results with hidden mapping
    results = []
    model_key = {}  # Will store which letter = which model (revealed at end)
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"[{i}/{len(TEST_PROMPTS)}] Testing: {prompt[:50]}...")
        
        # Get responses from all models
        responses = {}
        for model in MODELS:
            print(f"  → Querying {model}...")
            responses[model] = get_response(client, model, prompt)
        
        # Shuffle models for blind assignment
        shuffled = MODELS.copy()
        random.shuffle(shuffled)
        
        mapping = {
            "A": shuffled[0],
            "B": shuffled[1],
            "C": shuffled[2],
        }
        
        results.append({
            "prompt": prompt,
            "mapping": mapping,
            "responses": {
                "A": responses[shuffled[0]],
                "B": responses[shuffled[1]],
                "C": responses[shuffled[2]],
            }
        })
        print(f"  ✓ Done")
    
    print()
    print("📝 Generating markdown file...")
    
    # Generate markdown file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"AB_TEST_RESULTS_{timestamp}.md"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    with open(filepath, "w") as f:
        f.write("# Blind A/B/C Model Test Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Tests:** {len(TEST_PROMPTS)}\n")
        f.write(f"**Models:** Hidden until you finish rating!\n\n")
        f.write("---\n\n")
        f.write("## How to Rate\n\n")
        f.write("1. Read each prompt and the 3 responses (A, B, C)\n")
        f.write("2. Rate each response 1-5 based on:\n")
        f.write("   - **Warmth/Empathy** - Does it feel caring?\n")
        f.write("   - **Helpfulness** - Is the advice practical?\n")
        f.write("   - **Naturalness** - Does it sound human-like?\n")
        f.write("3. Edit the `Rating:` field for each response\n")
        f.write("4. Run `python calculate_results.py` to see winner\n\n")
        f.write("**Rating Scale:** 1=Poor, 2=Below Avg, 3=Average, 4=Good, 5=Excellent\n\n")
        f.write("---\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"## Test {i}\n\n")
            f.write(f"**Prompt:** {result['prompt']}\n\n")
            
            for letter in ["A", "B", "C"]:
                f.write(f"### Response {letter}\n\n")
                f.write(f"{result['responses'][letter]}\n\n")
                f.write(f"**Rating:** ___ /5\n\n")
            
            f.write("---\n\n")
        
        # Hidden mapping at the end (for calculate script)
        f.write("<!-- HIDDEN MAPPING (DO NOT EDIT) -->\n")
        f.write("<!-- This will be used by calculate_results.py -->\n")
        f.write("<!--\n")
        f.write("MAPPING_START\n")
        for i, result in enumerate(results, 1):
            f.write(f"TEST_{i}_A={result['mapping']['A']}\n")
            f.write(f"TEST_{i}_B={result['mapping']['B']}\n")
            f.write(f"TEST_{i}_C={result['mapping']['C']}\n")
        f.write("MAPPING_END\n")
        f.write("-->\n")
    
    print(f"✅ Saved to: {filepath}")
    print()
    print("📋 Next steps:")
    print(f"   1. Open {filename}")
    print("   2. Rate each response (1-5)")
    print("   3. Run: python calculate_results.py")
    print()
    
    return filepath

if __name__ == "__main__":
    run_test()
