import os
import datetime
import requests
from duckduckgo_search import DDGS

# GitHub Actions'da Ollama varsayılan olarak bu adreste çalışır
OLLAMA_URL = "http://localhost:11434/api/chat"
# Not: Ollama kütüphanesinde 'qwen3' çıktığında burayı 'qwen3:3b' yapabilirsin. 
# Şu an en stabil ve RAM dostu olan 'qwen2.5:3b' kullanıyoruz.
MODEL_NAME = "qwen2.5:3b" 

def search_web():
    """İnternet çöplüğünde niş fırsatları arar."""
    print("🔍 İnternette derin arama yapılıyor...")
    queries = [
        "yeni çıkan açık kaynak niş yazılım 2026",
        "yapay zeka eğitim veri seti yeni yayınlanan kaggle huggingface",
        "rare digital documents dataset open source 2026",
        "AI automation niche opportunities reddit hackernews"
    ]
    
    all_data = []
    with DDGS() as ddgs:
        for q in queries:
            try:
                results = list(ddgs.text(q, max_results=3))
                for r in results:
                    all_data.append(f"[{q}] Başlık: {r['title']} | Özet: {r['body']}")
            except Exception as e:
                print(f"Arama hatası: {e}")
                
    return "\n".join(all_data)

def generate_report_with_local_qwen(search_data):
    """Sunucuya indirilmiş Qwen modeli ile rapor oluşturur."""
    print(f"🧠 Yerel {MODEL_NAME} modeli ile analiz başlıyor...")
    
    prompt = f"""
    Sen uzman bir 'AI Veri Madenciliği ve Pazar Fırsatları Analistisin'.
    Aşağıda internette son dönemde tespit edilen veriler var.
    
    GÖREV:
    Bu verileri analiz et ve SADECE şu kriterlere uyan fırsatları listele:
    1. Son 3 ayda popülaritesi artan niş yazılımlar, özel veri setleri veya nadir dijital belgeler.
    2. Henüz kimsenin ticari olarak monopolleşmediği (tekelleşmediği) "mavi okyanus" başlıklar.
    3. Bu alanlarda otomasyon ile nasıl gelir elde edilebileceğine dair 1 cümlelik somut fikir.

    VERİLER:
    {search_data}

    ÇIKTI FORMATI (Markdown):
    # 📊 Günlük AI Veri Madenciliği Fırsat Raporu
    **Tarih:** {datetime.datetime.now().strftime('%d.%m.%Y')}
    
    ## 🚀 Monopolize Olmamış Niş Fırsatlar
    (Madde madde: Fırsat Adı, Neden Yükseliyor, Ticari Fikir)
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Sen yaratıcı, analitik ve fırsat odaklı bir AI araştırmacısısın. Kısa ve net cevap ver."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 1000 # Raporun çok uzayıp zaman aşımına uğramasını engeller
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300) # 5 dk timeout
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"❌ Qwen Yerel API Hatası: {e}"

def main():
    print("🤖 Yerel Qwen Araştırma Botu Başlatıldı...")
    
    # 1. Veri topla
    search_data = search_web()
    if not search_data.strip():
        print("⚠️ Hiçbir veri bulunamadı.")
        return

    # 2. Qwen ile analiz et
    report = generate_report_with_local_qwen(search_data)
    
    # 3. Raporu kaydet
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    
    os.makedirs("raporlar", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ Rapor başarıyla oluşturuldu: {filename}")

if __name__ == "__main__":
    main()

