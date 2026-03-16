"""Claude API ile Instagram caption üretir."""

import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CATEGORY_LABELS = {
    "turkey_concert": "🇹🇷 TÜRKİYE KONSER",
    "release":        "🎵 YENİ ÇIKIŞ",
    "concert":        "🎸 KONSER",
    "general":        "⚡ METAL HABER",
}

def generate_caption(news_item: dict) -> str:
    category = news_item.get("category", "general")
    is_turkish = category == "turkey_concert"

    system = """Sen bir Metal/Rock Instagram hesabının içerik yazarısın.
Türkiye konserleri için TAMAMEN TÜRKÇE yaz.
Diğer haberler için İngilizce caption yaz, altına kısa Türkçe özet ekle.
3-4 cümle, enerjik ton, 15-18 hashtag ekle. Emoji kullan ama abartma."""

    prompt = f"""Başlık: {news_item['title']}
Kaynak: {news_item['source']}
Özet: {news_item['summary']}

Bu haberi Instagram gönderisine dönüştür."""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()
