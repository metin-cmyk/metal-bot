import os, json, logging, schedule, time, feedparser, re
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from content_generator import generate_caption
from image_generator import create_image
from telegram_sender import send_to_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()]
)
log = logging.getLogger(__name__)

POSTED_FILE = Path("posted.json")

RSS_FEEDS = [
    # Orijinal kaynaklar
    "https://www.blabbermouth.net/news/feed/",
    "https://www.loudwire.com/feed/",
    "https://www.kerrang.com/feed",
    "https://www.metalinjection.net/feed",
    "https://metalstorm.net/rss/news.xml",
    # Yeni kaynaklar
    "https://www.loudersound.com/feeds.xml",          # Metal Hammer + Classic Rock
    "https://feeds.feedburner.com/Metalsucks",        # MetalSucks
    "https://decibelmagazine.com/feed",               # Decibel Magazine
    "https://www.revolvermag.com/rss.xml",            # Revolver Magazine
]

TURKEY_KEYWORDS = ["turkey", "turkiye", "istanbul", "ankara", "izmir", "konser", "tour"]

def load_posted():
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()

def save_posted(posted):
    POSTED_FILE.write_text(json.dumps(list(posted)))

def _clean(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def _get_image(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url")
    summary = entry.get("summary", "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if match:
        return match.group(1)
    return None

def _parse_date(entry):
    try:
        return parsedate_to_datetime(entry.get("published", ""))
    except:
        return datetime.now().astimezone()

def fetch_news():
    items = []
    cutoff = datetime.now().astimezone() - timedelta(days=10)
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                pub = _parse_date(entry)
                if pub < cutoff:
                    continue
                items.append({
                    "title":     _clean(entry.get("title", "")),
                    "link":      entry.get("link", ""),
                    "summary":   _clean(entry.get("summary", ""))[:500],
                    "source":    feed.feed.get("title", ""),
                    "image_url": _get_image(entry),
                    "published": pub,
                })
        except Exception as e:
            log.warning(f"RSS hatasi ({url}): {e}")
    items.sort(key=lambda x: x["published"], reverse=True)
    return items

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
    items  = [i for i in fetch_news() if i["link"] not in posted]

    if not items:
        log.info("Yeni haber yok.")
        return

    priority = {"turkey_concert": 0, "release": 1, "concert": 2, "general": 3}
    for item in items:
        item["category"] = categorize(item)
    items.sort(key=lambda x: priority[x["category"]])

    selected = items[0]
    log.info(f"Secilen: {selected['title']}")

    try:
        result     = generate_caption(selected)
        caption    = result["caption"]
        tr_baslik  = result["tr_summary"]
        selected["tr_summary"] = tr_baslik
        image_path = create_image(selected)
        send_to_telegram(image_path, caption, selected)
        posted.add(selected["link"])
        save_posted(posted)
        log.info("Gonderildi!")
    except Exception as e:
        log.error(f"Hata: {e}", exc_info=True)

def run_if_allowed():
    if 0 <= datetime.now().hour < 9:
        return
    run()

def main():
    log.info("Bot basliyor... Her 2 saatte bir, gece 00-09 arasi uyur.")
    schedule.every(2).hours.do(run_if_allowed)
    if os.getenv("RUN_NOW", "false") == "true":
        run()
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
