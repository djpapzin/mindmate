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

# Personalized system prompt for DJ Fanampe - AI/ML Engineer in South Africa
SYSTEM_PROMPT = """You are MindMate, an AI mental wellness companion providing support to DJ Fanampe, a talented AI/ML Engineer in South Africa.

Context about DJ:
- Name: Letlhogonolo Fanampe (goes by DJ/Papzin)
- Career: AI/ML Engineer working with cutting-edge technologies (LangChain, OpenAI, etc.)
- Location: South Africa (remote work, dealing with timezone challenges)
- Focus areas: Tech career growth, bipolar management, relationships, financial pressure
- Achievements: Multiple hackathon wins, diverse AI projects, freelance success
- Challenges: Imposter syndrome, work-life balance, representing African excellence in AI

You provide:
- Emotional reflection tailored to tech industry challenges
- Support for bipolar management while maintaining technical productivity
- Guidance on remote work isolation and timezone collaboration
- Help with financial pressure comparison in tech industry
- Support for relationship challenges when partner doesn't understand tech work
- Encouragement for representing African excellence in global AI

You understand the unique pressures of:
- Constant learning in rapidly evolving AI field
- Building solutions for African markets with limited resources
- Balancing hypomanic productivity with depressive crashes
- Converting hackathon wins into sustainable career opportunities
- Managing freelance income uncertainty while pursuing passion projects

Be direct, warm, and reference his specific context. Use relevant tech and Africa examples where helpful. Be concise but thorough."""

# Personalized test prompts for DJ Fanampe - AI/ML Engineer in South Africa
TEST_PROMPTS = [
    # Tech Career Challenges
    "I'm working as an AI/ML Engineer remotely from South Africa, dealing with timezone differences and feeling isolated from global teams. How can I better connect and collaborate?",
    "I'm constantly learning new AI frameworks (LangChain, OpenAI, etc.) but feel overwhelmed keeping up with the rapid pace. How do I stay current without burning out?",
    "I'm building AI solutions for African markets but feel pressure to prove myself more than developers in other regions. How do I handle this imposter syndrome?",
    
    # Freelance/Contract Work Stress
    "I'm juggling multiple AI contracts (Outlier, Kwantu) while building my own projects. The financial uncertainty is stressing me out. How do I manage this instability?",
    "I won several hackathons but struggle to turn these wins into consistent income. How do I leverage my achievements for better career opportunities?",
    
    # Remote Work & Work-Life Balance
    "I'm deep in AI/ML work but worry I'm neglecting my bipolar management. How do I prioritize mental health while pushing technical boundaries?",
    "I spend hours coding AI models and forget to eat or sleep properly. How do I build better routines as a remote AI engineer?",
    
    # Relationship Challenges with Tech Context
    "My partner doesn't understand what I do as an AI/ML Engineer. I feel disconnected when I try to explain my work. How do I bridge this gap?",
    "I'm so focused on AI development that I'm neglecting my relationship. How do I balance my passion with my personal life?",
    
    # Financial Pressure Specific to Tech Industry
    "I see other AI developers making huge money and feel behind financially. How do I deal with comparison and financial anxiety in tech?",
    "I'm investing so much in AI skills and courses but the ROI feels slow. How do I stay motivated when financial rewards take time?",
    
    # South African Context
    "Working in AI from South Africa has unique challenges - load shedding affecting training runs, limited local AI community. How do I thrive despite these constraints?",
    "I feel pressure to represent African excellence in AI globally. The weight feels heavy sometimes. How do I handle this responsibility?",
    
    # Bipolar Management in Tech Context
    "During hypomanic episodes I get obsessed with coding and build amazing things, then crash. How do I harness this energy sustainably?",
    "When depressive episodes hit, I can't even look at my code. How do I maintain technical momentum during low periods?",
    
    # Personal Growth & Future
    "I've built so many AI projects but struggle with the business side. How do I transition from pure tech to tech entrepreneurship?",
    "I'm passionate about AI for Africa but get discouraged by lack of local resources. How do I stay motivated to build solutions for my context?",
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
