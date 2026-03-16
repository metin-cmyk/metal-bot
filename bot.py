"""
Metal/Rock Instagram Bot — Telegram onaylı versiyon
Günde 2 kez haber önerir, sen Telegram'dan onaylarsın, sonra Instagram'a gider.
"""

import os
import json
import logging
import schedule
import time
import feedparser
import requests
from pathlib import Path
from datetime import datetime

from content_generator import generate_caption
from image_generator import create_image
from instagram_poster import post_to_instagram
from telegram_bot import send_for_approval, start_telegram_listener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

POSTED_FILE = Path("posted.json")

RSS_FEEDS = [
    "https://www.blabbermouth.net/news/feed/",
    "https://www.loudwire.com/feed/",
    "https://www.kerrang.com/feed",
    "https://www.metalinjection.net/feed",
    "https://metalstorm.net/rss/news.xml",
]

TURKEY_KEYWORDS = ["turkey", "türkiye", "istanbul", "ankara", "izmir", "konser", "tour"]

def load_posted():
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()

def save_posted(posted):
    POSTED_FILE.write_text(json.dumps(list(posted)))

def fetch_news():
    items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                items.append({
                    "title":     entry.get("title", ""),
                    "link":      entry.get("link", ""),
                    "summary":   entry.get("summary", "")[:500],
                    "source":    feed.feed.get("title", ""),
                    "image_url": _get_image(entry),
                })
        except Exception as e:
            log.warning(f"RSS hatası: {e}")
    return items

def _get_image(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url")
    return None

def categorize(item):
    text = (item["title"] + item["summary"]).lower()
    if any(k in text for k in TURKEY_KEYWORDS):
        return "turkey_concert"
    if any(k in text for k in ["album", "single", "release", "out now"]):
        return "release"
    if any(k in text for k in ["tour", "concert", "festival"]):
        return "concert"
    return "general"

def prepare_and_send():
    """Haberleri çek, en iyi 3'ünü hazırla, Telegram'a gönder."""
    log.info("Haberler çekiliyor...")
    posted = load_posted()
    items = fetch_news()

    # Daha önce paylaşılmamış haberleri filtrele
    new_items = [i for i in items if i["link"] not in posted]
    if not new_items:
        log.info("Yeni haber yok.")
        return

    # Öncelik sırala: Türkiye > release > concert > general
    priority = {"turkey_concert": 0, "release": 1, "concert": 2, "general": 3}
    for item in new_items:
        item["category"] = categorize(item)
    new_items.sort(key=lambda x: priority[x["category"]])

    # En iyi haberi seç
    selected = new_items[0]
    log.info(f"Seçilen: {selected['title']}")

    # Görsel + caption üret
    caption    = generate_caption(selected)
    image_path = create_image(selected)

    # Telegram'a gönder — onay beklemeye başla
    send_for_approval(
        image_path=image_path,
        caption=caption,
        news_item=selected,
        on_approve=lambda: _publish(selected, posted),
    )

def _publish(news_item, posted):
    """Onay gelince Instagram'a paylaş."""
    caption    = generate_caption(news_item)
    image_path = create_image(news_item)
    post_to_instagram(image_path, caption)
    posted.add(news_item["link"])
    save_posted(posted)
    log.info("✅ Instagram'a paylaşıldı!")

def main():
    log.info("Bot başlıyor...")

    # Telegram listener'ı arka planda başlat
    start_telegram_listener()

    # Zamanlayıcı: sabah 10, akşam 7
    schedule.every().day.at("10:00").do(prepare_and_send)
    schedule.every().day.at("19:00").do(prepare_and_send)

    # Hemen test etmek istersen: RUN_NOW=true python bot.py
    if os.getenv("RUN_NOW", "false") == "true":
        prepare_and_send()

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
