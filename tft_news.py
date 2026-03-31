import requests
from bs4 import BeautifulSoup
import os

TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
ROLE_ID = "ROL_ID_BURAYA" 
LAST_NEWS_FILE = "last_news.txt"

def main():
    print("--- DEBUG BAŞLADI ---")
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. Scraping Kontrolü
    try:
        response = requests.get(TARGET_URL, headers=headers)
        print(f"Site Yanıtı: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Riot'un en güncel haber kartını yakalamaya çalışıyoruz
        card = soup.find('a', href=True)
        if not card:
            print("HATA: Haber kartı bulunamadı (Selector hatası olabilir)!")
            return

        title = card.find('h2').get_text(strip=True) if card.find('h2') else "Başlık Yok"
        link = card['href']
        if not link.startswith('http'):
            link = "https://teamfighttactics.leagueoflegends.com" + link
        
        print(f"Bulunan Haber: {title}")
        print(f"Bulunan Link: {link}")

    except Exception as e:
        print(f"Scraping sırasında çökme: {e}")
        return

    # 2. Dosya Okuma Kontrolü
    last_link = ""
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip()
    print(f"Eski Link (Dosyadaki): '{last_link}'")

    # 3. Karşılaştırma ve Gönderim
    if link != last_link:
        print("DURUM: Yeni haber tespit edildi! Gönderiliyor...")
        
        if not WEBHOOK_URL:
            print("HATA: DISCORD_WEBHOOK bulunamadı! GitHub Secrets'ı kontrol et.")
            return

        payload = {
            "content": f"📢 <@&{ROLE_ID}> **Yeni Haber!**",
            "embeds": [{
                "title": title,
                "url": link,
                "color": 16753920
            }]
        }
        
        res = requests.post(WEBHOOK_URL, json=payload)
        print(f"Discord Yanıt Kodu: {res.status_code}")
        
        if res.status_code in [200, 204]:
            with open(LAST_NEWS_FILE, "w") as f:
                f.write(link)
            print("BAŞARI: last_news.txt güncellendi ve Discord'a basıldı.")
        else:
            print(f"HATA: Discord mesajı reddetti. Yanıt: {res.text}")
    else:
        print("DURUM: Haber zaten güncel, işlem yapılmadı.")
    
    print("--- DEBUG BİTTİ ---")

if __name__ == "__main__":
    main()
