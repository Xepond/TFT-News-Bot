import requests
from bs4 import BeautifulSoup
import os

# Ayarlar
TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK") # Güvenlik için ortam değişkeni kullanıyoruz
LAST_NEWS_FILE = "last_news.txt"

def get_latest_tft_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Önce ana haber kartını buluyoruz
        article_card = soup.find('a', href=True)
        if not article_card:
            return None
            
        # 2. SADECE başlık elementini arıyoruz (H2 etiketi genellikle temiz başlığı içerir)
        title_element = article_card.find('h2') 
        
        # Eğer h2 yoksa, 'title' içeren class'ları deneyelim (Riot bazen değiştirir)
        if not title_element:
            title_element = article_card.select_one('[class*="title"]')

        if title_element:
            title = title_element.get_text().strip()
        else:
            # Yedek plan: Metni al ve temizle (İlk satırı al gibi)
            title = article_card.get_text(separator='|').split('|')[0].strip()

        link = article_card['href']
        if not link.startswith('http'):
            link = "https://teamfighttactics.leagueoflegends.com" + link
            
        return {"title": title, "link": link}
    except Exception as e:
        print(f"Hata: {e}")
        return None

def main():
    news = get_latest_tft_news()
    if not news: return

    # Daha önce paylaşılan haberi kontrol et
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    if news['link'] != last_link:

        ROLE_ID = "1483254703818276976"
        payload = {
            "username": "TFT Haber Botu",
            "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!** <@&{ROLE_ID}> \n\n**{news['title']}**\n{news['link']}"
        }
        requests.post(WEBHOOK_URL, json=payload)
        
        # Son haberi güncelle
        with open(LAST_NEWS_FILE, "w") as f:
            f.write(news['link'])
        print(f"Yeni haber gönderildi: {news['title']}")
    else:
        print("Yeni haber yok.")

if __name__ == "__main__":
    main()
