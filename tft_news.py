import requests
from bs4 import BeautifulSoup
import os

# Ayarlar
TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
LAST_NEWS_FILE = "last_news.txt"
ROLE_ID = "1483254703818276976"

# DİKKAT: Kulüp logunun İNTERNET LİNKİNİ buraya yapıştır
CLUB_LOGO_URL = "https://imgur.com/a/5oo2FQ6"

def get_latest_tft_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Ana haber kartını buluyoruz
        article_card = soup.find('a', href=True)
        if not article_card: return None
            
        # 2. Başlık elementini arıyoruz (Senin sağlam mantığın)
        title_element = article_card.find('h2') 
        if not title_element:
            title_element = article_card.select_one('[class*="title"]')

        if title_element:
            title = title_element.get_text().strip()
        else:
            title = article_card.get_text(separator='|').split('|')[0].strip()

        # 3. Linki oluşturuyoruz
        link = article_card['href']
        if not link.startswith('http'):
            link = "https://teamfighttactics.leagueoflegends.com" + link

        # 4. RESİM BULMA (Yeni Kısım)
        img_tag = article_card.find('img')
        image_url = ""
        if img_tag:
            # Riot'un farklı resim yükleme tekniklerine karşı önlem
            image_url = img_tag.get('src') or img_tag.get('data-src') or ""
            if not image_url and img_tag.get('srcset'):
                image_url = img_tag.get('srcset').split(" ")[0]
            
        return {"title": title, "link": link, "image": image_url}
    
    except Exception as e:
        print(f"Hata (Scraping): {e}")
        return None

def main():
    news = get_latest_tft_news()
    if not news: return

    last_link = ""
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip()

    if news['link'] != last_link:
        
        # HATA KORUMASI 1: Temel Embed Yapısı (Resimsiz)
        embed = {
            "title": news['title'],
            "url": news['link'],
            "color": 16753920 # TFT Turuncusu
        }

        # HATA KORUMASI 2: Sadece geçerli bir resim linki varsa Embed'e ekle
        if news.get('image') and news['image'].startswith("http"):
            embed["image"] = {"url": news['image']}

        # HATA KORUMASI 3: Sadece geçerli bir logo linki varsa Footer'a ekle
        footer_dict = {"text": "ESOGÜ Riot Kampüs Elçiliği"}
        if CLUB_LOGO_URL.startswith("http"):
            footer_dict["icon_url"] = CLUB_LOGO_URL
        embed["footer"] = footer_dict

        # Ana Payload'u birleştiriyoruz
        payload = {
            "username": "TFT Haber Botu",
            "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!** <@&{ROLE_ID}>",
            "embeds": [embed]
        }

        # İsteğe bağlı: Botun profil resmini de kulüp logon yapıyoruz
        if CLUB_LOGO_URL.startswith("http"):
            payload["avatar_url"] = CLUB_LOGO_URL

        # Discord'a gönderim
        res = requests.post(WEBHOOK_URL, json=payload)
        
        if res.status_code in [200, 204]:
            with open(LAST_NEWS_FILE, "w") as f:
                f.write(news['link'])
            print(f"Başarı: Yeni haber gönderildi! ({news['title']})")
        else:
            print(f"Discord Hatası! Kod: {res.status_code}, Detay: {res.text}")
    else:
        print("Yeni haber yok.")

if __name__ == "__main__":
    main()
