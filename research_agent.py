
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
    "selected_topic": "The ONE specific topic name",
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
        clean_content = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*<LaTex>id_1</LaTex>', '', clean_content, flags=re.MULTILINE).strip()
        
        return json.loads(clean_content)
    except Exception as e:
        print(f"Evaluation error: {e}. Defaulting to STOP.")
        return {"status": "STOP", "reason": "Error", "new_queries": []}

def generate_final_report(all_findings, selected_topic, idea_pool):
    print("Generating final report...")
    
    all_data_text = "\n".join(all_findings)
    today_str = datetime.datetime.now().strftime('%d.%m.%Y')
    
    existing_ideas = "\n".join([f"- {idea['name']}: {idea.get('description', '')}" for idea in idea_pool.get("found_ideas", [])])
    
    # KRİTİK DÜZELTME: JSON bloğunu ayrı bir değişken olarak tanımladık
    json_format = '''
## New Ideas (JSON Format)
Extract the NEW ideas from above into this JSON format (for the idea pool):

```json
{{
    "new_ideas": [
        {{"name": "Idea Name", "description": "Short description"}},
        {{"name": "Idea Name 2", "description": "Short description 2"}}
    ]
}}

```'''
    
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
{json_format}

DATA:
{all_data_text}"""

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.6, "num_predict": 2000}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=1200)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        
        print(f"DEBUG: Report response (first 300 chars): {content[:300]}...")
        
        clean_content = re.sub(r'', '', content).strip()
        
        if not clean_content:
            print("WARNING: Qwen returned empty report. Saving raw data.")
            return f"# Daily Deep Web AI Data Mining Report (Raw Data Fallback)\n**Date:** {today_str}\n**Topic:** {selected_topic}\n\n{all_data_text}", []
        
        new_ideas = []
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', clean_content)
        if json_match:
            try:
                json_str = json_match.group(1)
                ideas_data = json.loads(json_str)
                new_ideas = ideas_data.get("new_ideas", [])
                clean_content = clean_content[:json_match.start()] + clean_content[json_match.end():]
            except Exception as e:
                print(f"JSON parsing error: {e}")
        
        return clean_content.strip(), new_ideas
    except Exception as e:
        print(f"Report generation error: {e}. Saving raw data.")
        return f"# Daily Deep Web AI Data Mining Report (Error Fallback)\n**Date:** {today_str}\n**Topic:** {selected_topic}\n\nError: {e}\n\nRaw Data:\n\n{all_data_text}", []

def main():
    print("Autonomous Qwen Deep Web Agent Started...")
    start_time = time.time()
    MAX_DURATION = 2700
    
    idea_pool = load_idea_pool()
    print(f"Idea pool loaded: {len(idea_pool.get('found_ideas', []))} existing ideas.")
    
    print("\n=== PHASE 1: Initial Broad Search ===")
    initial_queries = [
        "niche open source dataset 2026 site:reddit.com OR site:kaggle.com",
        "undiscovered ai automation tool github trending 2026",
        "rare digital documents dataset open source 2026",
        "new micro-saaS ideas solving specific problems 2026"
    ]
    
    initial_findings = search_web(initial_queries)
    print(f"Initial search complete: {len(initial_findings)} findings.")
    
    print("\n=== PHASE 2: Selecting Main Topic ===")
    topic_selection = select_main_topic(initial_findings, idea_pool)
    selected_topic = topic_selection.get("selected_topic", "Unknown")
    focus_queries = topic_selection.get("focus_queries", [])
    
    print(f"✅ SELECTED TOPIC: {selected_topic}")
    print(f"Reason: {topic_selection.get('reason', 'N/A')}")
    print(f"Focus queries: {focus_queries}")
    
    print("\n=== PHASE 3: Deep Research on Selected Topic ===")
    all_findings = initial_findings.copy()
    current_queries = focus_queries
    
    cycle = 1
    while (time.time() - start_time) < MAX_DURATION:
        print(f"\n--- Deep Dive Cycle {cycle} ---")
        
        new_data = search_web(current_queries)
        all_findings.extend(new_data)
        print(f"Added {len(new_data)} new findings. Total: {len(all_findings)}")
        
        evaluation = ask_qwen_to_evaluate_and_plan(all_findings, selected_topic, idea_pool)
        print(f"Qwen Decision: {evaluation.get('status')} - {evaluation.get('reason')}")
        
        if evaluation.get('status') == 'STOP':
            print("Qwen decided sufficient data is reached. Loop terminating.")
            break
            
        current_queries = evaluation.get('new_queries', [])
        if not current_queries:
            print("No new queries generated, loop terminating.")
            break
            
        cycle += 1

    print("\n=== PHASE 4: Generating Final Report ===")
    report, new_ideas = generate_final_report(all_findings, selected_topic, idea_pool)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    os.makedirs("raporlar", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    if new_ideas:
        print(f"Adding {len(new_ideas)} new ideas to pool...")
        for idea in new_ideas:
            idea_pool["found_ideas"].append({
                "name": idea.get("name", "Unnamed"),
                "description": idea.get("description", ""),
                "date": today,
                "topic": selected_topic
            })
        save_idea_pool(idea_pool)
        print(f"Idea pool updated. Total ideas: {len(idea_pool['found_ideas'])}")
        
    print(f"Report saved: {filename}")
    print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    main()

