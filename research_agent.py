import os
import datetime
import requests
import feedparser
from ddgs import DDGS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b" 

def search_rss_feeds():
    """Binlerce siteyi besleyen merkezi RSS kaynaklarını tarar (Engellenmez, çok hızlıdır)."""
    print("📡 RSS Hub'ları taranıyor...")
    feeds = [
        "https://hnrss.org/newest?q=dataset+OR+niche+OR+automation", # Hacker News (Niş odaklı)
        "https://hnrss.org/show", # Hacker News Show HN (Yeni projeler)
        "https://github.com/trending/python?since=daily", # GitHub Trending (XML olarak alınamaz, alternatif kullanıyoruz)
        "http://feeds.feedburner.com/oreilly/radar/atom", # O'Reilly Radar (Yeni teknoloji trendleri)
        "https://www.kaggle.com/discussions/general/rss.xml", # Kaggle Tartışmaları
    ]
    
    # GitHub Trending için özel basit bir API/RSS alternatifi
    github_trending_url = "https://rsshub.app/github/trending/daily/any/any" 
    
    all_data = []
    
    for url in feeds:
        try:
            # RSS beslemesini 5 saniye timeout ile çek
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:3]: # Her feed'den sadece en taze 3 haberi al (gürültüyü azalt)
                    all_data.append(f"[RSS Kaynak] Başlık: {entry.get('title', 'N/A')} | Özet: {entry.get('summary', entry.get('description', 'N/A'))[:300]}")
        except Exception as e:
            continue # Bir feed çalışmazsa diğerlerine devam et, sistem çökmesin
            
    return "\n".join(all_data)

def search_web_advanced():
    """DuckDuckGo'yu 'site:' operatörleriyle profesyonel dedektif gibi kullanır."""
    print("🔍 Gelişmiş operatörlerle derin web taraması yapılıyor...")
    
    # Sadece yüksek kaliteli, niş topluluklarda arama yapar
    queries = [
        "site:news.ycombinator.com (dataset OR 'open source' OR niche) 2026",
        "site:reddit.com/r/MachineLearning OR site:reddit.com/r/datasets (new OR rising) 2026",
        "site:github.com trending 'ai agent' OR 'automation' niche",
        "site:producthunt.com 'ai' OR 'data mining' new"
    ]
    
    all_data = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                try:
                    results = ddgs.text(q, max_results=3)
                    for r in results:
                        all_data.append(f"[Web Arama] Başlık: {r.get('title', 'N/A')} | Özet: {r.get('body', 'N/A')}")
                except Exception as e:
                    print(f"⚠️ '{q}' aranırken hata: {e}")
    except Exception as e:
        print(f"❌ DDGS başlatma hatası: {e}")
        
    return "\n".join(all_data)

def generate_report_with_local_qwen(search_data):
    print(f"🧠 Yerel {MODEL_NAME} modeli ile analiz başlıyor...")
    
    prompt = f"""
    Sen uzman bir 'AI Veri Madenciliği ve Pazar Fırsatları Analistisin'.
    Aşağıda Hacker News, Reddit, Kaggle, GitHub ve niş teknoloji RSS beslemelerinden toplanan son veriler var.
    
    GÖREVİN:
    Bu verileri analiz et ve SADECE şu kriterlere uyan fırsatları listele:
    1. Son 3 ayda popülaritesi artan niş yazılımlar, özel veri setleri veya nadir dijital belgeler.
    2. Henüz kimsenin ticari olarak monopolleşmediği (tekelleşmediği) "mavi okyanus" başlıklar.
    3. Bu alanlarda otomasyon ile nasıl gelir elde edilebileceğine dair 1-2 cümlelik, uygulanabilir somut fikir.

    VERİLER:
    {search_data}

    ÇIKTI FORMATI (Markdown):
    # 📊 Günlük AI Veri Madenciliği Fırsat Raporu
    **Tarih:** {datetime.datetime.now().strftime('%d.%m.%Y')}
    **Kaynaklar:** Hacker News, Reddit, Kaggle, GitHub, Niş RSS Beslemeleri
    
    ## 🚀 Monopolize Olmamış Niş Fırsatlar
    (Madde madde: Fırsat Adı, Neden Yükseliyor, Ticari/Otomasyon Fikri)
    
    ## ⚠️ Dikkat Edilmesi Gerekenler
    (Bu alanlardaki olası engeller veya veri erişim zorlukları)
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Sen yaratıcı, analitik ve fırsat odaklı bir AI araştırmacısısın. Kısa, net ve eyleme geçirilebilir cevap ver."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 1500}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"❌ Qwen Yerel API Hatası: {e}"

def main():
    print("🤖 Yerel Qwen Araştırma Botu V2.0 Başlatıldı...")
    
    # 1. RSS Hub'larından veri çek
    rss_data = search_rss_feeds()
    
    # 2. Gelişmiş Web Araması yap
    web_data = search_web_advanced()
    
    # 3. Verileri birleştir
    combined_data = f"--- RSS BESLEMELERİ ---\n{rss_data}\n\n--- GELİŞMİŞ WEB ARAMASI ---\n{web_data}"
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    os.makedirs("raporlar", exist_ok=True)

    if not combined_data.strip():
        print("⚠️ Hiçbir veri kaynağı yanıt vermedi. Yedek rapor oluşturuluyor.")
        report = f"# ⚠️ Günlük AI Veri Madenciliği Raporu\n**Tarih:** {today}\n\nBugün tüm veri kaynakları (RSS/API) yanıt vermedi. Sistem yarın otomatik olarak tekrar deneyecektir."
    else:
        report = generate_report_with_local_qwen(combined_data)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ Rapor başarıyla oluşturuldu: {filename}")

if __name__ == "__main__":
    main()

