"""
adults.uz — Telegram Web App uchun REST API (FastAPI)

Bu fayl database.py dagi funksiyalarni HTTP endpoint sifatida ochadi,
shop.html va admin.html shu endpointlardan foydalanadi.

Ishga tushirish:
    pip install fastapi uvicorn sqlalchemy aiosqlite pydantic
    uvicorn api:app --reload --port 8000

Ishga tushgach:
    - API hujjatlari:  http://127.0.0.1:8000/docs
    - Do'kon (shop):   http://127.0.0.1:8000/shop
    - Admin panel:     http://127.0.0.1:8000/admin
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()  # .env faylidan ANTHROPIC_API_KEY va boshqalarni o'qiydi

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

# ---------------------------------------------------------------------------
# Loglash — hamma muhim voqealar (buyurtmalar, xatoliklar) app.log fayliga
# va terminalga yoziladi. Keyinchalik nima bo'lganini tekshirish uchun kerak.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("adults_uz")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import database as db
import ai
import instagram
import notify

app = FastAPI(title="adults.uz API")

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ---------------------------------------------------------------------------
# Admin autentifikatsiyasi (HTTP Basic Auth)
# .env faylida ADMIN_USERNAME va ADMIN_PASSWORD o'rnatilishi shart.
# ---------------------------------------------------------------------------
security = HTTPBasic()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Admin paroli sozlanmagan. .env fayliga ADMIN_PASSWORD qo'ying.",
        )
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Login yoki parol noto'g'ri",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# Web App/browser'dan so'rov yuborilishiga ruxsat beramiz.
# Productionda allow_origins ni aniq domenlar bilan cheklang.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
async def on_startup() -> None:
    await db.init_db()
    logger.info("Server ishga tushdi, baza tayyor.")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Kutilmagan xatoliklarni (masalan tarmoq uzilishi, kod xatosi) qamrab oladi.
    Foydalanuvchiga texnik traceback ko'rsatmasdan, tushunarli xabar qaytaradi,
    lekin to'liq xatolikni app.log fayliga yozadi (keyin tekshirish uchun).
    """
    logger.error(f"Kutilmagan xatolik: {request.method} {request.url.path} — {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Serverda kutilmagan xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."},
    )


# ---------------------------------------------------------------------------
# Pydantic sxemalari (request/response validatsiyasi)
# ---------------------------------------------------------------------------

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    size: Optional[str] = None
    color: Optional[str] = None
    stock: int
    image_url: Optional[str] = None
    category_id: Optional[int] = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    price: float
    size: Optional[str] = None
    color: Optional[str] = None
    stock: int = 0
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserIn(BaseModel):
    telegram_id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = 1


class OrderCreateIn(BaseModel):
    telegram_id: int
    full_name: Optional[str] = None
    items: list[OrderItemIn]


class ChatMessageIn(BaseModel):
    message: str
    history: Optional[list[dict]] = None


class ImageSearchIn(BaseModel):
    image_base64: str
    media_type: str = "image/jpeg"


class GenerateDescriptionIn(BaseModel):
    name: str
    category: str = ""
    color: str = ""
    size: str = ""


# ---------------------------------------------------------------------------
# Mahsulotlar (Product)
# ---------------------------------------------------------------------------

