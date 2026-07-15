"""
adults.uz — Telegram Bot API orqali mijozga xabar yuborish.

Bu murakkab bot-freymvork emas — shunchaki Telegram Bot API'ga to'g'ridan-to'g'ri
HTTP so'rov yuboradi. Buyurtma yaratilganda yoki holati o'zgarganda mijozga
avtomatik xabar boradi.

Muhit o'zgaruvchisi kerak:
    BOT_TOKEN — BotFather'dan olingan token (masalan: 8349217239:AAHo...)
"""

from __future__ import annotations

import os
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_telegram_message(telegram_id: int, text: str) -> bool:
    """
    Mijozga Telegram orqali xabar yuboradi. BOT_TOKEN sozlanmagan bo'lsa
    yoki mijoz botni hali /start qilmagan bo'lsa, jimgina False qaytaradi
    (xatolik chiqarmaydi — bu funksiya asosiy oqimni to'xtatmasligi kerak).
    """
    if not BOT_TOKEN or not telegram_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": telegram_id, "text": text, "parse_mode": "HTML"},
            )
            return res.status_code == 200
    except Exception:
        return False


ORDER_CONFIRMATION_TEMPLATE = (
    "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
    "Buyurtma raqami: <b>#{order_id}</b>\n"
    "Mahsulot: {product_name} × {quantity}\n"
    "Jami: <b>{total} so'm</b>\n\n"
    "Tez orada operator siz bilan bog'lanadi."
)

STATUS_UPDATE_TEMPLATES = {
    "paid": "💳 Buyurtma #{order_id} uchun to'lov tasdiqlandi.",
    "shipped": "🚚 Buyurtma #{order_id} yo'lga chiqdi! Tez orada yetkaziladi.",
    "delivered": "📦 Buyurtma #{order_id} yetkazib berildi. Xaridingiz uchun rahmat!",
    "cancelled": "❌ Buyurtma #{order_id} bekor qilindi. Savollar bo'lsa, operator bilan bog'laning.",
}
