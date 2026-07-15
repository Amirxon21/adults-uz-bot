"""
adults.uz — Telegram bot (/start buyrug'i va Web App tugmasi)

Bu alohida, uzluksiz ishlaydigan jarayon (process) — uni FastAPI serveridan
alohida, alohida terminalda ishga tushirasiz. Vazifasi: mijoz botga /start
yozganda salomlashish xabari va "Do'konni ochish" tugmasini ko'rsatish.

Eslatma: agar siz BotFather'da Menu Button orqali Web App'ni allaqachon
sozlagan bo'lsangiz, bu bot ixtiyoriy — lekin u yoqimli /start tajribasini
va kelajakda buyruqlar (masalan /orders) qo'shish imkonini beradi.

O'rnatish:
    pip install aiogram

Ishga tushirish (alohida terminalda, server va tunnel ishlab turganda):
    python bot.py
"""

from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adults_uz_bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SHOP_URL = os.getenv("SHOP_URL", "")  # masalan: https://xxxx.trycloudflare.com/shop

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida topilmadi. BotFather'dan olgan tokeningizni qo'ying.")
if not SHOP_URL:
    raise RuntimeError("SHOP_URL .env faylida topilmadi. Masalan: https://xxxx.trycloudflare.com/shop")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=SHOP_URL))]
    ])
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "<b>adults.uz</b> rasmiy botiga xush kelibsiz.\n"
        "Quyidagi tugma orqali katalogni ko'rib, buyurtma berishingiz mumkin.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@dp.message(F.text == "/help")
async def handle_help(message: Message):
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "/start — do'konni ochish\n"
        "Savollar bo'lsa, operator bilan bog'laning: +998 88 042 41 88",
        parse_mode="HTML",
    )


async def main():
    logger.info("Bot ishga tushdi. To'xtatish uchun Ctrl+C.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
