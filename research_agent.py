import os
import datetime
import time
import random
import requests
import json
import re
from ddgs import DDGS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:4b"
IDEA_POOL_FILE = "fikir_havuzu.json"

def load_idea_pool():
    if os.path.exists(IDEA_POOL_FILE):
        try:
            with open(IDEA_POOL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"found_ideas": []}
    return {"found_ideas": []}

def save_idea_pool(pool):
    with open(IDEA_POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

def search_web(queries):
    all_data = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                print(f"Searching: {q}")
                try:
                    time.sleep(random.uniform(3, 7))
                    results = ddgs.text(q, max_results=5)
                    for r in results:
                        all_data.append(f"QUERY: {q} | TITLE: {r.get('title', 'N/A')} | BODY: {r.get('body', 'N/A')}")
                except Exception as e:
                    print(f"Search error: {e}")
    except Exception as e:
        print(f"DDGS init error: {e}")
    return all_data

def select_main_topic(initial_findings, idea_pool):
    """CRITICAL: Qwen selects ONE main topic to focus on for the entire day."""
    print("Qwen is selecting ONE main topic to focus on today...")
    
    existing_ideas = "\n".join([f"- {idea['name']}" for idea in idea_pool.get("found_ideas", [])[-20:]])
    findings_text = "\n".join(initial_findings[:20])
    
    prompt = f"""/no_think
You are an expert AI Market Analyst. Below are initial search results from the internet.

EXISTING IDEAS (DO NOT SELECT THESE AGAIN):
{existing_ideas if existing_ideas else "No existing ideas yet."}

INITIAL FINDINGS:
{findings_text}

TASK:
Select EXACTLY ONE main topic/niche to focus on for today's deep research. The topic MUST meet these criteria:
1. Rising in popularity in the last 3 months
2. NOT commercially monopolized yet (blue ocean)
3. Related to: niche software, special datasets, rare digital documents, or micro-SaaS
4. Can generate income via automation

OUTPUT FORMAT (Output ONLY valid JSON, nothing else):
{{
    "selected_topic": "The ONE specific topic name (e.g., 'Open-source clinical speech datasets for rare diseases')",
    "reason": "Why this topic meets all 4 criteria (1-2 sentences)",
    "focus_queries": ["3 very specific English search queries to dig deeper into THIS topic only"]
}}"""
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 500}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=1200)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        
        print(f"DEBUG: Topic selection response: {content[:300]}...")
        
        clean_content = re.sub(r'', '', content).strip()
        clean_content = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', clean_content, flags=re.MULTILINE).strip()
        
        return json.loads(clean_content)
    except Exception as e:
        print(f"Topic selection error: {e}. Using fallback topic.")
        return {
            "selected_topic": "Niche open-source datasets for specialized industries",
            "reason": "Fallback topic",
            "focus_queries": ["niche dataset 2026 site:reddit.com OR site:kaggle.com", "undiscovered data marketplace 2026"]
        }

def ask_qwen_to_evaluate_and_plan(current_findings, selected_topic, idea_pool):
    print(f"Qwen is evaluating data for topic: {selected_topic}...")
    
    recent_findings = "\n".join(current_findings[-15:])
    existing_ideas = "\n".join([f"- {idea['name']}" for idea in idea_pool.get("found_ideas", [])[-20:]])
    
    prompt = f"""/no_think
You are an autonomous Deep Web Data Miner focused on ONE topic: "{selected_topic}"

DATA COLLECTED SO FAR:
{recent_findings}

EXISTING IDEAS (DO NOT SUGGEST THESE):
{existing_ideas if existing_ideas else "None yet."}

TASK:
1. Is this data SUFFICIENT to find a unique, unmonopolized opportunity within "{selected_topic}"?
2. If NOT SUFFICIENT, generate 3 VERY SPECIFIC English search queries to dig deeper into THIS TOPIC ONLY.
3. If SUFFICIENT, output "STOP".

OUTPUT FORMAT (Output ONLY valid JSON):
{{
    "status": "CONTINUE" or "STOP",
    "reason": "Short explanation",
    "new_queries": ["query 1", "query 2", "query 3"]
}}"""
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 500}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=1200)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        
        print(f"DEBUG: Evaluation response: {content[:200]}...")
        
        clean_content = re.sub(r'', '', content).strip()
        clean_content = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', clean_content, flags=re.MULTILINE).strip()
        
        return json.loads(clean_content)
    except Exception as e:
        print(f"Evaluation error: {e}. Defaulting to STOP.")
        return {"status": "STOP", "reason": "Error", "new_queries": []}

def generate_final_report(all_findings, selected_topic, idea_pool):
    print("Generating final report...")
    
    all_data_text = "\n".join(all_findings)
    today_str = datetime.datetime.now().strftime('%d.%m.%Y')
    
    existing_ideas = "\n".join([f"- {idea['name']}: {idea.get('description', '')}" for idea in idea_pool.get("found_ideas", [])])
    
    prompt = f"""/no_think
You are an expert AI Data Mining and Market Opportunity Analyst.
Today's research focused on: "{selected_topic}"

Below is the raw data collected by the autonomous agent.

EXISTING IDEAS (DO NOT SUGGEST THESE, FIND NEW ONES):
{existing_ideas if existing_ideas else "None yet."}

TASK:
Analyze this data and list ONLY opportunities that meet these criteria:
1. Rising in popularity in the last 3 months within "{selected_topic}"
2. NOT commercially monopolized yet (blue ocean)
3. Can generate income via automation (1-2 sentence actionable idea)

OUTPUT FORMAT (Markdown, English only):
# Daily Deep Web AI Data Mining Report
**Date:** {today_str}
**Today's Focus Topic:** {selected_topic}
**Total Findings Analyzed:** {len(all_findings)}

## Unmonopolized Niche Opportunities
(Bullet points: Opportunity Name, Why it's rising, Commercial/Automation Idea)

## Agent Discovery Notes
(Interesting connections found during research)

## New Ideas (JSON Format)
Extract the NEW ideas from above into this JSON format (for the idea pool):

```json
{{
    "new_ideas": [
        {{"name": "Idea Name", "description": "Short description"}},
        {{"name": "Idea Name 2", "description": "Short description 2"}}
    ]
}}

