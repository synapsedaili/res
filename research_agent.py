import os
import datetime
import time
import random
import requests
import json
from ddgs import DDGS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b" 

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

def search_web(queries):
    all_data = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                print(f"🔍 Aranıyor: {q}")
                try:
                    time.sleep(random.uniform(3, 7))
                    results = ddgs.text(q, max_results=5)
                    for r in results:
                        all_data.append(f"SORGU: {q} | BAŞLIK: {r.get('title', 'N/A')} | OZET: {r.get('body', 'N/A')}")
                except Exception as e:
                    print(f"⚠️ Arama hatası: {e}")
    except Exception as e:
        print(f"❌ DDGS başlatma hatası: {e}")
    return all_data

def ask_qwen_to_evaluate_and_plan(current_findings):
    print("🧠 Qwen veriyi değerlendiriyor ve sonraki adımı planlıyor...")
    
    recent_findings = "\n".join(current_findings[-15:])
    
    prompt = f"""Sen otonom bir Derin Web Veri Madencisisin. 
    Su ana kadar su verileri topladik:
    {recent_findings}

    GOREV:
    1. Bu veriler, "son 3 ayda yukselen, monopolize olmamis nis yazilim/veri seti" bulmak icin YETERLI mi?
    2. Eger YETERLI DEGILSE, bu konuyu daha derine kazimak icin 3 adet COK SPESIFIK, uzun kuyruklu (long-tail) Ingilizce arama sorgusu uret.
    3. Eger YETERLI ISE, sadece "DUR" yaz.

    CEVAP FORMATI (Sadece JSON olarak ver, baska hicbir sey yazma):
    {{
        "durum": "DEVAM" veya "DUR",
        "neden": "Kisa aciklama",
        "yeni_sorgular": ["sorgu 1", "sorgu 2", "sorgu 3"]
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
        
        # GÜVENLİ TEMİZLİK: Tek tırnak kullanarak backtick sorununu kökten çözdük
        content = content.replace('
```json', '').replace('
```', '').strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"⚠️ Qwen değerlendirme hatası: {e}. Varsayılan olarak DUR deniyor.")
        return {"durum": "DUR", "neden": "Hata", "yeni_sorgular": []}

def generate_final_report(all_findings):
    print("📝 Nihai rapor oluşturuluyor...")
    
    all_data_text = "\n".join(all_findings)
    today_str = datetime.datetime.now().strftime('%d.%m.%Y')
    
    prompt = f"""Sen uzman bir AI Veri Madenciliği ve Pazar Fırsatları Analistisin.
    Asagida otonom araştırma ajani tarafindan internetin derinliklerinden toplanan ham veriler var.
    
    GOREV:
    Bu ham verileri analiz et ve SADECE su kriterlere uyan firsatlari listele:
    1. Son 3 ayda popülaritesi artan nis yazilimlar, ozel veri setleri veya nadir dijital belgeler.
    2. Henuz kimsenin ticari olarak monopollesmedigi "mavi okyanus" basliklar.
    3. Bu alanlarda otomasyon ile nasil gelir elde edilebilecegine dair 1-2 cumlelik, uygulanabilir somut fikir.

    VERILER:
    {all_data_text}

    CIKTI FORMATI (Markdown):
    # 📊 Derin Web AI Veri Madenciliği Raporu
    **Tarih:** {today_str}
    **Toplam İncelenen Bulgu Sayısı:** {len(all_findings)}
    
    ## 🚀 Monopolize Olmamış Niş Fırsatlar
    (Madde madde: Fırsat Adı, Neden Yükseliyor, Ticari/Otomasyon Fikri)
    
    ## 💡 Ajanın Keşif Notları
    (Araştırma sırasında öne çıkan ilginç, beklenmedik bağlantılar)"""

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
        return f"❌ Rapor oluşturma hatası: {e}"

def main():
    print("🤖 Otonom Qwen Derin Web Ajanı Başlatıldı...")
    start_time = time.time()
    MAX_DURATION = 2700  # 45 dakika
    
    all_findings = []
    current_queries = [
        "niche open source dataset 2026 site:reddit.com OR site:kaggle.com",
        "undiscovered ai automation tool github trending 2026",
        "rare digital documents dataset open source 2026",
        "new micro-saaS ideas solving specific problems 2026"
    ]
    
    cycle = 1
    while (time.time() - start_time) < MAX_DURATION:
        print(f"\n--- Dongu {cycle} ---")
        
        new_data = search_web(current_queries)
        all_findings.extend(new_data)
        print(f"✅ {len(new_data)} yeni bulgu eklendi. Toplam: {len(all_findings)}")
        
        evaluation = ask_qwen_to_evaluate_and_plan(all_findings)
        print(f"🧠 Qwen Kararı: {evaluation.get('durum')} - {evaluation.get('neden')}")
        
        if evaluation.get('durum') == 'DUR':
            print("🛑 Qwen yeterli veriye ulasildigina karar verdi. Dongu sonlandiriliyor.")
            break
            
        current_queries = evaluation.get('yeni_sorgular', [])
        if not current_queries:
            print("⚠️ Yeni sorgu uretilemedi, dongu sonlandiriliyor.")
            break
            
        cycle += 1

    print("\n📊 Nihai rapor hazırlanıyor...")
    report = generate_final_report(all_findings)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    os.makedirs("raporlar", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ Rapor başarıyla kaydedildi: {filename}")
    print(f"⏱️ Toplam gecen sure: {(time.time() - start_time)/60:.1f} dakika")

if __name__ == "__main__":
    main()

