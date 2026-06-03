
import os
import datetime
import time
import random
import requests
import json
import re
from ddgs import DDGS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b" 

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

def ask_qwen_to_evaluate_and_plan(current_findings):
    print("Qwen is evaluating data and planning next step...")
    
    recent_findings = "\n".join(current_findings[-15:])
    
    prompt = f"""You are an autonomous Deep Web Data Miner.
    Here is the data collected so far:
    {recent_findings}

    TASK:
    1. Is this data SUFFICIENT to find "niche software/datasets rising in the last 3 months that are not monopolized"?
    2. If NOT SUFFICIENT, generate 3 VERY SPECIFIC, long-tail English search queries to dig deeper.
    3. If SUFFICIENT, just output "STOP".

    OUTPUT FORMAT (Output ONLY valid JSON, nothing else):
    {{
        "status": "CONTINUE" or "STOP",
        "reason": "Short explanation",
        "new_queries": ["query 1", "query 2", "query 3"]
    }}"""
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 500}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        
        clean_content = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', content.strip(), flags=re.MULTILINE)
        
        return json.loads(clean_content)
    except Exception as e:
        print(f"Qwen evaluation error: {e}. Defaulting to STOP.")
        return {"status": "STOP", "reason": "Error", "new_queries": []}

def generate_final_report(all_findings):
    print("Generating final report...")
    
    all_data_text = "\n".join(all_findings)
    today_str = datetime.datetime.now().strftime('%d.%m.%Y')
    
    prompt = f"""You are an expert AI Data Mining and Market Opportunity Analyst.
    Below is the raw data collected by the autonomous research agent from the depths of the internet.
    
    TASK:
    Analyze this raw data and list ONLY opportunities that meet these criteria:
    1. Niche software, special datasets, or rare digital documents whose popularity has increased in the last 3 months.
    2. "Blue ocean" titles that no one has commercially monopolized yet.
    3. 1-2 sentence actionable, concrete ideas on how to generate income via automation in these areas.

    DATA:
    {all_data_text}

    OUTPUT FORMAT (Markdown):
    # Daily Deep Web AI Data Mining Report
    **Date:** {today_str}
    **Total Findings Analyzed:** {len(all_findings)}
    
    ## Unmonopolized Niche Opportunities
    (Bullet points: Opportunity Name, Why it is rising, Commercial/Automation Idea)
    
    ## Agent Discovery Notes
    (Interesting, unexpected connections found during research)"""

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 2000}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except Exception as e:
        return f"Report generation error: {e}"

def main():
    print("Autonomous Qwen Deep Web Agent Started...")
    start_time = time.time()
    MAX_DURATION = 2700  # 45 minutes
    
    all_findings = []
    current_queries = [
        "niche open source dataset 2026 site:reddit.com OR site:kaggle.com",
        "undiscovered ai automation tool github trending 2026",
        "rare digital documents dataset open source 2026",
        "new micro-saaS ideas solving specific problems 2026"
    ]
    
    cycle = 1
    while (time.time() - start_time) < MAX_DURATION:
        print(f"\n--- Cycle {cycle} ---")
        
        new_data = search_web(current_queries)
        all_findings.extend(new_data)
        print(f"Added {len(new_data)} new findings. Total: {len(all_findings)}")
        
        evaluation = ask_qwen_to_evaluate_and_plan(all_findings)
        print(f"Qwen Decision: {evaluation.get('status')} - {evaluation.get('reason')}")
        
        if evaluation.get('status') == 'STOP':
            print("Qwen decided sufficient data is reached. Loop terminating.")
            break
            
        current_queries = evaluation.get('new_queries', [])
        if not current_queries:
            print("No new queries generated, loop terminating.")
            break
            
        cycle += 1

    print("\nPreparing final report...")
    report = generate_final_report(all_findings)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    os.makedirs("raporlar", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Report successfully saved: {filename}")
    print(f"Total time elapsed: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    main()

