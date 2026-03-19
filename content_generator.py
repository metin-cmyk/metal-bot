"""Claude API ile Instagram caption uretir."""

import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_caption(news_item: dict) -> str:
    category = news_item.get("category", "general")

    system = """Sen bir Metal/Rock Instagram hesabının içerik yazarısın.
Caption formatı KESINLIKLE şöyle olmalı:

[2-3 cümle İngilizce haber özeti]

🇹🇷 [2-3 cümle Türkçe haber özeti]

#hashtag1 #hashtag2 ... (15-18 hashtag)

Kurallar:
- Türkiye konserleri için her iki dil de Türkçe olabilir
- Kaynak bilgisi YAZMA
- "Yeni haber" veya benzeri giriş cümlesi YAZMA
- Direkt habere gir
- 15-18 hashtag ekle, metal/rock ile ilgili"""

    prompt = f"""Başlık: {news_item['title']}
Özet: {news_item['summary']}

Bu haberi Instagram caption formatında yaz."""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()
