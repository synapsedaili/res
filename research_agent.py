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
    """Fikir havuzunu yükler, yoksa boş oluşturur."""
    if os.path.exists(IDEA_POOL_FILE):
        try:
            with open(IDEA_POOL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"found_ideas": []}
    return {"found_ideas": []}

def save_idea_pool(pool):
    """Fikir havuzunu kaydeder."""
    with open(IDEA_POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

def search_web(queries):
    all_data = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                print(f"Aranıyor: {q}")
                try:
                    time.sleep(random.uniform(3, 7))
                    results = ddgs.text(q, max_results=5)
                    for r in results:
                        all_data.append(f"SORGU: {q} | BAŞLIK: {r.get('title', 'N/A')} | ÖZET: {r.get('body', 'N/A')}")
                except Exception as e:
                    print(f"Arama hatası: {e}")
    except Exception as e:
        print(f"DDGS başlatma hatası: {e}")
    return all_data

def ask_qwen_to_evaluate_and_plan(current_findings, idea_pool):
    print("Qwen veriyi değerlendiriyor ve sonraki adımı planlıyor...")
    
    recent_findings = "\n".join(current_findings[-15:])
    
    # Fikir havuzunu Qwen'e göster
    existing_ideas = "\n".join([f"- {idea['name']}" for idea in idea_pool.get("found_ideas", [])[-20:]])
    
    prompt = f"""/no_think
Sen otonom bir Derin Web Veri Madencisisin.
Şu ana kadar şu verileri topladık:
{recent_findings}

ZATEN BULUNAN FİKİRLER (BUNLARI TEKRAR ÖNERME):
{existing_ideas if existing_ideas else "Henüz fikir bulunmadı."}

GÖREV:
1. Bu veriler, "son 3 ayda yükselen, monopolize olmamış niş yazılım/veri seti" bulmak için YETERLİ mi?
2. Eğer YETERLİ DEĞİLSE, bu konuyu daha derine kazımak için 3 adet ÇOK SPESİFİK İngilizce arama sorgusu üret.
3. Eğer YETERLİ İSE, sadece "DUR" yaz.

KRİTİK KURALLAR:
-  etiketlerini KULLANMA.
- Sadece geçerli JSON çıktısı ver. Markdown, açıklama YASAK.

ÇIKTI FORMATI:
{{
    "durum": "DEVAM" veya "DUR",
    "neden": "Kısa açıklama",
    "yeni_sorgular": ["sorgu 1", "sorgu 2", "sorgu 3"]
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
        
        print(f"DEBUG: Ham Qwen cevabı (ilk 200 karakter): {content[:200]}...")
        
        #  ve  etiketlerini temizle
        clean_content = re.sub(r'[\s\S]*', '', content)
        clean_content = re.sub(r'[\s\S]*', '', clean_content)
        clean_content = clean_content.strip()
        
        # Markdown bloklarını temizle
        clean_content = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', clean_content, flags=re.MULTILINE).strip()
        
        return json.loads(clean_content)
    except Exception as e:
        print(f"Qwen değerlendirme hatası: {e}. Varsayılan olarak DUR deniyor.")
        return {"durum": "DUR", "neden": "Hata", "yeni_sorgular": []}

def generate_final_report(all_findings, idea_pool):
    print("Nihai rapor oluşturuluyor...")
    
    all_data_text = "\n".join(all_findings)
    today_str = datetime.datetime.now().strftime('%d.%m.%Y')
    
    existing_ideas = "\n".join([f"- {idea['name']}: {idea.get('description', '')}" for idea in idea_pool.get("found_ideas", [])])
    
    prompt = f"""/no_think
Sen uzman bir AI Veri Madenciliği ve Pazar Fırsatları Analistisin.
Aşağıda otonom araştırma ajanı tarafından internetin derinliklerinden toplanan ham veriler var.

ZATEN BULUNAN FİKİRLER (BUNLARI TEKRAR ÖNERME, YENİ FİKİRLER BUL):
{existing_ideas if existing_ideas else "Henüz fikir bulunmadı."}

GÖREV:
Bu ham verileri analiz et ve SADECE şu kriterlere uyan fırsatları listele:
1. Son 3 ayda popülaritesi artan niş yazılımlar, özel veri setleri veya nadir dijital belgeler.
2. Henüz kimsenin ticari olarak monopolleşmediği "mavi okyanus" başlıklar.
3. Bu alanlarda otomasyon ile nasıl gelir elde edilebileceğine dair 1-2 cümlelik, uygulanabilir somut fikir.

KRİTİK KURALLAR:
-  etiketlerini KULLANMA.
- Kısa ve net ol. Madde işaretleri kullan.
- ÇIKTI TÜRKÇE OLMALIDIR.

VERİLER:
{all_data_text}

ÇIKTI FORMATI (Markdown):
# Günlük Derin Web AI Veri Madenciliği Raporu
**Tarih:** {today_str}
**İncelenen Bulgu Sayısı:** {len(all_findings)}

## Monopolize Olmamış Niş Fırsatlar
(Madde madde: Fırsat Adı, Neden Yükseliyor, Ticari/Otomasyon Fikri)

## Ajanın Keşif Notları
(Araştırma sırasında öne çıkan ilginç bağlantılar)

## Yeni Bulunan Fikirler (JSON Formatı)
Aşağıdaki formatta, raporda bahsettiğin YENİ fikirleri JSON olarak ekle (fikir havuzuna eklemek için):

```json
{{
    "yeni_fikirler": [
        {{"name": "Fikir Adı", "description": "Kısa açıklama"}},
        {{"name": "Fikir Adı 2", "description": "Kısa açıklama 2"}}
    ]
}}

```"""

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
        
        print(f"DEBUG: Ham rapor cevabı (ilk 200 karakter): {content[:200]}...")
        
        #  etiketlerini temizle
        clean_content = re.sub(r'[\s\S]*', '', content)
        clean_content = re.sub(r'[\s\S]*', '', clean_content)
        clean_content = clean_content.strip()
        
        # FALLBACK: Eğer Qwen boş dönerse ham verileri yaz
        if not clean_content:
            print("UYARI: Qwen boş rapor döndürdü. Ham veriler kaydediliyor.")
            return f"# Günlük Derin Web AI Veri Madenciliği Raporu (Ham Veri Yedek)\n**Tarih:** {today_str}\n\nQwen yapılandırılmış rapor oluşturamadı. Toplanan ham veriler:\n\n{all_data_text}", []
        
        # JSON bloğunu çıkar
        new_ideas = []
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', clean_content)
        if json_match:
            try:
                json_str = json_match.group(1)
                ideas_data = json.loads(json_str)
                new_ideas = ideas_data.get("yeni_fikirler", [])
                # JSON bloğunu rapordan kaldır
                clean_content = clean_content[:json_match.start()] + clean_content[json_match.end():]
            except Exception as e:
                print(f"JSON ayrıştırma hatası: {e}")
        
        return clean_content.strip(), new_ideas
    except Exception as e:
        print(f"Rapor oluşturma hatası: {e}. Ham veriler kaydediliyor.")
        return f"# Günlük Derin Web AI Veri Madenciliği Raporu (Hata Yedek)\n**Tarih:** {today_str}\n\nHata: {e}\n\nHam Veriler:\n\n{all_data_text}", []

def main():
    print("Otonom Qwen Derin Web Ajanı Başlatıldı...")
    start_time = time.time()
    MAX_DURATION = 2700  # 45 dakika
    
    # Fikir havuzunu yükle
    idea_pool = load_idea_pool()
    print(f"Fikir havuzu yüklendi: {len(idea_pool.get('found_ideas', []))} mevcut fikir.")
    
    all_findings = []
    current_queries = [
        "niche open source dataset 2026 site:reddit.com OR site:kaggle.com",
        "undiscovered ai automation tool github trending 2026",
        "rare digital documents dataset open source 2026",
        "new micro-saaS ideas solving specific problems 2026"
    ]
    
    cycle = 1
    while (time.time() - start_time) < MAX_DURATION:
        print(f"\n--- Döngü {cycle} ---")
        
        new_data = search_web(current_queries)
        all_findings.extend(new_data)
        print(f"{len(new_data)} yeni bulgu eklendi. Toplam: {len(all_findings)}")
        
        evaluation = ask_qwen_to_evaluate_and_plan(all_findings, idea_pool)
        print(f"Qwen Kararı: {evaluation.get('durum')} - {evaluation.get('neden')}")
        
        if evaluation.get('durum') == 'DUR':
            print("Qwen yeterli veriye ulaşıldığına karar verdi. Döngü sonlandırılıyor.")
            break
            
        current_queries = evaluation.get('yeni_sorgular', [])
        if not current_queries:
            print("Yeni sorgu üretilemedi, döngü sonlandırılıyor.")
            break
            
        cycle += 1

    print("\nNihai rapor hazırlanıyor...")
    report, new_ideas = generate_final_report(all_findings, idea_pool)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"raporlar/gunluk_rapor_{today}.md"
    os.makedirs("raporlar", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    # Yeni fikirleri havuza ekle
    if new_ideas:
        print(f"{len(new_ideas)} yeni fikir bulundu ve havuza ekleniyor...")
        for idea in new_ideas:
            idea_pool["found_ideas"].append({
                "name": idea.get("name", "İsimsiz"),
                "description": idea.get("description", ""),
                "date": today
            })
        save_idea_pool(idea_pool)
        print(f"Fikir havuzu güncellendi. Toplam fikir: {len(idea_pool['found_ideas'])}")
        
    print(f"Rapor başarıyla kaydedildi: {filename}")
    print(f"Toplam geçen süre: {(time.time() - start_time)/60:.1f} dakika")

if __name__ == "__main__":
    main()
