"""
Bazani boshlang'ich (demo) ma'lumotlar bilan to'ldirish uchun skript.
Faqat bir marta, birinchi sozlashda ishga tushiring:

    python seed.py

Bu skript avval kategoriyalarni, so'ng har bir kategoriyaga tegishli
mahsulotlarni qo'shadi. Agar shop.db allaqachon mavjud bo'lsa va
qayta to'ldirmoqchi bo'lsangiz, avval shop.db faylini o'chiring.

Eslatma: production serverda (Render) bu skript shart emas — api.py
serverni birinchi marta ishga tushirganda bazasi bo'sh bo'lsa, shu
demo ma'lumotlarni avtomatik qo'shadi.
"""

import asyncio

import database as db


async def main() -> None:
    await db.init_db()

    categories = ["Atirgullar", "Pionlar", "Aralash gullar", "Quyosh gullari"]
    cat_ids = {}
    for name in categories:
        cat = await db.add_category(name)
        cat_ids[name] = cat.id
        print(f"Kategoriya qo'shildi: {name} (id={cat.id})")

    products = [
        dict(name="11 ta qizil atirgul buketi", price=249000, size="O'rta", color="Qizil", stock=15,
             description="Yangi kesilgan qizil atirgullar, elegant qadoqlash bilan.", category_id=cat_ids["Atirgullar"]),
        dict(name="Pushti atirgullar guldastasi", price=229000, size="O'rta", color="Pushti", stock=12,
             description="Nafis pushti atirgullar, romantik uchrashuvlar uchun.", category_id=cat_ids["Atirgullar"]),
        dict(name="25 ta atirgul katta buketi", price=459000, size="Katta", color="Qizil", stock=6,
             description="Hashamatli katta buket, muhim kunlar uchun.", category_id=cat_ids["Atirgullar"]),
        dict(name="Pion guldastasi", price=279000, size="O'rta", color="Pushti", stock=8,
             description="Mavsumiy pionlar, boy va yumshoq ifor bilan.", category_id=cat_ids["Pionlar"]),
        dict(name="Oq pionlar buketi", price=289000, size="O'rta", color="Oq", stock=5,
             description="Nafis oq pionlar, to'y va marosimlar uchun mos.", category_id=cat_ids["Pionlar"]),
        dict(name="Bahor aralash buketi", price=199000, size="O'rta", color="Rang-barang", stock=14,
             description="Mavsumiy gullardan tashkil topgan quvnoq buket.", category_id=cat_ids["Aralash gullar"]),
        dict(name="Premium aralash guldasta", price=349000, size="Katta", color="Rang-barang", stock=7,
             description="Turli gullar uyg'unlashgan hashamatli tarkib.", category_id=cat_ids["Aralash gullar"]),
        dict(name="Kichik sovg'a buketi", price=129000, size="Kichik", color="Rang-barang", stock=20,
             description="Kundalik sovg'a uchun ixcham va chiroyli buket.", category_id=cat_ids["Aralash gullar"]),
        dict(name="Quyoshgul buketi", price=179000, size="O'rta", color="Sariq", stock=10,
             description="Yorqin quyoshgullar, kayfiyat ko'tarish uchun ajoyib sovg'a.", category_id=cat_ids["Quyosh gullari"]),
        dict(name="Katta quyoshgul guldastasi", price=259000, size="Katta", color="Sariq", stock=4,
             description="Yirik quyoshgullardan tashkil topgan quvnoq buket.", category_id=cat_ids["Quyosh gullari"]),
    ]

    for p in products:
        prod = await db.add_product(**p)
        print(f"Mahsulot qo'shildi: {prod.name} (id={prod.id})")

    print("\n✅ Demo ma'lumotlar muvaffaqiyatli qo'shildi!")


if __name__ == "__main__":
    asyncio.run(main())
