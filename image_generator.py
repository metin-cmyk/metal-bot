"""
Haber görseli oluşturur.
- Haberin orijinal fotoğrafını arkaya koyar
- therockula-post-overlay.png yi üstüne bindirir
- Sol üste kategori, sol alta başlık yazar
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

OVERLAY_PATH = Path("therockula-post-overlay.png")
FONT_PATH    = Path("fonts/BarlowCondensed-SemiBold.ttf")

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
    lum    = lum[:,:,np.newaxis]
    out    = bg_arr * (1 - lum) + ov_arr * lum
    return Image.fromarray(out.astype(np.uint8))

def create_image(news_item: dict) -> Path:
    photo = _fetch_image(news_item.get("image_url"))
    bg    = _prepare_bg(photo) if photo else Image.new("RGB", SIZE, (8, 8, 8))

    if OVERLAY_PATH.exists():
        result = _blend(bg, Image.open(OVERLAY_PATH))
    else:
        result = bg

    draw     = ImageDraw.Draw(result)
    category = news_item.get("category", "general")
    label    = CATEGORY_LABELS.get(category, "METAL HABER")
    title    = news_item.get("title", "")

    # Kategori etiketi - sol ust
    f_cat = _font(60)
    bbox  = draw.textbbox((50, 50), label, font=f_cat)
    draw.rectangle([bbox[0]-12, bbox[1]-8, bbox[2]+12, bbox[3]+8], fill=(200, 20, 20))
    draw.text((50, 50), label, font=f_cat, fill=(255, 255, 255))

    # Baslik - sol alt (THE ROCKULA in ustune cikmasin, max y=880)
    f_title = _font(48)
    line_h  = 58
    lines   = textwrap.fill(title, width=30).split("\n")[:6]
    y       = 880 - len(lines) * line_h
    for line in lines:
        draw.text((52, y+2), line, font=f_title, fill=(0, 0, 0))
        draw.text((50, y),   line, font=f_title, fill=(255, 255, 255))
        y += line_h

    safe = re.sub(r"[^a-z0-9]", "_", title.lower())[:40]
    path = OUTPUT_DIR / f"{safe}_{int(time.time())}.jpg"
    result.save(path, "JPEG", quality=92)
    return path
