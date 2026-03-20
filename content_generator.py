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

(Sadece 5 hashtag — niş ve ilgili olanlar, örn: #metal #heavymetal #newmusic #metalinjection #progressiverock)
---
TR_BASLIK:
[Haber başlığının Türkçe çevirisi — maksimum 8 kelime]"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": f"Başlık: {title}\nÖzet: {summary[:400]}"}]
    )

    response = msg.content[0].text.strip()

    caption   = ""
    tr_baslik = ""

    if "---\nTR_BASLIK:" in response:
        parts     = response.split("---\nTR_BASLIK:")
        caption   = parts[0].replace("CAPTION:", "").strip()
        tr_baslik = parts[1].strip()
    elif "TR_BASLIK:" in response:
        parts     = response.split("TR_BASLIK:")
        caption   = parts[0].replace("CAPTION:", "").strip()
        tr_baslik = parts[1].strip()
    else:
        caption = response.replace("CAPTION:", "").strip()

    return {"caption": caption, "tr_summary": tr_baslik}
