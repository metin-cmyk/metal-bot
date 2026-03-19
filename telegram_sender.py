"""
Telegram'a gorsel + caption gonderir.
"""

import os
import logging
import requests
from pathlib import Path

log = logging.getLogger(__name__)

TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_to_telegram(image_path: Path, caption: str, news_item: dict):
    # 1. Gorseli gonder
    with open(image_path, "rb") as img:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"photo": img},
            timeout=30,
        )
        r.raise_for_status()

    # 2. Caption'i ayri mesaj olarak gonder (kopyalamak kolay olsun)
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       caption,
            "parse_mode": "Markdown",
        },
        timeout=30,
    )
    r.raise_for_status()
    log.info("Telegram'a gonderildi.")
