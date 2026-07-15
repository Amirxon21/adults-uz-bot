"""
adults.uz — AI funksiyalari (Claude API orqali)

Bu modul uchta AI funksiyani ta'minlaydi:
  1. chat_recommend()       — mijoz bilan suhbat, katalogdan mahsulot tavsiya qilish
  2. analyze_clothing_image() — mijoz yuborgan rasmni tahlil qilib, qidiruv
                                 kalit so'zlarini chiqarish (rasm orqali qidiruv)
  3. generate_description() — admin uchun mahsulot tavsifini avtomatik yozish
  4. parse_order_intent()   — Instagram DM matnidan buyurtma niyatini aniqlash

O'rnatish:
    pip install anthropic

Muhim: ANTHROPIC_API_KEY muhit o'zgaruvchisini albatta o'rnating:
    Windows (PowerShell):  $env:ANTHROPIC_API_KEY="sk-ant-..."
    Linux/Mac:             export ANTHROPIC_API_KEY="sk-ant-..."
API kalitni https://console.anthropic.com dan olasiz.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import anthropic

MODEL = "claude-sonnet-4-5"  # muvozanatli tezlik/sifat uchun

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY muhit o'zgaruvchisi topilmadi. "
                "console.anthropic.com dan kalit oling va uni sozlang."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _extract_json(text: str) -> dict:
    """Modeldan qaytgan matndan JSON qismini xavfsiz ajratib oladi."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Modeldan JSON formatida javob kelmadi")
    return json.loads(text[start:end + 1])


# ---------------------------------------------------------------------------
# 1. Chatbot — mahsulot tavsiya qilish
# ---------------------------------------------------------------------------

def chat_recommend(message: str, catalog: list[dict], history: Optional[list[dict]] = None) -> dict:
    """
    Mijozning xabariga javob beradi va agar mos kelsa, katalogdan mahsulot(lar)
    tavsiya qiladi.

    catalog: [{"id":1, "name":"...", "price":99000, "category":"Futbolka",
               "color":"Qora", "size":"L", "stock":10}, ...]
    history: oldingi xabarlar [{"role":"user"/"assistant", "content":"..."}]

    Qaytaradi: {"reply": str, "recommended_product_ids": [int, ...]}
    """
    client = _get_client()
    history = history or []

    catalog_text = "\n".join(
        f"- id={p['id']}: {p['name']} | {p.get('category','')} | "
        f"rang: {p.get('color','—')} | o'lcham: {p.get('size','—')} | "
        f"narx: {p['price']} so'm | qoldiq: {p['stock']}"
        for p in catalog
    )

    system_prompt = f"""Sen "adults.uz" kiyim-kechak do'konining AI-yordamchisisan.
Vazifang — mijozga do'stona, qisqa va foydali javob berish, imkon qadar
quyidagi katalogdan mos mahsulot(lar)ni tavsiya qilish.

QOIDALAR:
- Faqat quyidagi katalogda mavjud mahsulotlarni tavsiya qil, hech qachon
  o'ylab topma yoki katalogdan tashqari mahsulot aytma.
- Agar qoldiq (stock) 0 bo'lsa, o'sha mahsulotni tavsiya qilma.
- Javobing o'zbek tilida, qisqa (2-4 gap) va samimiy bo'lsin.
- Har doim JAVOBNI FAQAT quyidagi JSON formatida qaytar, boshqa hech narsa yozma:

{{"reply": "mijozga javob matni", "recommended_product_ids": [id1, id2]}}

Agar tavsiya qilishga mos mahsulot topilmasa, recommended_product_ids ni bo'sh
massiv [] qilib qoldir.

KATALOG:
{catalog_text}
"""

    messages = history + [{"role": "user", "content": message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=messages,
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    try:
        return _extract_json(text)
    except (ValueError, json.JSONDecodeError):
        # Modeldan JSON kelmasa ham, mijoz javobsiz qolmasligi uchun zaxira
        return {"reply": text.strip() or "Kechirasiz, javob bera olmadim.", "recommended_product_ids": []}


# ---------------------------------------------------------------------------
# 2. Rasm orqali qidiruv
# ---------------------------------------------------------------------------

def analyze_clothing_image(image_base64: str, media_type: str = "image/jpeg") -> dict:
    """
    Mijoz yuborgan kiyim rasmini tahlil qiladi va qidiruv uchun kalit
    so'zlarni chiqaradi (kategoriya, rang, uslub).

    Qaytaradi: {"category": str, "color": str, "keywords": [str, ...], "description": str}
    """
    client = _get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_base64},
                },
                {
                    "type": "text",
                    "text": (
                        "Bu rasmda qanday kiyim bor? Faqat quyidagi JSON formatida "
                        "javob ber, boshqa hech narsa yozma:\n"
                        '{"category": "Futbolka/Ko\'ylak/Shim/Kurtka/Aksessuar dan biri", '
                        '"color": "asosiy rang (o\'zbekcha)", '
                        '"keywords": ["qidiruv uchun 3-5 ta kalit so\'z, o\'zbekcha"], '
                        '"description": "1 gapli tavsif"}'
                    ),
                },
            ],
        }],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    try:
        return _extract_json(text)
    except (ValueError, json.JSONDecodeError):
        return {"category": "", "color": "", "keywords": [], "description": "Rasmni tahlil qilib bo'lmadi"}


