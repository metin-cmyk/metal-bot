"""
Gorsel bulamazsa su sırayla dener:
1. RSS'deki image_url
2. Haberin orijinal sayfasindan og:image
3. Google Images'dan grup adi ile arama
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def _try_url(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=6, headers=HEADERS)
        r.raise_for_status()
        # En az 10KB olmali (kucuk ikonlari eliyoruz)
        if len(r.content) < 10000:
            return None
        return r.content
    except:
        return None

def _fetch_og_image(page_url):
    """Haberin orijinal sayfasindan og:image cek."""
    try:
        r = requests.get(page_url, timeout=8, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # og:image
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # twitter:image
        tw = soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            return tw["content"]

        # Sayfadaki en buyuk gorsel
        imgs = soup.find_all("img", src=True)
        for img in imgs:
            src = img["src"]
            if src.startswith("//"):
                src = "https:" + src
            if any(x in src.lower() for x in [".jpg", ".jpeg", ".png", ".webp"]):
                if not any(x in src.lower() for x in ["logo", "icon", "avatar", "thumb"]):
                    return src
    except:
        pass
    return None

def _search_google_image(query):
    """Google Images'dan gorsel ara."""
    try:
        search_url = "https://www.google.com/search?q=%s&tbm=isch" % requests.utils.quote(query)
        r = requests.get(search_url, timeout=8, headers=HEADERS)
        # og:image linklerini bul
        matches = re.findall(r'https://[^"\']+\.(?:jpg|jpeg|png|webp)', r.text)
        for url in matches[:5]:
            if "gstatic" in url or "googleapis" in url:
                continue
            content = _try_url(url)
            if content:
                return url
    except:
        pass
    return None

def get_best_image_url(news_item):
    """
    En iyi gorsel URL'sini bulur.
    Sirayila: RSS url -> og:image -> Google arama
    """
    # 1. RSS'deki url
    rss_url = news_item.get("image_url")
    if rss_url and _try_url(rss_url):
        return rss_url

    # 2. Haberin sayfasindan og:image
    page_url = news_item.get("link")
    if page_url:
        og_url = _fetch_og_image(page_url)
        if og_url and _try_url(og_url):
            return og_url

    # 3. Google'dan grup adi ile ara
    grup_adi = news_item.get("grup_adi", "")
    if grup_adi and grup_adi != "NEWS":
        query = "%s band metal" % grup_adi
        google_url = _search_google_image(query)
        if google_url:
            return google_url

    # 4. Haber basligiyla ara
    title = news_item.get("title", "")
    if title:
        google_url = _search_google_image(title[:50] + " metal band")
        if google_url:
            return google_url

    return None
