"""
Haber gorseli olusturur.
- Haberin fotografini arkaya koyar (blend ile)
- Overlay ustune bindirilir
- Sol uste kategori (45pt, kirmizi kutu yok)
- Sol altta baslik EN (30pt Bold) + TR ozet (30pt Regular)
- THE ROCKULA logosunun ustune cikmaz
"""

import os
import re
import time
import textwrap
import requests
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO

OUTPUT_DIR = Path("images")
OUTPUT_DIR.mkdir(exist_ok=True)

SIZE = (1080, 1080)

OVERLAY_PATH   = Path("therockula-post-overlay.png")
FONT_BOLD_PATH = Path("BarlowCondensed-SemiBold.ttf")
FONT_REG_PATH  = Path("BarlowCondensed-Regular.ttf")

CATEGORY_LABELS = {
    "turkey_concert": "KONSER",
    "release":        "YENI CIKIS",
    "concert":        "KONSER",
    "general":        "METAL HABER",
}

def _font(size, bold=True):
    path = FONT_BOLD_PATH if bold else FONT_REG_PATH
    if path.exists():
        return ImageFont.truetype(str(path), size)
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _fetch_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except:
        return None

def _prepare_bg(photo):
    w, h = photo.size
    s = min(w, h)
    img = photo.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))
    img = img.resize(SIZE, Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.65)
    return img

def _blend(bg, overlay):
    """
    Screen blend: overlay'in parlak alanlari (ates) one cikiyor,
    karanlik merkez transparan gibi davranip arkaplanı gosteriyor.
    """
    ov     = overlay.convert("RGB").resize(SIZE, Image.LANCZOS)
    ov_arr = np.array(ov).astype(float) / 255.0
    bg_arr = np.array(bg).astype(float) / 255.0

    # Screen blend modu: 1 - (1-a)*(1-b)
    out = 1.0 - (1.0 - bg_arr) * (1.0 - ov_arr)
    out = np.clip(out * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(out)

def create_image(news_item: dict) -> Path:
    # 1. Arkaplan
    photo = _fetch_image(news_item.get("image_url"))
    bg    = _prepare_bg(photo) if photo else Image.new("RGB", SIZE, (15, 15, 15))

    # 2. Overlay (screen blend)
    if OVERLAY_PATH.exists():
        overlay = Image.open(OVERLAY_PATH).convert("RGB")
        result  = _blend(bg, overlay)
    else:
        result = bg

    draw     = ImageDraw.Draw(result)
    category = news_item.get("category", "general")
    label    = CATEGORY_LABELS.get(category, "METAL HABER")
    title    = news_item.get("title", "")
    summary  = news_item.get("summary", "")

    # pt -> px (96dpi): 45pt=60px, 30pt=40px
    f_cat   = _font(60, bold=True)    # 45pt kategori
    f_title = _font(40, bold=True)    # 30pt baslik (bold)
    f_tr    = _font(40, bold=False)   # 30pt Turkce ozet (regular)

    # ── Sol ust: kategori (kirmizi kutu yok, sadece beyaz yazi) ──
    draw.text((50, 50), label, font=f_cat, fill=(255, 255, 255))

    # ── Sol alt: EN baslik + TR ozet ──
    # THE ROCKULA logosu yaklasik y=930, ona cikmasin
    # Asagi hizala: metinleri asagidan yukari dogru diz

    line_h_title = 46
    line_h_tr    = 44
    margin_left  = 50
    logo_y       = 930   # THE ROCKULA'nin y pozisyonu

    # Turkce ozet - ilk 120 karakter, 1 satir
    tr_text = summary[:120] if summary else ""
    tr_lines = textwrap.fill(tr_text, width=42).split("\n")[:2]

    # EN baslik
    en_lines = textwrap.fill(title, width=36).split("\n")[:4]

    # Toplam yukseklik hesapla
    total_h = (len(en_lines) * line_h_title) + (len(tr_lines) * line_h_tr) + 12  # 12px aralik

    y = logo_y - total_h

    # EN baslik yaz
    for line in en_lines:
        draw.text((margin_left+2, y+2), line, font=f_title, fill=(0, 0, 0))
        draw.text((margin_left,   y),   line, font=f_title, fill=(255, 255, 255))
        y += line_h_title

    y += 12  # EN ile TR arasi bosluk

    # TR ozet yaz (biraz daha soluk - %80 beyaz)
    for line in tr_lines:
        draw.text((margin_left+2, y+2), line, font=f_tr, fill=(0, 0, 0))
        draw.text((margin_left,   y),   line, font=f_tr, fill=(200, 200, 200))
        y += line_h_tr

    safe = re.sub(r"[^a-z0-9]", "_", title.lower())[:40]
    path = OUTPUT_DIR / f"{safe}_{int(time.time())}.jpg"
    result.save(path, "JPEG", quality=92)
    return path
