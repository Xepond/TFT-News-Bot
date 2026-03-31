import requests
from bs4 import BeautifulSoup
import os

TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
LAST_NEWS_FILE = "last_news.txt"
ROLE_ID = "1483254703818276976"

# BURAYA ".png" VEYA ".jpg" İLE BİTEN DIRECT LİNKİ YAPIŞTIR!
CLUB_LOGO_URL = "https://imgur.com/a/5oo2FQ6.png" 

def get_latest_tft_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Haber kartını bul (Sadece içinde '/news/' veya '/game-updates/' geçen linkleri al ki menü linklerine takılmayalım)
        article_card = soup.find('a', href=lambda x: x and ('/news/' in x.lower() or '/game-updates/' in x.lower()))
        if not article_card: return None

        # 2. Başlığı Bulma (Kategori etiketlerini atlayıp ASIL başlığı bulma mantığı)
        title = ""
        # Bütün h2, h3 ve p etiketlerini topla, en uzun metne sahip olan genelde asıl başlıktır
        text_elements = article_card.find_all(['h2', 'h3', 'p', 'span'])
        longest_text = ""
        for elem in text_elements:
            text = elem.get_text(strip=True)
            if len(text) > len(longest_text) and text not in ["Oyun Güncellemeleri", "Yama Notları", "Geliştiricilerden"]:
                longest_text = text
        
        title = longest_text if longest_text else "Yeni TFT Haberi"

        # 3. Linki Oluştur
        link = article_card['href']
        if not link.startswith('http'):
            link = "https://teamfighttactics.leagueoflegends.com" + link

        # 4. Haberin Resmini Bul
        img_tag = article_card.find('img')
        image_url = ""
        if img_tag:
            image_url = img_tag.get('src') or img_tag.get('data-src') or ""
            # Bazen Riot arka plan resmi kullanır
        else:
            div_img = article_card.find('div', style=lambda s: s and 'background-image' in s)
            if div_img:
                # Arka plan urlsini ayrıştır
                style = div_img['style']
                start = style.find("url('") + 5
                end = style.find("')", start)
                if start > 4 and end > 0:
                    image_url = style[start:end]

        return {"title": title, "link": link, "image": image_url}
    
    except Exception as e:
        print(f"Scraping Hatası: {e}")
        return None

def main():
    news = get_latest_tft_news()
    if not news: return

    last_link = ""
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip()

    if news['link'] != last_link:
        
        # Embed Yapısını Yeniden Tasarladık
        embed = {
            "title": news['title'],
            "url": news['link'], # Başlığı tıklanabilir yapar
            "description": f"Haberin tamamını okumak için [Riot Games Sitesine Git]({news['link']})\n\n🔗 **Direkt Link:** {news['link']}",
            "color": 16753920 
        }

        # Eğer haber resmi varsa ekle
        if news.get('image') and news['image'].startswith("http"):
            embed["image"] = {"url": news['image']}

        # Kulüp logosunu .png/.jpg kontrolü ile ekle
        if CLUB_LOGO_URL.startswith("http") and ("png" in CLUB_LOGO_URL.lower() or "jpg" in CLUB_LOGO_URL.lower()):
            embed["footer"] = {
                "text": "ESOGÜ Riot Kampüs Elçiliği",
                "icon_url": CLUB_LOGO_URL
            }
            embed["thumbnail"] = {"url": CLUB_LOGO_URL} # Logoyu sağ üste de küçük olarak ekler, çok şık durur

        payload = {
            "username": "TFT Haber Botu",
            "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!** <@&{ROLE_ID}>",
            "embeds": [embed]
        }

        # Gönderim
        res = requests.post(WEBHOOK_URL, json=payload)
        
        if res.status_code in [200, 204]:
            with open(LAST_NEWS_FILE, "w") as f:
                f.write(news['link'])
            print(f"Başarı: Yeni haber gönderildi! ({news['title']})")
        else:
            print(f"Discord Hatası! Kod: {res.status_code}")
    else:
        print("Yeni haber yok.")

if __name__ == "__main__":
    main()