# ---------------------------------------------------------------------------
# 3. Admin uchun avtomatik mahsulot tavsifi
# ---------------------------------------------------------------------------

def generate_description(name: str, category: str = "", color: str = "", size: str = "") -> str:
    """Admin panel uchun: mahsulot nomi/xususiyatlari asosida sotuvni oshiruvchi tavsif yozadi."""
    client = _get_client()

    prompt = f"""Quyidagi kiyim mahsuloti uchun jozibali, qisqa (1-2 gap) sotuv
tavsifini o'zbek tilida yoz. Haqiqiy bo'lmagan xususiyatlarni (masalan
"organik paxta" kabi tekshirilmagan da'volarni) qo'shma — faqat berilgan
ma'lumotlarga tayan va umumiy jozibali uslubda yoz.

Mahsulot: {name}
Kategoriya: {category or "—"}
Rang: {color or "—"}
O'lcham: {size or "—"}

Faqat tavsif matnini yoz, boshqa hech narsa qo'shma."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


# ---------------------------------------------------------------------------
# 4. Instagram DM — buyurtma niyatini aniqlash
# ---------------------------------------------------------------------------

def parse_order_intent(message: str, catalog: list[dict]) -> dict:
    """
    Instagram DM matnidan mijoz nima demoqchi ekanini aniqlaydi:
    oddiy savol/salom, yoki aniq mahsulot buyurtma qilish niyati.

    Qaytaradi: {
      "intent": "order" | "question" | "greeting",
      "product_id": int | None,
      "quantity": int,
      "reply": str
    }
    """
    client = _get_client()

    catalog_text = "\n".join(
        f"- id={p['id']}: {p['name']} ({p.get('color','')}, {p.get('size','')}) "
        f"- {p['price']} so'm, qoldiq: {p['stock']}"
        for p in catalog
    )

    system_prompt = f"""Sen "adults.uz" kiyim-kechak do'konining Instagram DM
yordamchisisan. Mijozning xabarini tahlil qil va aniq JSON formatida javob ber:

{{"intent": "order" yoki "question" yoki "greeting",
  "product_id": mos mahsulot id raqami yoki null,
  "quantity": nechta dona (agar aytilmagan bo'lsa 1),
  "reply": "mijozga DM orqali yuboriladigan qisqa, samimiy javob (o'zbek tilida)"}}

Qoidalar:
- Agar mijoz aniq mahsulot nomini yoki unga o'xshash narsani so'rasa va
  katalogda mos narsa bo'lsa, intent="order" va mos product_id ni qo'y.
- Agar mahsulot omborda yo'q (qoldiq 0) bo'lsa, intent="question" qil va
  reply'da buni tushuntir, muqobil taklif qil.
- Agar shunchaki salomlashish yoki umumiy savol bo'lsa, intent="greeting"
  yoki "question", product_id=null.
- Faqat JSON qaytar, boshqa matn yozma.

KATALOG:
{catalog_text}
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": message}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    try:
        return _extract_json(text)
    except (ValueError, json.JSONDecodeError):
        return {
            "intent": "question",
            "product_id": None,
            "quantity": 1,
            "reply": "Kechirasiz, so'rovingizni tushunmadim. Iltimos, mahsulot nomini aniqroq yozing.",
        }
