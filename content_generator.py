"""Claude API ile caption ve Turkce ozet uretir."""

import os
import re
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def _clean(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_caption(news_item: dict) -> dict:
    """
    Returns: {
        "caption": Instagram metni,
        "tr_summary": Gorsel icin kisa Turkce ozet (max 1 cumle)
    }
    """
    title   = _clean(news_item.get("title", ""))
    summary = _clean(news_item.get("summary", ""))

    system = """Sen bir Metal/Rock Instagram hesabının içerik yazarısın.
Senden iki şey isteniyor:

1. CAPTION: Instagram gönderisi
Format:
[2-3 cümle İngilizce haber]

🇹🇷 [2-3 cümle Türkçe özet]

#hashtag1 #hashtag2 ... (15-18 hashtag)

2. TR_OZET: Görsel üzerine yazılacak çok kısa Türkçe özet (MAX 10 kelime, 1 cümle)

Yanıtını KESINLIKLE şu formatta ver:
CAPTION:
[caption metni]

TR_OZET:
[kısa Türkçe özet]"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": f"Başlık: {title}\nÖzet: {summary[:400]}"}]
    )

    response = msg.content[0].text.strip()

    # Parse
    caption   = ""
    tr_summary = ""

    if "CAPTION:" in response and "TR_OZET:" in response:
        parts      = response.split("TR_OZET:")
        tr_summary = parts[1].strip()
        caption    = parts[0].replace("CAPTION:", "").strip()
    else:
        caption    = response
        tr_summary = ""

    return {"caption": caption, "tr_summary": tr_summary}
