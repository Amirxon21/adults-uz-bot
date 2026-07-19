"""
adults.uz — Telegram Web App bot uchun ma'lumotlar bazasi moduli.

Texnologiya: SQLAlchemy 2.0 (async ORM)
Standart holatda SQLite ishlatiladi (fayl: shop.db), lekin DATABASE_URL
o'zgaruvchisini o'zgartirib PostgreSQL'ga osongina o'tish mumkin, masalan:
    postgresql+asyncpg://user:password@localhost:5432/adults_uz

O'rnatish:
    pip install sqlalchemy aiosqlite
    # Postgres uchun qo'shimcha: pip install asyncpg
"""

from __future__ import annotations

import enum
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    select,
    text,
    update as sa_update,
)
logger = logging.getLogger("adults_uz")
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ---------------------------------------------------------------------------
# Ulanish sozlamalari
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///shop.db")

# Neon/Supabase/Render kabi provayderlar odatda "postgres://" yoki "postgresql://"
# ko'rinishidagi manzil beradi. SQLAlchemy'ning async drayveri (asyncpg) ishlashi uchun
# buni "postgresql+asyncpg://" formatiga avtomatik o'tkazamiz.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Ko'p provayderlar (Neon, Supabase) manzilga "?sslmode=require&channel_binding=require"
# kabi bir nechta parametr qo'shadi, lekin asyncpg buларни to'g'ridan-to'g'ri tushunmaydi.
# Shuning uchun URL'ni to'g'ri (urllib orqali) tahlil qilib, bu parametrlarni ajratib
# olamiz va asyncpg'ga mos "connect_args" sifatida beramiz — oddiy matn almashtirish
# (string replace) turli provayderlarning parametr tartibida xato qilishi mumkin edi.
connect_args = {}
if DATABASE_URL.startswith("postgresql+asyncpg"):
    from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode

    parts = urlsplit(DATABASE_URL)
    query_params = parse_qs(parts.query)

    if query_params.pop("sslmode", None):
        connect_args["ssl"] = True
    query_params.pop("channel_binding", None)  # asyncpg buni qo'llab-quvvatlamaydi

    new_query = urlencode(query_params, doseq=True)
    DATABASE_URL = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Modellar
# ---------------------------------------------------------------------------

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    size: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # S, M, L, XL...
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    """
    Mahsulotning asosiy rasmidan (Product.image_url) tashqari qo'shimcha
    rasmlari — galereya sifatida ko'rsatish uchun.
    """
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="images")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    instagram_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Bazani yaratish
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Jadvallarni (agar mavjud bo'lmasa) yaratadi. Botni ishga tushirishda bir marta chaqiring."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_lightweight_migrations(conn)


async def _run_lightweight_migrations(conn) -> None:
    """
    SQLAlchemy'ning create_all() funksiyasi FAQAT yangi jadval yaratadi —
    mavjud jadvalga yangi ustun qo'shmaydi (bu "migratsiya" deb ataladi).
    Loyiha rivojlanishi davomida modelga yangi maydonlar qo'shilganda
    (masalan username, photo_url), ularni mavjud bazaga shu yerda,
    xavfsiz tarzda qo'shamiz. Faqat PostgreSQL uchun ishlaydi (Neon/Render);
    SQLite bilan ishlaganda (lokal test) sokin o'tkazib yuboriladi.
    """
    if engine.dialect.name != "postgresql":
        return

    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url VARCHAR(500)",
    ]
    for statement in migrations:
        try:
            await conn.execute(text(statement))
        except Exception as e:
            logger.warning(f"Migratsiya bajarilmadi ({statement}): {e}")


# ---------------------------------------------------------------------------
# Mahsulotlar (Product) bilan ishlash funksiyalari
# ---------------------------------------------------------------------------

