import os, re, time, textwrap, requests, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from image_fetcher import get_best_image_url

OUTPUT_DIR = Path("images")
OUTPUT_DIR.mkdir(exist_ok=True)
SIZE = (1080, 1350)

OVERLAY_PATH   = Path("therockula-post-overlay.png")
FONT_BOLD_PATH = Path("BarlowCondensed-SemiBold.ttf")
FONT_REG_PATH  = Path("BarlowCondensed-Regular.ttf")

def _font(size, bold=True):
    path = FONT_BOLD_PATH if bold else FONT_REG_PATH
    if path.exists():
        return ImageFont.truetype(str(path), size)
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _clean(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def _fetch_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (15, 15, 15))
            bg.paste(img, mask=img.split()[3])
            return bg
        return img.convert("RGB")
    except:
        return None

def _prepare_bg(photo):
    w, h = photo.size
    new_w = 1080
    new_h = int(h * new_w / w)
    if new_h < 1350:
        new_h = 1350
        new_w = int(w * new_h / h)
    img  = photo.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - 1080) // 2
    top  = (new_h - 1350) // 2
    img  = img.crop((left, top, left + 1080, top + 1350))
    img  = ImageEnhance.Brightness(img).enhance(0.65)
    return img

def _blend(bg, overlay):
    ov     = overlay.convert("RGB").resize(SIZE, Image.LANCZOS)
    ov_arr = np.array(ov).astype(float) / 255.0
    bg_arr = np.array(bg).astype(float) / 255.0
    out    = 1.0 - (1.0 - bg_arr) * (1.0 - ov_arr)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

def create_image(news_item):
    # En iyi gorseli bul
    image_url = get_best_image_url(news_item)
    photo     = _fetch_image(image_url)
    bg        = _prepare_bg(photo) if photo else Image.new("RGB", SIZE, (15, 15, 15))

    if OVERLAY_PATH.exists():
        result = _blend(bg, Image.open(OVERLAY_PATH).convert("RGB"))
    else:
        result = bg

    draw     = ImageDraw.Draw(result)
    title    = _clean(news_item.get("title", ""))
    tr_text  = news_item.get("tr_summary", "")
    grup_adi = news_item.get("grup_adi", "")

    f_grup  = _font(80, bold=True)
    f_title = _font(40, bold=True)
    f_tr    = _font(40, bold=False)

    # Sol ust: grup adi
    if grup_adi and grup_adi != "NEWS":
        draw.text((50, 50), grup_adi.upper(), font=f_grup, fill=(255, 255, 255))

    # Sol alt: baslik + TR ozet
    logo_y       = 1200
    line_h_title = 48
    line_h_tr    = 44

    en_lines = textwrap.fill(title, width=42).split("\n")[:4]
    tr_lines = textwrap.fill(tr_text, width=46).split("\n")[:2] if tr_text else []

    total_h = len(en_lines)*line_h_title + (12 + len(tr_lines)*line_h_tr if tr_lines else 0)
    y = logo_y - total_h

    for line in en_lines:
        draw.text((52, y+2), line, font=f_title, fill=(0, 0, 0))
        draw.text((50, y),   line, font=f_title, fill=(255, 255, 255))
        y += line_h_title

    if tr_lines:
        y += 12
        for line in tr_lines:
            draw.text((52, y+2), line, font=f_tr, fill=(0, 0, 0))
            draw.text((50, y),   line, font=f_tr, fill=(200, 200, 200))
            y += line_h_tr

    safe = re.sub(r"[^a-z0-9]", "_", title.lower())[:40]
    path = OUTPUT_DIR / f"{safe}_{int(time.time())}.jpg"
    result.save(path, "JPEG", quality=92)
    return path
