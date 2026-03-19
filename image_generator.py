"""
Haber için 1080x1080 Instagram görseli oluşturur.
Orijinal görsel varsa kullanır, yoksa siyah-kırmızı metal şablon yapar.
"""

import os
import re
import time
import textwrap
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO

OUTPUT_DIR = Path("images")
OUTPUT_DIR.mkdir(exist_ok=True)

SIZE = (1080, 1080)

CATEGORY_LABELS = {
    "turkey_concert": "TR KONSER",
    "release":        "YENİ ÇIKIŞ",
    "concert":        "KONSER",
    "general":        "METAL HABER",
}

def _font(size, bold=False):
    paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/freefont/FreeSans{'Bold' if bold else ''}.ttf",
    ]
    for p in paths:
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

def create_image(news_item: dict) -> Path:
    base = _fetch_image(news_item.get("image_url"))

    if base:
        w, h = base.size
        s = min(w, h)
        img = base.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))
        img = img.resize(SIZE, Image.LANCZOS)
        img = ImageEnhance.Brightness(img).enhance(0.45)
    else:
        img = Image.new("RGB", SIZE, (10, 10, 10))
        draw = ImageDraw.Draw(img)
        for i in range(6):
            y = 80 + i * 160
            draw.rectangle([0, y, SIZE[0], y+2], fill=(160, 15, 15))
        draw.rectangle([0, 0, SIZE[0], 6], fill=(200, 20, 20))
        draw.rectangle([0, SIZE[1]-6, SIZE[0], SIZE[1]], fill=(200, 20, 20))

    draw = ImageDraw.Draw(img, "RGBA")

    # Alt karartma
    for i in range(500):
        a = int(210 * (i / 500))
        draw.rectangle([0, SIZE[1]-500+i, SIZE[0], SIZE[1]-500+i+1], fill=(0, 0, 0, a))

    # Kategori etiketi
    category = news_item.get("category", "general")
    label = CATEGORY_LABELS.get(category, "METAL HABER")
    f_label = _font(34, bold=True)
    bbox = draw.textbbox((50, 50), label, font=f_label)
    draw.rectangle([bbox[0]-14, bbox[1]-10, bbox[2]+14, bbox[3]+10], fill=(190, 15, 15))
    draw.text((50, 50), label, font=f_label, fill=(240, 240, 240))

    # Ana başlık
    f_title = _font(54, bold=True)
    wrapped = textwrap.fill(news_item["title"], width=26)
    lines = wrapped.split("\n")
    y = SIZE[1] - len(lines) * 68 - 90
    for line in lines:
        draw.text((52, y+2), line, font=f_title, fill=(0, 0, 0))
        draw.text((50, y),   line, font=f_title, fill=(240, 240, 240))
        y += 68

    # Kaynak
    f_src = _font(28)
    draw.text((50, SIZE[1]-55), f"via {news_item['source']}", font=f_src, fill=(160, 160, 160))

    # Hesap adı
    handle = os.getenv("IG_HANDLE", "@therockula")
    f_hdl = _font(30, bold=True)
    bbox2 = draw.textbbox((0, 0), handle, font=f_hdl)
    tx = SIZE[0] - (bbox2[2]-bbox2[0]) - 50
    draw.text((tx, SIZE[1]-55), handle, font=f_hdl, fill=(210, 30, 30))

    name = re.sub(r"[^a-z0-9]", "_", news_item["title"].lower())[:40]
    path = OUTPUT_DIR / f"{name}_{int(time.time())}.jpg"
    img.save(path, "JPEG", quality=92)
    return path
