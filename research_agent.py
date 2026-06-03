import os
import datetime
import time
import random
import requests
import json
from ddgs import DDGS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b" 

# Anti-ban için rastgele kullanıcı ajanları
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

def search_web(queries):
    """Ban yememek için rastgele bekleme ve user-agent ile arama yapar."""
    all_data = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                print(f"🔍 Aranıyor: {q}")
                try:
                    # Rastgele 3-7 saniye bekle (Anti-bot davranışı)
                    time.sleep(random.uniform(3, 7))
                    results = ddgs.text(q, max_results=5)
                    for r in results:
                        all_data.append(f"SORGU: {q} | BAŞLIK: {r.get('title', 'N/A')} | ÖZET: {r.get('body', 'N/A')}")
                except Exception as e:
                    print(f"⚠️ Arama hatası: {e}")
    except Exception as e:
        print(f"❌ DDGS başlatma hatası: {e}")
    return all_data

def ask_qwen_to_evaluate_and_plan(current_findings):
    """Qwen'e mevcut veriyi gösterir. Yeterli mi? Değilse daha derin 3 yeni sorgu üretmesini ister."""
    print("🧠 Qwen veriyi değerlendiriyor ve sonraki adımı planlıyor...")
    
    prompt = f"""
    Sen otonom bir 'Derin Web Veri Madencisi'sin. 
    Şu ana kadar şu verileri topladık:
    {chr(10).join(current_findings[-15:])} # Son 15 bulguyu göster (token tasarrufu)

    GÖREV:
    1. Bu veriler, "son 3 ayda yükselen, monopolize olmamış niş yazılım/veri seti" bulmak için YETERLİ mi?
    2. Eğer YETERLİ DEĞİLSE, bu konuyu daha derine kazımak için 3 adet ÇOK SPESİFİK, uzun kuyruklu (long-tail) İngilizce arama sorgusu üret.
    3. Eğer YETERLİ İSE, sadece "DUR" yaz.

    CEVAP FORMATI (Sadece JSON olarak ver, başka hiçbir şey yazma):
    {{
        "durum": "DEVAM" veya "DUR",
        "neden": "Kısa açıklama",
        "yeni_sorgular": ["sorgu 1", "sorgu 2", "sorgu 3"]
    }}
    """
    
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
        
        # JSON temizleme (Bazen model 
```json ... 
``` ekleyebilir)
        content = content.replace("
```json", "").replace("
```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"⚠️ Qwen değerlendirme hatası: {e}. Varsayılan olarak DUR deniyor.")
        return {"durum": "DUR", "neden": "Hata", "yeni_sorgular": []}

def generate_final_report(all_findings):
    print("📝 Nihai rapor oluşturuluyor...")
    prompt = f"""
    Sen uzman bir 'AI Veri Madenciliği ve Pazar Fırsatları Analistisin'.
    Aşağıda otonom araştırma ajanı tarafından internetin derinliklerinden toplanan ham veriler var.
    
    GÖREV:
    Bu ham verileri analiz et ve SADECE şu kriterlere uyan fırsatları listele:
    1. Son 3 ayda popülaritesi artan niş yazılımlar, özel veri setleri veya nadir dijital belgeler.
    2. Henüz kimsenin ticari olarak monopolleşmediği "mavi okyanus" başlıklar.
    3. Bu alanlarda otomasyon ile nasıl gelir elde edilebileceğine dair 1-2 cümlelik, uygulanabilir somut fikir.

    VERİLER:
    {chr(10).join(all_findings)}

    ÇIKTI FORMATI (Markdown):
    # 📊 Derin Web AI Veri Madenciliği Raporu
    **Tarih:** {datetime.datetime.now().strftime('%d.%m.%Y')}
    **Toplam İncelenen Bulgu Sayısı:** {len(all_findings)}
    
    ## 🚀 Monopolize Olmamış Niş Fırsatlar
    (Madde madde: Fırsat Adı, Neden Yükseliyor, Ticari/Otomasyon Fikri)
    
    ## 💡 Ajanın Keşif Notları
    (Araştırma sırasında öne çıkan ilginç, beklenmedik bağlantılar)
    """

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
    MAX_DURATION = 2700  # 45 dakika (GitHub 60 dk limiti için güvenli tampon)
    
    all_findings = []
    # Başlangıç sorguları (Çöplüğün kapısı)
    current_queries = [
        "niche open source dataset 2026 site:reddit.com OR site:kaggle.com",
        "undiscovered ai automation tool github trending 2026",
        "rare digital documents dataset open source 2026",
        "new micro-saaS ideas solving specific problems 2026"
    ]
    
    cycle = 1
    while (time.time() - start_time) < MAX_DURATION:
        print(f"\n--- Döngü {cycle} ---")
        
        # 1. Ara
        new_data = search_web(current_queries)
        all_findings.extend(new_data)
        print(f"✅ {len(new_data)} yeni bulgu eklendi. Toplam: {len(all_findings)}")
        
        # 2. Qwen Değerlendirsin
        evaluation = ask_qwen_to_evaluate_and_plan(all_findings)
        print(f"🧠 Qwen Kararı: {evaluation.get('durum')} - {evaluation.get('neden')}")
        
        if evaluation.get('durum') == 'DUR':
            print("🛑 Qwen yeterli veriye ulaşıldığına karar verdi. Döngü sonlandırılıyor.")
            break
            
        # 3. Yeni sorgularla devam et
        current_queries = evaluation.get('yeni_sorgular', [])
        if not current_queries:
            print("⚠️ Yeni sorgu üretilemedi, döngü sonlandırılıyor.")
            break
            
        cycle += 1

    # Süre dolduysa veya Qwen dur dediyse raporu yaz
    print("\n📊 Nihai rapor hazırlanıyor...")
    report = generate_final_report(all_findings)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    os.makedirs("raporlar", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ Rapor başarıyla kaydedildi: {filename}")
    print(f"⏱️ Toplam geçen süre: {(time.time() - start_time)/60:.1f} dakika")

if __name__ == "__main__":
    main()

