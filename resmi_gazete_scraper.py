import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# GitHub sunucuları İngilizce olduğu için ay isimlerini manuel eşleştiriyoruz
TURKISH_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos", 
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}

# --- AYARLAR ---
KEYWORDS = ["İşçi", "İşveren", "Sendika", "SGK", "4857", "5510", "Yönetmelik", "Tebliğ", "Atama"]

def fetch_resmi_gazete():
    now = datetime.now()
    today_url_format = now.strftime("%Y%m%d")
    month_str = TURKISH_MONTHS[now.month]
    display_date = f"{now.day} {month_str} {now.year}"
    
    url = f"https://www.resmigazete.gov.tr/eskiler/{now.year}/{now.strftime('%m')}/{today_url_format}.htm"
    
    # Bağlantı hatalarına karşı 3 kez deneme yapacak mekanizma
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Deneme {attempt + 1}: Sorgulanıyor: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Referer': 'https://www.resmigazete.gov.tr/',
                'Cache-Control': 'no-cache'
            }

            # Zaman aşımını 45 saniyeye çıkardık
            response = requests.get(url, headers=headers, timeout=45)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                print("Bağlantı başarılı, içerik ayrıştırılıyor...")
                return parse_content(response.text, display_date)
            elif response.status_code == 404:
                return f"Bilgi: {display_date} tarihli gazete henüz yayımlanmamış görünüyor (404)."
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            wait_time = 10 * (attempt + 1)
            print(f"Zaman aşımı! {wait_time} saniye sonra tekrar denenecek...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Hata: {str(e)}")
            time.sleep(5)

    return f"Hata: Resmî Gazete sunucusuna {max_retries} deneme sonunda ulaşılamadı."

def parse_content(html_content, display_date):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a')
    
    fihrist_items = []
    found_matches = []

    for link in links:
        text = link.get_text().strip()
        if len(text) > 15:
            fihrist_items.append(text)
            for kw in KEYWORDS:
                if kw.lower() in text.lower():
                    href = link.get('href', '')
                    if href.startswith('/'):
                        full_link = "https://www.resmigazete.gov.tr" + href
                    elif not href.startswith('http'):
                        full_link = f"https://www.resmigazete.gov.tr/eskiler/{datetime.now().year}/{datetime.now().strftime('%m')}/{href}"
                    else:
                        full_link = href
                    
                    found_matches.append({'keyword': kw, 'title': text, 'link': full_link})

    report = f"📅 {display_date} - RESMİ GAZETE ANALİZ RAPORU\n" + "="*50 + "\n"
    if not fihrist_items:
        return report + "⚠️ Sayfa okundu ancak başlıklar ayrıştırılamadı."

    report += f"📋 Toplam Başlık Sayısı: {len(fihrist_items)}\n\n🔍 ÇEEİ BULGULARI:\n"
    if found_matches:
        for m in found_matches:
            report += f"✅ [{m['keyword']}] {m['title']}\nLink: {m['link']}\n\n"
    else:
        report += "❌ Bugün anahtar kelimelerle ilgili kayıt bulunamadı.\n"

    report += "\n--- TAM FİHRİST (İLK 30) ---\n"
    for item in fihrist_items[:30]:
        report += f"- {item}\n"
    return report

if __name__ == "__main__":
    result = fetch_resmi_gazete()
    with open("gunluk_rapor.txt", "w", encoding="utf-8") as f:
        f.write(result)