async def add_product(
    name: str,
    price: float,
    size: Optional[str] = None,
    color: Optional[str] = None,
    stock: int = 0,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    category_id: Optional[int] = None,
) -> Product:
    """Yangi kiyim mahsulotini bazaga qo'shadi."""
    async with async_session() as session:
        product = Product(
            name=name,
            price=price,
            size=size,
            color=color,
            stock=stock,
            description=description,
            image_url=image_url,
            category_id=category_id,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


async def get_product(product_id: int) -> Optional[Product]:
    """ID bo'yicha bitta mahsulotni qaytaradi."""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()


async def list_products(
    category_id: Optional[int] = None,
    size: Optional[str] = None,
    color: Optional[str] = None,
    only_in_stock: bool = True,
    only_active: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[Product]:
    """
    Filtrlar asosida mahsulotlar ro'yxatini qaytaradi.
    Telegram Web App'dagi katalog/filtr sahifasi uchun mos.
    """
    async with async_session() as session:
        query = select(Product)

        if only_active:
            query = query.where(Product.is_active.is_(True))
        if only_in_stock:
            query = query.where(Product.stock > 0)
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if size is not None:
            query = query.where(Product.size == size)
        if color is not None:
            query = query.where(Product.color == color)

        query = query.order_by(Product.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        return result.scalars().all()


async def update_stock(product_id: int, quantity_change: int) -> Optional[Product]:
    """
    Mahsulot qoldig'ini o'zgartiradi (buyurtma qilinganda manfiy, qaytarilganda musbat).
    Qoldiq 0 dan pastga tushmasligini tekshiradi.
    """
    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is None:
            return None

        new_stock = product.stock + quantity_change
        if new_stock < 0:
            raise ValueError(
                f"Yetarli qoldiq yo'q: mavjud={product.stock}, so'ralgan={-quantity_change}"
            )

        product.stock = new_stock
        await session.commit()
        await session.refresh(product)
        return product


async def add_product_image(product_id: int, url: str) -> ProductImage:
    """Mahsulotga qo'shimcha rasm (galereya) qo'shadi."""
    async with async_session() as session:
        result = await session.execute(
            select(func.coalesce(func.max(ProductImage.position), -1)).where(
                ProductImage.product_id == product_id
            )
        )
        next_position = result.scalar_one() + 1

        image = ProductImage(product_id=product_id, url=url, position=next_position)
        session.add(image)
        await session.commit()
        await session.refresh(image)
        return image


async def list_product_images(product_id: int) -> Sequence[ProductImage]:
    """Mahsulotning barcha qo'shimcha rasmlarini tartib bo'yicha qaytaradi."""
    async with async_session() as session:
        result = await session.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.position)
        )
        return result.scalars().all()


async def delete_product_image(image_id: int) -> None:
    """Galereyadan bitta rasmni o'chiradi."""
    async with async_session() as session:
        image = await session.get(ProductImage, image_id)
        if image is not None:
            await session.delete(image)
            await session.commit()


async def update_product(
    product_id: int,
    name: Optional[str] = None,
    price: Optional[float] = None,
    size: Optional[str] = None,
    color: Optional[str] = None,
    stock: Optional[int] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    category_id: Optional[int] = None,
) -> Optional[Product]:
    """
    Mavjud mahsulotning maydonlarini yangilaydi. Faqat berilgan (None bo'lmagan)
    maydonlar o'zgartiriladi — qolganlari o'z holicha qoladi.
    """
    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is None:
            return None

        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        if size is not None:
            product.size = size
        if color is not None:
            product.color = color
        if stock is not None:
            product.stock = stock
        if description is not None:
            product.description = description
        if image_url is not None:
            product.image_url = image_url
        if category_id is not None:
            product.category_id = category_id

        await session.commit()
        await session.refresh(product)
        return product


async def deactivate_product(product_id: int) -> None:
    """Mahsulotni o'chirmasdan, faqat faol emas deb belgilaydi (soft delete)."""
    async with async_session() as session:
        await session.execute(
            sa_update(Product)
            .where(Product.id == product_id)
            .values(is_active=False)
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Foydalanuvchilar (User)
# ---------------------------------------------------------------------------

async def get_or_create_user(
    telegram_id: int,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    username: Optional[str] = None,
    photo_url: Optional[str] = None,
) -> User:
    """
    Telegram ID bo'yicha foydalanuvchini topadi yoki yangi yaratadi.
    Agar foydalanuvchi allaqachon mavjud bo'lsa-yu, Telegram profili
    (ism, username, rasm) o'zgargan bo'lsa, shu yerda yangilanadi.
    """
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is not None:
            changed = False
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if username and user.username != username:
                user.username = username
                changed = True
            if photo_url and user.photo_url != photo_url:
                user.photo_url = photo_url
                changed = True
            if changed:
                await session.commit()
                await session.refresh(user)
            return user

        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            phone=phone,
            username=username,
            photo_url=photo_url,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_or_create_user_by_instagram(
    instagram_id: str,
    full_name: Optional[str] = None,
) -> User:
    """Instagram foydalanuvchi ID'si (sender id) bo'yicha foydalanuvchini topadi yoki yaratadi."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.instagram_id == instagram_id)
        )
        user = result.scalar_one_or_none()
        if user is not None:
            return user

        user = User(instagram_id=instagram_id, full_name=full_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# ---------------------------------------------------------------------------
# Buyurtmalar (Order)
# ---------------------------------------------------------------------------

async def create_order(user_id: int, product_id: int, quantity: int = 1) -> Order:
    """
    Yangi buyurtma yaratadi va mahsulot qoldig'ini avtomatik kamaytiradi.
    Bitta tranzaksiya ichida bajariladi — xatolik bo'lsa hech narsa saqlanmaydi.
    """
    async with async_session() as session:
        async with session.begin():
            product = await session.get(Product, product_id)
            if product is None:
                raise ValueError("Mahsulot topilmadi")
            if product.stock < quantity:
                raise ValueError(
                    f"Yetarli qoldiq yo'q: mavjud={product.stock}, so'ralgan={quantity}"
                )

            product.stock -= quantity
            total_price = float(product.price) * quantity

            order = Order(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                total_price=total_price,
                status=OrderStatus.PENDING,
            )
            session.add(order)

        await session.refresh(order)
        return order


async def get_user_orders(user_id: int, limit: int = 20) -> Sequence[Order]:
    """Foydalanuvchining buyurtmalar tarixini qaytaradi (eng yangisi birinchi)."""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_order(order_id: int) -> Optional[Order]:
    """ID bo'yicha bitta buyurtmani qaytaradi (bildirishnoma yuborish uchun kerak)."""
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: int) -> Optional[User]:
    """ID bo'yicha foydalanuvchini qaytaradi (bildirishnoma yuborish uchun kerak)."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def update_order_status(order_id: int, status: OrderStatus) -> Optional[Order]:
    """Buyurtma holatini yangilaydi (masalan, to'lov qabul qilinganda 'paid')."""
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            return None
        order.status = status
        await session.commit()
        await session.refresh(order)
        return order


async def search_products_by_keywords(keywords: list[str], limit: int = 8) -> Sequence[Product]:
    """
    Berilgan kalit so'zlar (masalan AI rasm tahlilidan: "denim", "ko'k", "kurtka")
    bo'yicha nom, rang yoki kategoriya nomida moslik qidiradi.
    Rasm orqali qidiruv funksiyasi shu orqali ishlaydi.
    """
    if not keywords:
        return []
    async with async_session() as session:
        conditions = []
        for kw in keywords:
            like = f"%{kw}%"
            conditions.append(Product.name.ilike(like))
            conditions.append(Product.color.ilike(like))
        query = (
            select(Product)
            .where(Product.is_active.is_(True))
            .where(Product.stock > 0)
            .where(func.coalesce(Product.name, "").isnot(None))
        )
        from sqlalchemy import or_
        query = query.where(or_(*conditions)).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


# ---------------------------------------------------------------------------
# Kategoriyalar (Category)
# ---------------------------------------------------------------------------

async def add_category(name: str) -> Category:
    """Yangi kategoriya qo'shadi (masalan: Futbolka, Shim, Kurtka)."""
    async with async_session() as session:
        existing = await session.execute(
            select(Category).where(func.lower(Category.name) == name.strip().lower())
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"'{name}' nomli kategoriya allaqachon mavjud")

        category = Category(name=name.strip())
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


async def list_categories() -> Sequence[Category]:
    """Barcha kategoriyalarni qaytaradi."""
    async with async_session() as session:
        result = await session.execute(select(Category).order_by(Category.name))
        return result.scalars().all()


async def rename_category(category_id: int, new_name: str) -> Optional[Category]:
    """Kategoriya nomini o'zgartiradi."""
    async with async_session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            return None
        category.name = new_name
        await session.commit()
        await session.refresh(category)
        return category


async def delete_category(category_id: int) -> None:
    """
    Kategoriyani o'chiradi. Agar shu kategoriyaga tegishli mahsulotlar mavjud
    bo'lsa, ValueError chiqaradi (avval mahsulotlarni boshqa kategoriyaga
    ko'chirish yoki o'chirish kerak).
    """
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        )
        product_count = result.scalar_one()
        if product_count > 0:
            raise ValueError(
                f"Bu kategoriyada {product_count} ta mahsulot bor — avval ularni "
                f"boshqa kategoriyaga o'tkazing yoki o'chiring."
            )

        category = await session.get(Category, category_id)
        if category is not None:
            await session.delete(category)
            await session.commit()


# ---------------------------------------------------------------------------
# Admin statistikasi
# ---------------------------------------------------------------------------

async def get_inventory() -> Sequence[Product]:
    """
    Admin panel uchun: faol yoki nofaol, qoldig'i bor yoki yo'q — barcha
    mahsulotlarni qaytaradi (ombor holatini to'liq ko'rish uchun).
    """
    async with async_session() as session:
        result = await session.execute(
            select(Product).order_by(Product.stock.asc())
        )
        return result.scalars().all()


async def get_top_products(limit: int = 5, days: Optional[int] = None) -> list[dict]:
    """
    Eng ko'p sotilgan mahsulotlarni qaytaradi: nechta dona sotilgani va
    jami tushum (revenue). 'days' berilsa, faqat so'nggi N kunlik buyurtmalar
    hisobga olinadi (masalan, so'nggi 7 kun).
    """
    async with async_session() as session:
        query = (
            select(
                Product.id,
                Product.name,
                func.sum(Order.quantity).label("sold_qty"),
                func.sum(Order.total_price).label("revenue"),
            )
            .join(Order, Order.product_id == Product.id)
            .where(Order.status != OrderStatus.CANCELLED)
        )

        if days is not None:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.where(Order.created_at >= cutoff)

        query = (
            query.group_by(Product.id, Product.name)
            .order_by(func.sum(Order.quantity).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        return [
            {
                "product_id": row.id,
                "name": row.name,
                "sold_qty": int(row.sold_qty or 0),
                "revenue": float(row.revenue or 0),
            }
            for row in result.all()
        ]


async def get_top_customers(limit: int = 5) -> list[dict]:
    """
    Eng faol mijozlarni qaytaradi: nechta buyurtma bergani va jami
    sarflagan summasi. Admin panelda "kim ko'proq buyurtma beryapti"
    bo'limi uchun.
    """
    async with async_session() as session:
        query = (
            select(
                User.id,
                User.telegram_id,
                User.full_name,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_price).label("total_spent"),
            )
            .join(Order, Order.user_id == User.id)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(User.id, User.telegram_id, User.full_name)
            .order_by(func.count(Order.id).desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return [
            {
                "user_id": row.id,
                "telegram_id": row.telegram_id,
                "full_name": row.full_name or f"ID {row.telegram_id}",
                "order_count": int(row.order_count or 0),
                "total_spent": float(row.total_spent or 0),
            }
            for row in result.all()
        ]


async def get_dashboard_summary() -> dict:
    """
    Bosh sahifadagi KPI kartalari uchun: bugungi savdo, buyurtmalar soni,
    faol mijozlar soni, kam qolgan mahsulotlar soni.
    """
    async with async_session() as session:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        today_orders_result = await session.execute(
            select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_price), 0),
            ).where(Order.created_at >= today_start, Order.status != OrderStatus.CANCELLED)
        )
        today_order_count, today_revenue = today_orders_result.one()

        active_customers_result = await session.execute(
            select(func.count(func.distinct(Order.user_id)))
        )
        active_customers = active_customers_result.scalar_one()

        low_stock_result = await session.execute(
            select(func.count(Product.id)).where(Product.stock <= 4, Product.stock > 0)
        )
        low_stock_count = low_stock_result.scalar_one()

        out_of_stock_result = await session.execute(
            select(func.count(Product.id)).where(Product.stock == 0)
        )
        out_of_stock_count = out_of_stock_result.scalar_one()

        return {
            "today_revenue": float(today_revenue or 0),
            "today_order_count": int(today_order_count or 0),
            "active_customers": int(active_customers or 0),
            "low_stock_count": int(low_stock_count or 0),
            "out_of_stock_count": int(out_of_stock_count or 0),
        }


async def get_all_orders(limit: int = 200) -> list[dict]:
    """
    Admin panel — 'Buyurtmalar' sahifasi uchun barcha buyurtmalarni
    mijoz va mahsulot ma'lumotlari bilan birga qaytaradi.
    """
    async with async_session() as session:
        query = (
            select(
                Order.id,
                Order.quantity,
                Order.total_price,
                Order.status,
                Order.created_at,
                Product.name.label("product_name"),
                User.full_name,
                User.telegram_id,
                User.instagram_id,
            )
            .join(Product, Product.id == Order.product_id)
            .join(User, User.id == Order.user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return [
            {
                "id": row.id,
                "customer_name": row.full_name or f"ID {row.telegram_id or row.instagram_id}",
                "product_name": row.product_name,
                "quantity": row.quantity,
                "total_price": float(row.total_price),
                "status": row.status.value,
                "created_at": row.created_at.isoformat(),
            }
            for row in result.all()
        ]


async def get_all_customers(limit: int = 200) -> list[dict]:
    """
    Admin panel — 'Mijozlar' sahifasi uchun BARCHA ro'yxatdan o'tgan
    foydalanuvchilarni qaytaradi (buyurtma bergan yoki bermagan farqi yo'q),
    buyurtmalar soni va jami sarflagan summasi bilan birga.
    """
    async with async_session() as session:
        query = (
            select(
                User.id,
                User.telegram_id,
                User.instagram_id,
                User.full_name,
                User.username,
                User.photo_url,
                User.phone,
                User.created_at,
                func.count(Order.id).filter(Order.status != OrderStatus.CANCELLED).label("order_count"),
                func.sum(Order.total_price).filter(Order.status != OrderStatus.CANCELLED).label("total_spent"),
                func.max(Order.created_at).label("last_order_at"),
            )
            .outerjoin(Order, Order.user_id == User.id)
            .group_by(User.id, User.telegram_id, User.instagram_id, User.full_name, User.username, User.photo_url, User.phone, User.created_at)
            .order_by(func.count(Order.id).desc(), User.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return [
            {
                "id": row.id,
                "full_name": row.full_name or f"ID {row.telegram_id or row.instagram_id}",
                "username": row.username,
                "photo_url": row.photo_url,
                "telegram_id": row.telegram_id,
                "instagram_id": row.instagram_id,
                "phone": row.phone,
                "order_count": int(row.order_count or 0),
                "total_spent": float(row.total_spent or 0),
                "last_order_at": row.last_order_at.isoformat() if row.last_order_at else None,
            }
            for row in result.all()
        ]


# ---------------------------------------------------------------------------
# Foydalanish namunasi
# ---------------------------------------------------------------------------

async def _example() -> None:
    await init_db()

    category = await add_product(  # namuna: kategoriya kerak bo'lsa alohida qo'shiladi
        name="Erkaklar futbolkasi",
        price=99000,
        size="L",
        color="qora",
        stock=15,
        description="100% paxta, yozgi kolleksiya",
    )
    print("Qo'shildi:", category.id, category.name)

    products = await list_products(size="L", color="qora")
    print("Topildi:", len(products), "ta mahsulot")

    user = await get_or_create_user(telegram_id=123456789, full_name="Test User")
    order = await create_order(user_id=user.id, product_id=category.id, quantity=2)
    print("Buyurtma yaratildi:", order.id, "jami narx:", order.total_price)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_example())
