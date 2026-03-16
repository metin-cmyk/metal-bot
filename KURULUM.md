# Kurulum Rehberi — Adım Adım

## Sistemin çalışma mantığı

Sabah 10:00 ve akşam 19:00'da bot haberleri tarar.
Telefona Telegram mesajı gelir: görsel + caption + iki buton.
✅ Paylaş'a basarsan Instagram'a gider. ❌ Atla'ya basarsan geçer.

---

## 1. GitHub hesabı aç (2 dakika)

1. github.com'a git
2. "Sign up" → email + şifre + kullanıcı adı
3. Email onayını tamamla

---

## 2. Kodu GitHub'a yükle (3 dakika)

1. github.com'da sağ üst köşe → "+" → "New repository"
2. İsim: `metal-bot` → "Create repository"
3. "uploading an existing file" linkine tıkla
4. Bu klasördeki tüm dosyaları sürükle bırak
5. "Commit changes" butonuna bas

---

## 3. Telegram botu aç (3 dakika)

1. Telegram'da @BotFather'ı aç
2. `/newbot` yaz
3. Bot için bir isim ver (örn: MetalHaberBot)
4. Sana bir TOKEN verecek → kopyala, bir yere not et

Kendi chat ID'ni öğrenmek için:
1. @userinfobot'a Telegram'dan mesaj at
2. Sana "Your ID: 123456789" diyecek → bunu da not et

---

## 4. API key'leri topla

Bunları bir yere not et, hepsini Railway'e gireceksin:

| Değişken | Nereden alınır |
|---|---|
| ANTHROPIC_API_KEY | console.anthropic.com → API Keys |
| TELEGRAM_TOKEN | @BotFather'dan aldığın token |
| TELEGRAM_CHAT_ID | @userinfobot'tan aldığın numara |
| IG_USER_ID | Instagram ayarlar → hesap bilgileri → meta hesap ID |
| IG_ACCESS_TOKEN | developers.facebook.com (aşağıda anlatıldı) |
| IMGBB_API_KEY | api.imgbb.com → ücretsiz kayıt → API key |
| IG_HANDLE | @senin_instagram_kullanici_adin |

### Instagram token almak (en uzun adım, 10 dk)

1. Instagram hesabını Business/Creator yap:
   Ayarlar → Hesap → Profesyonel hesaba geç

2. developers.facebook.com'a git → "My Apps" → "Create App"

3. "Business" seç → app'e "Instagram Graph API" ekle

4. Token oluştur ve bu komutla uzun ömürlüye çevir:
   (TOKEN kısmına kendi token'ını yaz)

```
https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=APP_SECRET&access_token=TOKEN
```

5. Hesap ID için tarayıcıda şunu aç:
```
https://graph.instagram.com/me?fields=id,username&access_token=TOKEN
```

---

## 5. Railway'e deploy et (5 dakika)

1. railway.app'e git → "Start a New Project"
2. "Deploy from GitHub repo" → metal-bot'u seç
3. Sol menü → "Variables" → her satır için "Add Variable":

```
ANTHROPIC_API_KEY  = sk-ant-xxx
TELEGRAM_TOKEN     = 123456:ABCxxx
TELEGRAM_CHAT_ID   = 123456789
IG_USER_ID         = 123456789
IG_ACCESS_TOKEN    = EAAxxxxx
IMGBB_API_KEY      = xxxxxxxx
IG_HANDLE          = @hesabin
```

4. "Deploy" butonuna bas
5. Bitti! Artık 7/24 çalışıyor.

---

## 6. Test et

Railway'de Variables'a git, şunu ekle:
```
RUN_NOW = true
```
Kaydet → Railway yeniden başlatır → Telegram'a hemen bir haber gelir.
Test bittikten sonra RUN_NOW'u sil ya da `false` yap.

---

## Hatırlatıcı

Instagram token 60 günde bir yenilenmeli!
Telefon takvimine 55. güne hatırlatıcı ekle.

Token yenileme linki (tarayıcıda aç):
```
https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=SENIN_TOKENIN
```
Sonra Railway'de IG_ACCESS_TOKEN değerini güncelle.
