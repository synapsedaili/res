import os
import datetime
import requests
from ddgs import DDGS # Yeni kütüphane adı

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b" 

def search_web():
    print("🔍 İnternette derin arama yapılıyor...")
    # İngilizce aramak GitHub IP'lerinde engellenmeyi azaltır ve daha fazla sonuç verir
    queries = [
        "niche open source software tools 2026",
        "new AI dataset kaggle huggingface 2026",
        "rare digital documents dataset open source",
        "AI automation niche opportunities reddit hackernews"
    ]
    
    all_data = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                try:
                    # Yeni ddgs sözdizimi
                    results = ddgs.text(q, max_results=3)
                    for r in results:
                        all_data.append(f"[{q}] Başlık: {r.get('title', 'N/A')} | Özet: {r.get('body', 'N/A')}")
                except Exception as e:
                    print(f"⚠️ '{q}' aranırken hata: {e}")
    except Exception as e:
        print(f"❌ DDGS başlatma hatası: {e}")
        
    return "\n".join(all_data)

def generate_report_with_local_qwen(search_data):
    print(f"🧠 Yerel {MODEL_NAME} modeli ile analiz başlıyor...")
    
    prompt = f"""
    Sen uzman bir 'AI Veri Madenciliği ve Pazar Fırsatları Analistisin'.
    Aşağıda internette son dönemde tespit edilen veriler var.
    
    GÖREV:
    Bu verileri analiz et ve SADECE şu kriterlere uyan fırsatları listele:
    1. Son 3 ayda popülaritesi artan niş yazılımlar, özel veri setleri veya nadir dijital belgeler.
    2. Henüz kimsenin ticari olarak monopolleşmediği "mavi okyanus" başlıklar.
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
        "options": {"temperature": 0.7, "num_predict": 1000}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"❌ Qwen Yerel API Hatası: {e}"

def main():
    print("🤖 Yerel Qwen Araştırma Botu Başlatıldı...")
    
    search_data = search_web()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    
    os.makedirs("raporlar", exist_ok=True)

    # KRİTİK DÜZELTME: Veri gelmezse bile dosya oluştur ki git hata vermesin
    if not search_data.strip():
        print("⚠️ DuckDuckGo veri döndürmedi (IP kısıtlaması olabilir). Yedek rapor oluşturuluyor.")
        report = f"# ⚠️ Günlük AI Veri Madenciliği Raporu\n**Tarih:** {today}\n\nBugün arama motoru (DuckDuckGo) GitHub sunucu IP'lerini kısıtladığı için veri çekilemedi. Sistem yarın otomatik olarak tekrar deneyecektir."
    else:
        report = generate_report_with_local_qwen(search_data)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ Rapor başarıyla oluşturuldu: {filename}")

if __name__ == "__main__":
    main()

