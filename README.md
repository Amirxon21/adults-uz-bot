# adults.uz — ishga tushirish qo'llanmasi

## 1. Kutubxonalarni o'rnatish

Loyiha papkasida, venv faollashtirilgan holda:

```powershell
pip install -r requirements.txt
```

## 2. Bazani demo ma'lumotlar bilan to'ldirish (faqat birinchi marta)

```powershell
python seed.py
```

Bu kategoriyalarni (Futbolka, Ko'ylak, Shim, Kurtka, Aksessuar) va har biriga
bir nechta mahsulotni bazaga (`shop.db`) qo'shadi.

⚠️ Agar keyinroq qayta ishga tushirsangiz, ikki marta bir xil mahsulotlar
qo'shilib ketadi — bazani tozalash uchun `shop.db` faylini o'chirib, `seed.py`ni
qayta ishga tushiring.

## 3. Serverni ishga tushirish

```powershell
uvicorn api:app --reload --port 8000
```

Terminalda shunga o'xshash chiqishi kerak:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## 4. Tekshirish

Brauzerda oching:

| Manzil | Nima uchun |
|---|---|
| http://127.0.0.1:8000/shop | Mijozlar uchun do'kon (Telegram Web App) |
| http://127.0.0.1:8000/admin | Admin panel (statistika, ombor) |
| http://127.0.0.1:8000/docs | Barcha API endpointlarning interaktiv hujjati |

`/shop` sahifasida katalogni ko'rishingiz, savatga mahsulot qo'shishingiz va
"Buyurtma berish" tugmasini bosishingiz mumkin — bu haqiqatan ham `shop.db`
bazasiga yoziladi. Keyin `/admin` sahifasini yangilasangiz, statistika
o'zgarganini ko'rasiz.

## 5. Telegram botga ulash (keyingi bosqich)

Hozircha bu — mustaqil web-server. Uni haqiqiy Telegram Web App qilish uchun:

1. Serverni internetga ochiq joyga joylashtirish kerak (masalan VPS, Render,
   Railway) — chunki Telegram HTTPS manzilga muhtoj.
2. BotFather'da botingizga: `/setmenubutton` yoki `/newapp` orqali
   `https://sizning-domeningiz/shop` manzilini ulaysiz.
3. Admin panelni (`/admin`) parol bilan himoyalash kerak bo'ladi — hozircha
   himoyasiz, faqat lokal test uchun.

Agar shu bosqichga o'tishni xohlasangiz (deploy qilish, HTTPS, admin panelga
parol qo'shish), ayting — birga qilamiz.

## 6. AI funksiyalarini sozlash (chatbot, rasm qidiruv, tavsif generatori)

Uchala AI funksiya ham Claude API orqali ishlaydi (`ai.py`). Sozlash:

1. https://console.anthropic.com saytiga kiring, API kalit yarating.
2. Muhit o'zgaruvchisiga qo'ying:

   **Windows PowerShell:**
   ```powershell
   $env:ANTHROPIC_API_KEY="sk-ant-..."
   ```
   (Bu faqat joriy terminal sessiyasi uchun ishlaydi. Doimiy qilish uchun
   Windows'da "Environment Variables" orqali tizim darajasida qo'shing.)

3. Serverni qayta ishga tushiring:
   ```powershell
   uvicorn api:app --reload --port 8000
   ```

Endi `/shop` sahifasidagi **🤖 AI** bo'limi va 📷 rasm qidiruv tugmasi, hamda
`/admin` sahifasidagi **✨ AI yozsin** tugmasi ishlaydi.

⚠️ Claude API pullik xizmat — har bir so'rov uchun kichik summa yechiladi.
Narxlar: https://www.anthropic.com/pricing

## 7. Instagram DM integratsiyasini sozlash

Bu eng murakkab qism — kod tayyor, lekin ishlashi uchun Meta (Facebook)
tomonida ham sozlash kerak:

### A) Meta Developer akkaunt tayyorlash
1. https://developers.facebook.com ga kiring, yangi **App** yarating (turi:
   "Business").
2. App ichida **Instagram** mahsulotini qo'shing.
3. Instagram akkauningiz **Business** yoki **Creator** turida bo'lishi va
   Facebook Page'ga ulangan bo'lishi shart (agar bo'lmasa, Instagram
   ilovasida Sozlamalar → Akkaunt turi orqali o'zgartiring).
4. App sozlamalarida Instagram akkauntingizni ulang.

### B) Webhook sozlash
1. Serveringiz internetga ochiq bo'lishi kerak (HTTPS bilan).
2. Meta App → Webhooks bo'limida:
   - Callback URL: `https://sizning-domeningiz.com/webhook/instagram`
   - Verify Token: o'zingiz o'ylab topgan so'z (masalan `mening_maxfiy_sozim`)
   - Subscribe qilinadigan field: **messages**
3. Shu tokenni muhit o'zgaruvchisiga qo'ying:
   ```powershell
   $env:INSTAGRAM_VERIFY_TOKEN="mening_maxfiy_sozim"
   ```

### C) Page Access Token olish
1. Meta App → Instagram → **Generate Token** orqali Page Access Token oling.
2. Muhit o'zgaruvchisiga qo'ying:
   ```powershell
   $env:INSTAGRAM_PAGE_ACCESS_TOKEN="EAAxxxxx..."
   ```

### D) App Review (production uchun)
- Agar faqat siz test qilsangiz — "Test mode"da ishlaydi, review shart emas.
- Agar boshqa odamlar ham DM yozadigan bo'lsa (haqiqiy mijozlar), Meta'dan
  `instagram_business_manage_messages` ruxsati uchun **App Review**'dan
  o'tish kerak bo'ladi — bu Meta tomonidan tekshiriladigan alohida jarayon
  (odatda bir necha kun davom etadi, video-namoyish talab qilinadi).

Bu qism sozlanmagan bo'lsa ham, qolgan hamma narsa (shop, admin, AI chat,
rasm qidiruv) normal ishlayveradi — Instagram faqat alohida qo'shimcha.

## Muammolarni bartaraf etish

| Xatolik | Yechim |
|---|---|
| `ModuleNotFoundError` | `pip install -r requirements.txt` ni qayta bajaring, venv faolligini tekshiring |
| `/shop` sahifasi bo'sh yoki xato beradi | Terminaldagi server loglarini tekshiring; `seed.py` ishga tushirilganini tasdiqlang |
| Admin panelda "Ma'lumot yuklanmadi" | Server ishlab turganini va portlar mos kelishini (8000) tekshiring |
| CORS xatoligi (agar shop.html'ni alohida ochsangiz) | `shop.html`/`admin.html` ichidagi `API_BASE` o'zgaruvchisini `http://127.0.0.1:8000` ga o'zgartiring |
