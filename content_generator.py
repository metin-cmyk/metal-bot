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
Yanıtını TAM OLARAK şu formatta ver, başka hiçbir şey ekleme:

CAPTION:
[2-3 cümle İngilizce haber özeti]

🇹🇷 [2-3 cümle Türkçe özet]

#hashtag1 #hashtag2 #hashtag3 (15-18 hashtag)
---
TR_OZET:
[Maksimum 8 kelime Türkçe özet - görsel için]"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": f"Başlık: {title}\nÖzet: {summary[:400]}"}]
    )

    response = msg.content[0].text.strip()

    # Parse et
    caption    = ""
    tr_summary = ""

    if "---\nTR_OZET:" in response:
        parts      = response.split("---\nTR_OZET:")
        caption    = parts[0].replace("CAPTION:", "").strip()
        tr_summary = parts[1].strip()
    elif "TR_OZET:" in response:
        parts      = response.split("TR_OZET:")
        caption    = parts[0].replace("CAPTION:", "").strip()
        tr_summary = parts[1].strip()
    else:
        caption = response.replace("CAPTION:", "").strip()

    return {"caption": caption, "tr_summary": tr_summary}
