"""
Haber gorseli olusturur.
- Haberin orijinal fotografini arkaya koyar
- therockula-post-overlay.png yi ustune bindirir
- Sol uste kategori (60pt), sol alta baslik (30pt) Barlow Condensed SemiBold
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

# Font ve overlay ana klasorde
OVERLAY_PATH = Path("therockula-post-overlay.png")
FONT_PATH    = Path("BarlowCondensed-SemiBold.ttf")

CATEGORY_LABELS = {
    "turkey_concert": "TR KONSER",
    "release":        "YENI CIKIS",
    "concert":        "KONSER",
    "general":        "METAL HABER",
}

def _font(size):
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size)
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
    img = ImageEnhance.Brightness(img).enhance(0.7)
    return img

def _blend(bg, overlay):
    ov     = overlay.convert("RGB").resize(SIZE, Image.LANCZOS)
    ov_arr = np.array(ov).astype(float)
    bg_arr = np.array(bg).astype(float)
    lum    = (ov_arr[:,:,0]*0.299 + ov_arr[:,:,1]*0.587 + ov_arr[:,:,2]*0.114) / 255.0
    lum    = lum[:,:, np.newaxis]
    out    = bg_arr * (1 - lum) + ov_arr * lum
    return Image.fromarray(out.astype(np.uint8))

def create_image(news_item: dict) -> Path:
    # 1. Arkaplan
    photo = _fetch_image(news_item.get("image_url"))
    bg    = _prepare_bg(photo) if photo else Image.new("RGB", SIZE, (8, 8, 8))

    # 2. Overlay bindirme
    if OVERLAY_PATH.exists():
        result = _blend(bg, Image.open(OVERLAY_PATH))
    else:
        result = bg

    draw     = ImageDraw.Draw(result)
    category = news_item.get("category", "general")
    label    = CATEGORY_LABELS.get(category, "METAL HABER")
    title    = news_item.get("title", "")

    # Piksel cinsinden pt -> px (96 dpi: 1pt = 1.333px)
    # 60pt = 80px, 30pt = 40px
    f_cat   = _font(80)   # 60pt
    f_title = _font(40)   # 30pt

    # Sol ust - kategori etiketi
    pad_x, pad_y = 50, 50
    bbox = draw.textbbox((pad_x, pad_y), label, font=f_cat)
    draw.rectangle(
        [bbox[0]-14, bbox[1]-10, bbox[2]+14, bbox[3]+10],
        fill=(200, 20, 20)
    )
    draw.text((pad_x, pad_y), label, font=f_cat, fill=(255, 255, 255))

    # Sol alt - baslik (THE ROCKULA logosu y=920 civarinda, ona cikmasin)
    line_h     = 48
    max_bottom = 900
    lines      = textwrap.fill(title, width=36).split("\n")[:7]
    y          = max_bottom - len(lines) * line_h

    for line in lines:
        draw.text((52, y+2), line, font=f_title, fill=(0, 0, 0))    # golge
        draw.text((50, y),   line, font=f_title, fill=(255, 255, 255))
        y += line_h

    safe = re.sub(r"[^a-z0-9]", "_", title.lower())[:40]
    path = OUTPUT_DIR / f"{safe}_{int(time.time())}.jpg"
    result.save(path, "JPEG", quality=92)
    return path