@app.get("/api/products", response_model=list[ProductOut])
async def api_list_products(
    category_id: Optional[int] = None,
    size: Optional[str] = None,
    color: Optional[str] = None,
    only_in_stock: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    """Katalog uchun mahsulotlar ro'yxati (filtrlar bilan)."""
    return await db.list_products(
        category_id=category_id,
        size=size,
        color=color,
        only_in_stock=only_in_stock,
        only_active=True,
        limit=limit,
        offset=offset,
    )


@app.get("/api/products/{product_id}", response_model=ProductOut)
async def api_get_product(product_id: int):
    product = await db.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    return product


@app.post("/api/products", response_model=ProductOut)
async def api_add_product(payload: ProductCreate, _: bool = Depends(verify_admin)):
    """Admin panel orqali yangi mahsulot qo'shish uchun."""
    return await db.add_product(**payload.model_dump())


@app.post("/api/upload-image")
async def api_upload_image(file: UploadFile = File(...), _: bool = Depends(verify_admin)):
    """
    Mahsulot rasmini serverga yuklaydi va ochiq URL qaytaradi.
    Admin panel: mahsulot qo'shishda shu URL keyin image_url sifatida saqlanadi.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Faqat JPEG, PNG, WEBP yoki GIF rasm yuklash mumkin")

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"

    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = UPLOADS_DIR / unique_name

    contents = await file.read()
    max_size = 8 * 1024 * 1024  # 8 MB
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="Rasm hajmi 8 MB dan oshmasligi kerak")

    with open(dest_path, "wb") as f:
        f.write(contents)

    logger.info(f"Rasm yuklandi: {unique_name} ({len(contents)} bayt)")
    return {"image_url": f"/static/uploads/{unique_name}"}


@app.post("/api/products/{product_id}/deactivate")
async def api_deactivate_product(product_id: int, _: bool = Depends(verify_admin)):
    await db.deactivate_product(product_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Kategoriyalar
# ---------------------------------------------------------------------------

@app.get("/api/categories", response_model=list[CategoryOut])
async def api_list_categories():
    return await db.list_categories()


@app.post("/api/categories", response_model=CategoryOut)
async def api_add_category(name: str, _: bool = Depends(verify_admin)):
    return await db.add_category(name)


# ---------------------------------------------------------------------------
# Foydalanuvchilar va buyurtmalar
# ---------------------------------------------------------------------------

@app.post("/api/users")
async def api_get_or_create_user(payload: UserIn):
    user = await db.get_or_create_user(
        telegram_id=payload.telegram_id,
        full_name=payload.full_name,
        phone=payload.phone,
    )
    return {"id": user.id, "telegram_id": user.telegram_id, "full_name": user.full_name}


@app.post("/api/orders")
async def api_create_order(payload: OrderCreateIn):
    """
    Bir nechta mahsulotdan iborat buyurtmani yaratadi.
    Avval foydalanuvchini topadi/yaratadi, so'ng har bir mahsulot uchun
    alohida Order yozuvi hosil qiladi (database.py struktura shunday).
    """
    user = await db.get_or_create_user(
        telegram_id=payload.telegram_id, full_name=payload.full_name
    )

    created_orders = []
    try:
        for item in payload.items:
            order = await db.create_order(
                user_id=user.id,
                product_id=item.product_id,
                quantity=item.quantity,
            )
            created_orders.append(order.id)
            logger.info(f"Yangi buyurtma: #{order.id} — user_id={user.id}, product_id={item.product_id}, qty={item.quantity}")

            product = await db.get_product(item.product_id)
            if user.telegram_id and product:
                text = notify.ORDER_CONFIRMATION_TEMPLATE.format(
                    order_id=order.id,
                    product_name=product.name,
                    quantity=item.quantity,
                    total=f"{order.total_price:,.0f}".replace(",", " "),
                )
                await notify.send_telegram_message(user.telegram_id, text)
    except ValueError as e:
        logger.warning(f"Buyurtma xatoligi: {e} — user_id={user.id}")
        raise HTTPException(status_code=400, detail=str(e))

    return {"order_ids": created_orders, "user_id": user.id}


@app.get("/api/orders/{telegram_id}")
async def api_get_user_orders(telegram_id: int):
    user = await db.get_or_create_user(telegram_id=telegram_id)
    orders = await db.get_user_orders(user.id)
    result = []
    for o in orders:
        product = await db.get_product(o.product_id)
        result.append({
            "id": o.id,
            "product_name": product.name if product else "—",
            "quantity": o.quantity,
            "total_price": float(o.total_price),
            "status": o.status.value,
            "created_at": o.created_at.isoformat(),
        })
    return result


# ---------------------------------------------------------------------------
# Admin statistikasi
# ---------------------------------------------------------------------------

@app.get("/api/admin/summary")
async def api_admin_summary(_: bool = Depends(verify_admin)):
    return await db.get_dashboard_summary()


@app.get("/api/admin/top-products")
async def api_admin_top_products(limit: int = 5, days: Optional[int] = 7, _: bool = Depends(verify_admin)):
    return await db.get_top_products(limit=limit, days=days)


@app.get("/api/admin/top-customers")
async def api_admin_top_customers(limit: int = 5, _: bool = Depends(verify_admin)):
    return await db.get_top_customers(limit=limit)


@app.get("/api/admin/inventory", response_model=list[ProductOut])
async def api_admin_inventory(_: bool = Depends(verify_admin)):
    return await db.get_inventory()


@app.get("/api/admin/orders")
async def api_admin_orders(limit: int = 200, _: bool = Depends(verify_admin)):
    return await db.get_all_orders(limit=limit)


@app.get("/api/admin/customers")
async def api_admin_customers(limit: int = 200, _: bool = Depends(verify_admin)):
    return await db.get_all_customers(limit=limit)


class OrderStatusIn(BaseModel):
    status: str  # "pending" | "paid" | "shipped" | "delivered" | "cancelled"


@app.post("/api/admin/orders/{order_id}/status")
async def api_admin_update_order_status(order_id: int, payload: OrderStatusIn, _: bool = Depends(verify_admin)):
    try:
        status_enum = db.OrderStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Noto'g'ri holat qiymati")
    order = await db.update_order_status(order_id, status_enum)
    if order is None:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    logger.info(f"Buyurtma holati yangilandi: #{order_id} -> {payload.status}")

    template = notify.STATUS_UPDATE_TEMPLATES.get(payload.status)
    if template:
        user = await db.get_user_by_id(order.user_id)
        if user and user.telegram_id:
            await notify.send_telegram_message(user.telegram_id, template.format(order_id=order_id))

    return {"ok": True}


# ---------------------------------------------------------------------------
# AI funksiyalari (Claude API)
# ---------------------------------------------------------------------------

async def _catalog_for_ai() -> list[dict]:
    """Barcha faol mahsulotlarni AI funksiyalari uchun soddalashtirilgan formatda qaytaradi."""
    categories = {c.id: c.name for c in await db.list_categories()}
    products = await db.list_products(only_in_stock=False, limit=200)
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "category": categories.get(p.category_id, ""),
            "color": p.color,
            "size": p.size,
            "stock": p.stock,
        }
        for p in products
    ]


@app.post("/api/ai/chat")
async def api_ai_chat(payload: ChatMessageIn):
    """AI-yordamchi chatbot: mijozning xabariga javob beradi va mahsulot tavsiya qiladi."""
    catalog = await _catalog_for_ai()
    try:
        result = ai.chat_recommend(payload.message, catalog, payload.history)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    products = []
    for pid in result.get("recommended_product_ids", []):
        p = await db.get_product(pid)
        if p:
            products.append(ProductOut.model_validate(p))
    return {"reply": result.get("reply", ""), "products": products}


@app.post("/api/ai/image-search")
async def api_ai_image_search(payload: ImageSearchIn):
    """Mijoz yuborgan rasm asosida katalogdan o'xshash mahsulotlarni topadi."""
    try:
        analysis = ai.analyze_clothing_image(payload.image_base64, payload.media_type)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    keywords = analysis.get("keywords", []) + [analysis.get("color", ""), analysis.get("category", "")]
    keywords = [k for k in keywords if k]
    products = await db.search_products_by_keywords(keywords)
    return {"analysis": analysis, "products": products}


@app.post("/api/ai/generate-description")
async def api_ai_generate_description(payload: GenerateDescriptionIn):
    """Admin panel uchun: mahsulot nomi/xususiyatlari asosida tavsif yozadi."""
    try:
        description = ai.generate_description(
            payload.name, payload.category, payload.color, payload.size
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"description": description}


# ---------------------------------------------------------------------------
# Instagram DM integratsiyasi
# ---------------------------------------------------------------------------

@app.get("/webhook/instagram")
async def instagram_verify(request: Request):
    """Meta webhook manzilni birinchi ro'yxatdan o'tkazganda chaqiradigan tekshiruv."""
    params = request.query_params
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")

    result = instagram.verify_webhook(mode, token, challenge)
    if result is None:
        raise HTTPException(status_code=403, detail="Verify token mos kelmadi")
    return int(result) if result.isdigit() else result


@app.post("/webhook/instagram")
async def instagram_receive(payload: dict):
    """
    Instagram'dan kelgan DM xabarlarni qabul qiladi:
    1. AI orqali xabarni tahlil qiladi (buyurtvormi, savolmi)
    2. Agar buyurtma bo'lsa — bazaga yozadi va qoldiqni kamaytiradi
    3. Mijozga DM orqali javob yuboradi
    """
    messages = instagram.extract_messages(payload)
    catalog = await _catalog_for_ai()

    for msg in messages:
        try:
            intent = ai.parse_order_intent(msg["text"], catalog)
        except RuntimeError:
            continue  # AI sozlanmagan bo'lsa, xabarni jimgina o'tkazib yuboramiz

        reply_text = intent.get("reply", "Rahmat, xabaringiz uchun!")

        if intent.get("intent") == "order" and intent.get("product_id"):
            user = await db.get_or_create_user_by_instagram(msg["sender_id"])
            try:
                order = await db.create_order(
                    user_id=user.id,
                    product_id=intent["product_id"],
                    quantity=intent.get("quantity", 1),
                )
                reply_text = f"✅ Buyurtmangiz qabul qilindi! Buyurtma raqami: #{order.id}. {reply_text}"
            except ValueError as e:
                reply_text = f"Kechirasiz, {e}"

        try:
            await instagram.send_instagram_message(msg["sender_id"], reply_text)
        except RuntimeError:
            pass  # Page token sozlanmagan bo'lsa ham xatolik chiqarmaymiz

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Frontend fayllarni xizmat qilish (shop.html / admin.html)
# ---------------------------------------------------------------------------

@app.get("/shop")
async def serve_shop():
    return FileResponse(BASE_DIR / "shop.html")


@app.get("/admin")
async def serve_admin(_: bool = Depends(verify_admin)):
    return FileResponse(BASE_DIR / "admin.html")


@app.get("/health")
async def health_check():
    """Deployment platformalari (Render, Railway) server tirikligini shu orqali tekshiradi."""
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "adults.uz API ishlayapti. /docs, /shop yoki /admin ga o'ting."}
