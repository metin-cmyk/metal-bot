import os, re, anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def _clean(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def generate_caption(news_item: dict) -> dict:
    title   = _clean(news_item.get("title", ""))
    summary = _clean(news_item.get("summary", ""))

    system = """Sen bir Metal/Rock Instagram hesabının içerik yazarısın.
Yanıtını TAM OLARAK şu formatta ver:

CAPTION:
🇬🇧 [2-3 cümle İngilizce haber özeti]

🇹🇷 [2-3 cümle Türkçe özet — İngilizce ile AYNI bilgiyi içermeli]

#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5

(Sadece 5 hashtag — niş ve ilgili olanlar)
---
TR_BASLIK:
[Haber başlığının Türkçe çevirisi — maksimum 8 kelime]
---
GRUP_ADI:
[Haberdeki ana grup veya sanatçı adı — sadece isim, örn: Metallica veya Iron Maiden & Judas Priest. Birden fazla varsa en önemlisi. Grup yoksa NEWS yaz.]"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": f"Başlık: {title}\nÖzet: {summary[:400]}"}]
    )

    response = msg.content[0].text.strip()

    caption   = ""
    tr_baslik = ""
    grup_adi  = ""

    # Parse
    parts = response.split("---")
    for i, part in enumerate(parts):
        part = part.strip()
        if part.startswith("CAPTION:"):
            caption = part.replace("CAPTION:", "").strip()
        elif part.startswith("TR_BASLIK:"):
            tr_baslik = part.replace("TR_BASLIK:", "").strip()
        elif part.startswith("GRUP_ADI:"):
            grup_adi = part.replace("GRUP_ADI:", "").strip()

    return {
        "caption":    caption,
        "tr_summary": tr_baslik,
        "grup_adi":   grup_adi,
    }
