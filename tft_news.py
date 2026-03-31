import requests
from bs4 import BeautifulSoup
import os

TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
LAST_NEWS_FILE = "last_news.txt"
ROLE_ID = "1483254703818276976"

# DİKKAT: Linkin sonu MUTLAKA .png veya .jpg ile bitmeli!
CLUB_LOGO_URL = "https://i.imgur.com/sqOABeG.jpeg" 

def get_latest_tft_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Ana haber kartını bul
        article_card = soup.find('a', href=lambda x: x and ('/news/' in x.lower() or '/game-updates/' in x.lower()))
        if not article_card: return None

        # 2. AKILLI METİN AYRIŞTIRICI (Sorunu çözen kısım)
        # Kartın içindeki tüm metinleri liste halinde alır
        all_texts = [text.strip() for text in article_card.stripped_strings if text.strip()]
        
        valid_texts = []
        for text in all_texts:
            # Kategorileri ve o çirkin ISO tarih formatını (2026-03-30T...) atlıyoruz
            if text in ["Oyun Güncellemeleri", "Yama Notları", "Geliştiricilerden", "Haberler"]: continue
            if "202" in text and "T" in text and "Z" in text: continue 
            valid_texts.append(text)

        # Temizlenen listede 1. eleman başlık, 2. eleman özet olur
        title = valid_texts[0] if len(valid_texts) > 0 else "Yeni TFT Haberi"
        summary = valid_texts[1] if len(valid_texts) > 1 else ""

        # 3. Link
        link = article_card['href']
        if not link.startswith('http'):
            link = "https://teamfighttactics.leagueoflegends.com" + link

        # 4. Gelişmiş Resim Bulucu
        image_url = ""
        img_tag = article_card.find('img')
        if img_tag:
            image_url = img_tag.get('src') or img_tag.get('data-src') or ""
        
        # Bazen Riot resimleri <source> etiketi içinde tutar
        if not image_url:
            source = article_card.find('source')
            if source and source.get('srcset'):
                image_url = source.get('srcset').split(',')[0].split(' ')[0]

        return {"title": title, "link": link, "summary": summary, "image": image_url}
    
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
        
        # Tasarımı Sadeleştirdik ve Güzelleştirdik
        desc_text = f"{news['summary']}\n\n🔗 [Haberin Tamamını Oku]({news['link']})"
        
        embed = {
            "title": news['title'],
            "url": news['link'], 
            "description": desc_text,
            "color": 16753920 
        }

        # Ana Haber Resmi
        if news.get('image') and news['image'].startswith("http"):
            embed["image"] = {"url": news['image']}

        # Kulüp Logosu (Eğer link doğru formattaysa ekler, yoksa hatayı önlemek için pas geçer)
        if CLUB_LOGO_URL.startswith("http") and ("png" in CLUB_LOGO_URL.lower() or "jpg" in CLUB_LOGO_URL.lower()):
            embed["footer"] = {
                "text": "ESOGÜ Riot Kampüs Elçiliği",
                "icon_url": CLUB_LOGO_URL
            }
            embed["thumbnail"] = {"url": CLUB_LOGO_URL}

        payload = {
            "username": "TFT Haber Botu",
            "content": f"📢 **Yeni Bir Güncelleme Var!** <@&{ROLE_ID}>",
            "embeds": [embed]
        }

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
