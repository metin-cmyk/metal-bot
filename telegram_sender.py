"""
Telegram'a görsel + caption gönderir.
Onay butonu yok — direkt gönderir, sen Instagram'a manuel yapıştırırsın.
"""

import os
import logging
import requests
from pathlib import Path

log = logging.getLogger(__name__)

TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CATEGORY_EMOJI = {
    "turkey_concert": "🇹🇷",
    "release":        "🎵",
    "concert":        "🎸",
    "general":        "⚡",
}

def send_to_telegram(image_path: Path, caption: str, news_item: dict):
    """Görseli ve caption'ı Telegram'a gönderir."""

    emoji = CATEGORY_EMOJI.get(news_item.get("category", "general"), "⚡")

    # Önce görseli gönder
    with open(image_path, "rb") as img:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"photo": img},
            timeout=30,
        )
        r.raise_for_status()

    # Sonra caption'ı ayrı mesaj olarak gönder (kopyalamak kolay olsun)
    mesaj = (
        f"{emoji} *Yeni haber hazır — Instagram'a yapıştır!*\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{caption}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📰 Kaynak: {news_item['source']}\n"
        f"🔗 {news_item['link']}"
    )

    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       mesaj,
            "parse_mode": "Markdown",
        },
        timeout=30,
    )
    r.raise_for_status()
    log.info("Telegram'a gönderildi.")
