import requests
from bs4 import BeautifulSoup
import os

TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
ROLE_ID = "ROL_ID_BURAYA" # Daha önce aldığın Rol ID'sini buraya yapıştır
LAST_NEWS_FILE = "last_news.txt"

def get_latest_tft_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ana haber kartını bul
        card = soup.find('a', href=True)
        if not card: return None

        # 1. Başlık (h2)
        title = card.find('h2').get_text(strip=True) if card.find('h2') else "TFT Güncellemesi"

        # 2. Resim URL'sini Çekme (Kritik Nokta)
        # Genelde 'img' etiketinin içindedir. Riot bazen 'src' yerine 'data-src' kullanabilir.
        img_tag = card.find('img')
        image_url = ""
        if img_tag:
            image_url = img_tag.get('src') or img_tag.get('data-src') or ""

        # 3. Link
        link = card['href']
        if not link.startswith('http'):
            link = "https://teamfighttactics.leagueoflegends.com" + link
            
        return {"title": title, "link": link, "image": image_url}
    except Exception as e:
        print(f"Hata: {e}")
        return None

def main():
    news = get_latest_tft_news()
    if not news: return

    last_link = ""
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip()

    if news['link'] != last_link:
        # Şık Discord Embed Yapısı + Resim + Rol Etiketi
        payload = {
            "content": f"📢 <@&{ROLE_ID}> **Yeni bir haber yayınlandı!**",
            "embeds": [{
                "title": news['title'],
                "url": news['link'],
                "color": 16753920, # TFT Turuncusu
                "image": {
                    "url": news['image'] # Çektiğimiz resim buraya geliyor
                },
                "footer": {
                    "text": "ESOGÜ Riot Kampüs Elçiliği",
                    "icon_url": "https://imgur.com/a/5oo2FQ6" # Varsa elçilik logosu
                }
            }]
        }
        
        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code in [200, 204]:
            with open(LAST_NEWS_FILE, "w") as f:
                f.write(news['link'])
            print("Resimli haber başarıyla gönderildi!")
    else:
        print("Yeni haber yok.")

if __name__ == "__main__":
    main()
