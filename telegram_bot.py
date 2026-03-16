"""
Telegram onay sistemi.

Bot sana görsel + caption gönderir.
Sen ✅ Paylaş veya ❌ Atla butonuna basarsın.
"""

import os
import logging
import threading
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackQueryHandler, ContextTypes
)

log = logging.getLogger(__name__)

TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # Kendi chat ID'n

# Bekleyen onayları sakla: {callback_data: on_approve_func}
_pending: dict[str, callable] = {}

app: Application = None


async def _send(image_path: Path, caption: str, news_item: dict, on_approve):
    """Telegram'a görsel + butonları gönderir."""
    key = f"approve_{news_item['link'][-20:]}"  # unique key
    _pending[key] = on_approve

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Paylaş",    callback_data=f"yes_{key}"),
            InlineKeyboardButton("❌ Atla",      callback_data=f"no_{key}"),
        ]
    ])

    preview = caption[:300] + "..." if len(caption) > 300 else caption

    with open(image_path, "rb") as img:
        await app.bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=img,
            caption=f"🤘 *Yeni haber hazır!*\n\n{preview}",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    log.info("Telegram'a gönderildi, onay bekleniyor...")


async def _button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton tıklamalarını yakalar."""
    query = update.callback_query
    await query.answer()

    data = query.data  # "yes_approve_xxx" veya "no_approve_xxx"

    if data.startswith("yes_"):
        key = data[4:]
        if key in _pending:
            on_approve = _pending.pop(key)
            await query.edit_message_caption("⏳ Paylaşılıyor...")
            try:
                on_approve()
                await query.edit_message_caption("✅ Instagram'a paylaşıldı!")
            except Exception as e:
                await query.edit_message_caption(f"❌ Hata: {e}")
        else:
            await query.edit_message_caption("Bu onay süresi dolmuş.")

    elif data.startswith("no_"):
        key = data[3:]
        _pending.pop(key, None)
        await query.edit_message_caption("❌ Atlandı.")


def send_for_approval(image_path: Path, caption: str, news_item: dict, on_approve):
    """Ana bot'tan çağrılır. Thread-safe wrapper."""
    import asyncio
    asyncio.run_coroutine_threadsafe(
        _send(image_path, caption, news_item, on_approve),
        app.loop
    )


def start_telegram_listener():
    """Telegram bot'u arka plan thread'inde başlatır."""
    global app

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CallbackQueryHandler(_button_handler))

    def run():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app._loop = loop
        loop.run_until_complete(app.initialize())
        loop.run_until_complete(app.start())
        loop.run_until_complete(app.updater.start_polling())
        loop.run_forever()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    log.info("Telegram listener başlatıldı.")
