# adults.uz — Professional darajaga keltirish: to'liq hisobot

## ✅ HOZIR QO'SHILDI (kod tomondan tayyor)

| # | Nima | Fayl |
|---|---|---|
| 1 | **Telegram bildirishnomalari** — buyurtma berilganda va holat o'zgarganda mijozga avtomatik xabar boradi | `notify.py`, `api.py` |
| 2 | **Haqiqiy bot (/start)** — Web App tugmasi bilan chiroyli salomlashish | `bot.py` |
| 3 | **Admin panel paroli** — endi `/admin` login-parolsiz ochilmaydi | `api.py` (HTTP Basic Auth) |
| 4 | **Mahsulot rasmlarini yuklash** — emoji o'rniga haqiqiy rasm | `api.py`, `admin.html`, `shop.html` |
| 5 | **To'liq ishlaydigan admin sahifalar** — Ombor, Buyurtmalar (holat o'zgartirish bilan), Mijozlar, Katalog | `admin.html` |
| 6 | **Loglash** — barcha muhim voqealar `app.log` fayliga yoziladi | `api.py` |
| 7 | **Xatolarni tutish** — kutilmagan xatolik foydalanuvchiga texnik matn ko'rsatmaydi | `api.py` |
| 8 | **Avtomatik testlar** — asosiy funksiyalar tekshiriladi | `test_database.py` |
| 9 | **Zaxira nusxa skripti** — bazani yo'qotmaslik uchun | `backup.py` |
| 10 | **Health-check** — hosting platformalari server tirikligini tekshiradi | `/health` endpoint |
| 11 | **Docker/Procfile** — istalgan hostingga bir zumda joylash uchun | `Dockerfile`, `Procfile` |
| 12 | **AI chatbot, rasm-qidiruv, tavsif generatori** | `ai.py` |
| 13 | **Instagram DM integratsiyasi** (kod tayyor) | `instagram.py` |

## 🔧 SIZ QILISHINGIZ KERAK (kod bilan hal bo'lmaydigan narsalar)

Bular — **texnik emas, tashkiliy/biznes** qadamlar. Men buni siz o'rniga bajara olmayman, chunki bularning barchasi sizning shaxsiy hisobingiz, hujjatlaringiz yoki shartnomangizni talab qiladi:

### 1. Doimiy hosting (BUGUNGI eng muhim keyingi qadam)
Hozir sizning bot **faqat kompyuteringiz ochiq va ikkita terminal ishlab turgandagina** ishlaydi. Bu jiddiy cheklov.

**Nima qilish kerak:**
- https://render.com yoki https://railway.app da bepul akkaunt oching
- GitHub'ga loyihangizni yuklang (repository yarating)
- Render/Railway'da "New Web Service" → GitHub repo'ni ulang → avtomatik `Dockerfile`ni aniqlab, deploy qiladi
- Natijada doimiy manzil olasiz (masalan `https://adults-uz.onrender.com`) — bu **hech qachon o'zgarmaydi**, cloudflared shart emas bo'lib qoladi

Xohlasangiz, shu qadamni birga, ekran-baekran qilib bera olaman — alohida so'rang.

### 2. Domen nomi (ixtiyoriy, lekin professional ko'rinish uchun)
`adults.uz` domenini sotib olish (agar hali sizniki bo'lmasa) — bu Namecheap, REG.RU yoki O'zbekiston domen ro'yxatga oluvchilari orqali qilinadi. Keyin hostingga ulanadi.

### 3. To'lov tizimi (Click/Payme)
Hozir buyurtma "band qilish" tarzida ishlaydi (naqd pul yoki keyinroq to'lov). Onlayn to'lovni ulash uchun:
- **Click** yoki **Payme**da tadbirkor sifatida ro'yxatdan o'ting (https://click.uz yoki https://payme.uz — biznes bo'limi)
- Ular sizga **Merchant ID** va **Secret Key** beradi
- Shu kalitlar bilan men ularning API'sini `api.py`ga ulab beraman (bu qism texnik, keyin qila olaman — lekin kalitlarni faqat siz, ro'yxatdan o'tib, ololasiz)

### 4. Instagram App Review (agar ko'p odam yozadigan bo'lsa)
`instagram.py` tayyor, lekin Meta'dan ruxsat olish — alohida jarayon (README.md'da batafsil yozilgan edi).

### 5. Yuridik/biznes tomon
- Yetkazib berish shartlari, qaytarish siyosati (matn sifatida — buni birga yozib bera olaman)
- Agar rasmiy tadbirkor sifatida ishlasangiz — soliq/patent masalalari (bu texnik emas, buxgalteriya masalasi)

## 💡 Kelajakda qo'shsa bo'ladigan narsalar (ixtiyoriy, hoziroq shart emas)

- Ko'p tilli interfeys (o'zbek/rus/ingliz)
- Chegirma/promo-kod tizimi
- Mahsulotlarga mijoz sharhlari va reyting
- SMS orqali bildirishnoma (agar mijoz Telegram botni to'xtatgan bo'lsa)
- Ko'proq to'lov usullari (bank kartasi orqali to'g'ridan-to'g'ri)

---

## Yangi fayllarni ishga tushirish

### `.env` faylini to'ldiring
```
BOT_TOKEN=<BotFather'dan olgan tokeningiz>
SHOP_URL=<hozirgi cloudflared manzilingiz>/shop
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<o'zingiz o'ylab toping, kuchli parol>
```

⚠️ **`ADMIN_PASSWORD`ni albatta to'ldiring** — bo'sh qolsa, `/admin` sahifasi butunlay ishlamay qoladi (xavfsizlik uchun ataylab shunday qilingan).

### Kutubxonalarni yangilang
```powershell
pip install -r requirements.txt
```

### Botni ishga tushiring (ixtiyoriy, /start uchun)
Yangi, to'rtinchi terminalda:
```powershell
python bot.py
```

### Admin panelga kirish
`/admin`ni ochganda brauzer login-parol so'raydi — `.env`dagi `ADMIN_USERNAME`/`ADMIN_PASSWORD`ni kiriting.
