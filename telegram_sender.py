“””
Telegram’a gorsel + caption gonderir.
Komut dinler: /haber /haber5 /haber10 /durum
“””

import os
import logging
import threading
import requests
from pathlib import Path

log = logging.getLogger(**name**)

TELEGRAM_TOKEN   = os.environ[“TELEGRAM_TOKEN”]
TELEGRAM_CHAT_ID = os.environ[“TELEGRAM_CHAT_ID”]

# Bot modülüne referans — komutlar için

_run_callback = None
_last_offset  = 0

def set_run_callback(fn):
“”“bot.py’den run fonksiyonunu buraya bağla.”””
global _run_callback
_run_callback = fn

def send_to_telegram(image_path: Path, caption: str, news_item: dict):
“”“Görsel + caption gönderir.”””
with open(image_path, “rb”) as img:
r = requests.post(
f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto”,
data={“chat_id”: TELEGRAM_CHAT_ID},
files={“photo”: img},
timeout=30,
)
r.raise_for_status()

```
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
```

def _send_message(text):
requests.post(
f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage”,
data={“chat_id”: TELEGRAM_CHAT_ID, “text”: text},
timeout=10,
)

def _poll_commands():
“”“Telegram’dan komutları dinler (long polling).”””
global _last_offset
while True:
try:
r = requests.get(
f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates”,
params={“offset”: _last_offset + 1, “timeout”: 30},
timeout=40,
)
updates = r.json().get(“result”, [])
for update in updates:
_last_offset = update[“update_id”]
msg = update.get(“message”, {})
text = msg.get(“text”, “”).strip().lower()

```
            if text == "/haber":
                _send_message("⏳ 1 haber hazırlanıyor...")
                threading.Thread(target=_run_callback, args=(1,), daemon=True).start()

            elif text == "/haber5":
                _send_message("⏳ 5 haber hazırlanıyor...")
                threading.Thread(target=_run_callback, args=(5,), daemon=True).start()

            elif text == "/haber10":
                _send_message("⏳ 10 haber hazırlanıyor...")
                threading.Thread(target=_run_callback, args=(10,), daemon=True).start()

            elif text == "/durum":
                from pathlib import Path
                import json
                posted_file = Path("posted.json")
                count = len(json.loads(posted_file.read_text())) if posted_file.exists() else 0
                _send_message(f"🤘 Bot çalışıyor!\n📰 Toplam gönderilen haber: {count}\n⏰ Sonraki haber: 2 saatte bir")

            elif text == "/start":
                _send_message(
                    "🤘 Metal Haber Bot aktif!\n\n"
                    "Komutlar:\n"
                    "/haber — 1 haber gönder\n"
                    "/haber5 — 5 haber gönder\n"
                    "/haber10 — 10 haber gönder\n"
                    "/durum — bot durumu"
                )
    except Exception as e:
        log.warning(f"Polling hatasi: {e}")
```

def start_command_listener():
“”“Komut dinleyiciyi arka planda başlat.”””
t = threading.Thread(target=_poll_commands, daemon=True)
t.start()
log.info(“Telegram komut dinleyici başlatıldı.”)