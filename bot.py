"""
Metal/Rock Haber Botu — Sadece Telegram versiyonu
Gece 00:00-09:00 arası uyur, diğer saatlerde her 2 saatte bir haber gönderir.
"""

import os
import json
import logging
import schedule
import time
import feedparser
from pathlib import Path
from datetime import datetime

from content_generator import generate_caption
from image_generator import create_image
from telegram_sender import send_to_telegram

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

def run():
    log.info("Haberler aranıyor...")
    posted = load_posted()
    items = fetch_news()

    new_items = [i for i in items if i["link"] not in posted]
    if not new_items:
        log.info("Yeni haber yok.")
        return

    priority = {"turkey_concert": 0, "release": 1, "concert": 2, "general": 3}
    for item in new_items:
        item["category"] = categorize(item)
    new_items.sort(key=lambda x: priority[x["category"]])

    selected = new_items[0]
    log.info(f"Seçilen haber: {selected['title']}")

    try:
        caption    = generate_caption(selected)
        image_path = create_image(selected)
        send_to_telegram(image_path, caption, selected)

        posted.add(selected["link"])
        save_posted(posted)
        log.info("✅ Telegram'a gönderildi!")

    except Exception as e:
        log.error(f"Hata: {e}", exc_info=True)

def run_if_allowed():
    """Gece 00:00-09:00 arası çalışmaz."""
    hour = datetime.now().hour
    if 0 <= hour < 9:
        log.info(f"Gece modu — saat {hour}:00, atlanıyor.")
        return
    run()

def main():
    log.info("Bot başlıyor... Her 2 saatte bir kontrol eder, gece 00:00-09:00 arası uyur.")

    schedule.every(2).hours.do(run_if_allowed)

    if os.getenv("RUN_NOW", "false") == "true":
        run()

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
