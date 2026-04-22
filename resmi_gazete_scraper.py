import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# GitHub sunucuları İngilizce dilinde çalıştığı için ay isimlerini manuel eşleştiriyoruz
TURKISH_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos", 
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}

# --- AYARLAR ---
# Takip etmek istediğiniz anahtar kelimeler
KEYWORDS = ["İşçi", "İşveren", "Sendika", "SGK", "4857", "5510", "Yönetmelik", "Tebliğ", "Atama"]

def fetch_resmi_gazete():
    now = datetime.now()
    # Resmi Gazete URL formatı: YYYYMMDD
    today_url_format = now.strftime("%Y%m%d")
    month_str = TURKISH_MONTHS[now.month]
    display_date = f"{now.day} {month_str} {now.year}"
    
    # Resmi Gazete Arşiv URL'si (Doğrudan fihrist dosyası)
    url = f"https://www.resmigazete.gov.tr/eskiler/{now.year}/{now.strftime('%m')}/{today_url_format}.htm"
    
    # Bot engelini aşmak için gerçek bir tarayıcı başlıkları (User-Agent)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://www.resmigazete.gov.tr/'
    }

    try:
        print(f"Sorgulanıyor: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return f"Hata: {display_date} tarihli gazeteye ulaşılamadı. (Durum Kodu: {response.status_code})\nHenüz yayımlanmamış veya erişim engellenmiş olabilir."

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Resmi Gazete fihristi <a> etiketleri içinde başlıkları barındırır.
        links = soup.find_all('a')
        
        fihrist_items = []
        found_matches = []

        for link in links:
            text = link.get_text().strip()
            # Kısa menü metinlerini ele
            if len(text) > 15:
                fihrist_items.append(text)
                
                # Anahtar kelime kontrolü
                for kw in KEYWORDS:
                    if kw.lower() in text.lower():
                        # Linki tam URL'ye çevir
                        href = link.get('href', '')
                        full_link = href
                        if href.startswith('/'):
                            full_link = "https://www.resmigazete.gov.tr" + href
                        elif not href.startswith('http'):
                            # Göreli linkleri (relative path) tamamlama
                            full_link = f"https://www.resmigazete.gov.tr/eskiler/{now.year}/{now.strftime('%m')}/{href}"

                        found_matches.append({
                            'keyword': kw,
                            'title': text,
                            'link': full_link
                        })

        # RAPOR OLUŞTURMA
        report = f"📅 {display_date} - RESMİ GAZETE ANALİZ RAPORU\n"
        report += "="*50 + "\n"
        
        if not fihrist_items:
            report += "⚠️ Sayfa okundu ancak fihrist içeriği ayrıştırılamadı. Web sitesi yapısı farklı olabilir.\n"
            return report

        report += f"📋 Toplam Başlık Sayısı: {len(fihrist_items)}\n\n"
        
        report += "🔍 ÇEEİ VE İŞ HUKUKU BULGULARI:\n"
        if found_matches:
            for match in found_matches:
                report += f"✅ [EŞLEŞME: {match['keyword']}]\n"
                report += f"   Madde: {match['title']}\n"
                report += f"   Bağlantı: {match['link']}\n\n"
        else:
            report += "❌ Belirtilen anahtar kelimelerle ilgili bugün bir kayıt bulunamadı.\n"

        report += "\n--- TAM FİHRİST (İLK 30 BAŞLIK) ---\n"
        for item in fihrist_items[:30]:
            report += f"- {item}\n"

        return report

    except Exception as e:
        return f"Sistemsel Hata: {str(e)}"

if __name__ == "__main__":
    result = fetch_resmi_gazete()
    print(result)
    
    # Raporu GitHub Actions'ın paketleyebileceği bir dosyaya yaz
    with open("gunluk_rapor.txt", "w", encoding="utf-8") as f:
        f.write(result)
