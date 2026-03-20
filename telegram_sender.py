import os, logging, threading, requests
from pathlib import Path

log = logging.getLogger(__name__)

TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

_run_callback = None
_last_offset  = 0

def set_run_callback(fn):
    global _run_callback
    _run_callback = fn

def send_to_telegram(image_path, caption, news_item):
    with open(image_path, "rb") as img:
        r = requests.post(
            "https://api.telegram.org/bot%s/sendPhoto" % TELEGRAM_TOKEN,
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"photo": img},
            timeout=30,
        )
        r.raise_for_status()

    r = requests.post(
        "https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_TOKEN,
        data={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       caption,
            "parse_mode": "Markdown",
        },
        timeout=30,
    )
    r.raise_for_status()

def _send_message(text):
    requests.post(
        "https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_TOKEN,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=10,
    )

def _poll_commands():
    global _last_offset
    while True:
        try:
            r = requests.get(
                "https://api.telegram.org/bot%s/getUpdates" % TELEGRAM_TOKEN,
                params={"offset": _last_offset + 1, "timeout": 30},
                timeout=40,
            )
            updates = r.json().get("result", [])
            for update in updates:
                _last_offset = update["update_id"]
                msg  = update.get("message", {})
                text = msg.get("text", "").strip().lower()

                if text == "/start":
                    _send_message(
                        "Merhaba! Metal Haber Bot aktif.\n\n"
                        "Komutlar:\n"
                        "/haber - 1 haber gonder\n"
                        "/haber5 - 5 haber gonder\n"
                        "/haber10 - 10 haber gonder\n"
                        "/durum - bot durumu"
                    )
                elif text == "/haber":
                    _send_message("1 haber hazirlanıyor...")
                    threading.Thread(target=_run_callback, args=(1,), daemon=True).start()
                elif text == "/haber5":
                    _send_message("5 haber hazirlanıyor...")
                    threading.Thread(target=_run_callback, args=(5,), daemon=True).start()
                elif text == "/haber10":
                    _send_message("10 haber hazirlanıyor...")
                    threading.Thread(target=_run_callback, args=(10,), daemon=True).start()
                elif text == "/durum":
                    import json
                    posted_file = Path("posted.json")
                    count = len(json.loads(posted_file.read_text())) if posted_file.exists() else 0
                    _send_message("Bot calisiyor!\nToplam gonderilen: %d haber\nSonraki: 2 saatte bir" % count)
        except Exception as e:
            log.warning("Polling hatasi: %s" % e)

def start_command_listener():
    t = threading.Thread(target=_poll_commands, daemon=True)
    t.start()
    log.info("Telegram komut dinleyici basladi.")
