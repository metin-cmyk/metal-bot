import os, re, time, textwrap, requests, numpy as np
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

def _clean(text):
    """HTML etiketlerini ve gereksiz boslukları temizle."""
    text = re.sub(r'<[^>]+>', ' ', text)          # HTML tags
    text = re.sub(r'&[a-z]+;', ' ', text)         # HTML entities
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _font(size, bold=True):
    path = FONT_BOLD_PATH if bold else FONT_REG_PATH
    if path.exists():
        return ImageFont.truetype(str(path), size)
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _fetch_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGB")
        return img
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
    ov     = overlay.convert("RGB").resize(SIZE, Image.LANCZOS)
    ov_arr = np.array(ov).astype(float) / 255.0
    bg_arr = np.array(bg).astype(float) / 255.0
    out    = 1.0 - (1.0 - bg_arr) * (1.0 - ov_arr)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

def _extract_image(entry_dict):
    """RSS entry'den gorsel URL'sini bul."""
    # Direkt image_url
    url = entry_dict.get("image_url")
    if url:
        return url
    # Summary icindeki img src
    summary = entry_dict.get("summary", "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if match:
        return match.group(1)
    return None

def create_image(news_item: dict) -> Path:
    # Gorsel URL'sini bul
    image_url = _extract_image(news_item)
    photo     = _fetch_image(image_url)
    bg        = _prepare_bg(photo) if photo else Image.new("RGB", SIZE, (15, 15, 15))

    # Overlay
    if OVERLAY_PATH.exists():
        result = _blend(bg, Image.open(OVERLAY_PATH).convert("RGB"))
    else:
        result = bg

    draw     = ImageDraw.Draw(result)
    category = news_item.get("category", "general")
    label    = CATEGORY_LABELS.get(category, "METAL HABER")
    title    = _clean(news_item.get("title", ""))
    summary  = news_item.get("tr_summary") or _clean(news_item.get("summary", ""))

    f_cat   = _font(60, bold=True)   # 45pt kategori
    f_title = _font(40, bold=True)   # 30pt baslik
    f_tr    = _font(40, bold=False)  # 30pt TR ozet

    # Sol ust: kategori (sadece beyaz yazi, kutu yok)
    draw.text((50, 50), label, font=f_cat, fill=(255, 255, 255))

    # Sol alt: EN baslik + TR ozet, THE ROCKULA'nin ustune cikmasin
    logo_y       = 930
    line_h_title = 46
    line_h_tr    = 44

    en_lines = textwrap.fill(title, width=36).split("\n")[:4]
    tr_lines = textwrap.fill(summary[:150], width=42).split("\n")[:2]

    total_h = len(en_lines)*line_h_title + 12 + len(tr_lines)*line_h_tr
    y = logo_y - total_h

    for line in en_lines:
        draw.text((52, y+2), line, font=f_title, fill=(0,0,0))
        draw.text((50, y),   line, font=f_title, fill=(255,255,255))
        y += line_h_title

    y += 12

    for line in tr_lines:
        draw.text((52, y+2), line, font=f_tr, fill=(0,0,0))
        draw.text((50, y),   line, font=f_tr, fill=(200,200,200))
        y += line_h_tr

    safe = re.sub(r"[^a-z0-9]", "_", title.lower())[:40]
    path = OUTPUT_DIR / f"{safe}_{int(time.time())}.jpg"
    result.save(path, "JPEG", quality=92)
    return path
