"""
adults.uz — Instagram DM integratsiyasi

Bu modul Instagram Business akkauntga kelgan DM xabarlarni qabul qilib,
AI orqali tahlil qiladi va agar mijoz mahsulot buyurtma qilmoqchi bo'lsa,
avtomatik ravishda bazaga buyurtma yozadi hamda mijozga javob yuboradi.

MUHIM — bu ishlashi uchun quyidagilar KERAK (faqat kod yozish yetarli emas):

1. Facebook Developer akkaunt (developers.facebook.com) va yangi "App" yaratish.
2. Instagram akkauntingiz "Business" yoki "Creator" turida bo'lishi va
   Facebook Page'ga ulangan bo'lishi kerak.
3. Facebook App'da "Instagram" mahsulotini qo'shish va Page'ni ulash.
4. Webhook manzilini ro'yxatdan o'tkazish:
   - Callback URL: https://sizning-domeningiz.com/webhook/instagram
   - Verify token: quyidagi INSTAGRAM_VERIFY_TOKEN bilan bir xil bo'lishi kerak
   - Subscribe qilinadigan field: "messages"
5. "instagram_business_basic", "instagram_business_manage_messages" kabi
   ruxsatlar uchun Meta App Review'dan o'tish kerak (agar production'da,
   o'zingizning shaxsiy akkauntingizdan tashqari odamlar yozadigan bo'lsa).
   Test rejimida (faqat siz va test foydalanuvchilar) review shart emas.
6. Page Access Token olib, INSTAGRAM_PAGE_ACCESS_TOKEN muhit o'zgaruvchisiga
   qo'yish kerak.

Muhit o'zgaruvchilari:
    INSTAGRAM_VERIFY_TOKEN       — o'zingiz o'ylab topgan maxfiy so'z (webhook tasdiqlash uchun)
    INSTAGRAM_PAGE_ACCESS_TOKEN  — Meta Developer konsolidan olinadigan token
"""

from __future__ import annotations

import os

import httpx

VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "adults_uz_verify")
PAGE_ACCESS_TOKEN = os.getenv("INSTAGRAM_PAGE_ACCESS_TOKEN", "")

GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"


def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    """
    Meta webhook manzilini birinchi marta ro'yxatdan o'tkazganda GET so'rov
    yuboradi — shu funksiya token to'g'riligini tekshiradi.
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge
    return None


async def send_instagram_message(recipient_id: str, text: str) -> None:
    """Instagram foydalanuvchisiga DM orqali javob yuboradi."""
    if not PAGE_ACCESS_TOKEN:
        raise RuntimeError(
            "INSTAGRAM_PAGE_ACCESS_TOKEN o'rnatilmagan — Meta Developer "
            "konsolidan Page Access Token oling."
        )

    async with httpx.AsyncClient() as client:
        await client.post(
            GRAPH_API_URL,
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text},
            },
            timeout=10.0,
        )


def extract_messages(webhook_body: dict) -> list[dict]:
    """
    Meta webhook payload'idan foydali xabarlarni ajratib oladi.
    Qaytaradi: [{"sender_id": str, "text": str}, ...]
    """
    messages = []
    for entry in webhook_body.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            text = event.get("message", {}).get("text")
            if sender_id and text:
                messages.append({"sender_id": sender_id, "text": text})
    return messages
