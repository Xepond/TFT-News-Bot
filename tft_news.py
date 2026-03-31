import requests
from bs4 import BeautifulSoup
import os

# Ayarlar
TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK") # Güvenlik için ortam değişkeni kullanıyoruz
LAST_NEWS_FILE = "last_news.txt"

def get_latest_tft_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(TARGET_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Riot'un site yapısına göre ilk haber kartını bulalım
    article = soup.find('a', href=True) # Genelde haberler <a> içinde olur
    if not article:
        return None
    
    title = article.text.strip()
    link = article['href']
    if not link.startswith('http'):
        link = "https://teamfighttactics.leagueoflegends.com" + link
        
    return {"title": title, "link": link}

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
        # Yeni haber var! Discord'a gönder
        payload = {
            "username": "TFT Haber Botu",
            "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!**\n\n**{news['title']}**\n{news['link']}"
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