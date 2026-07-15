"""
Bazani boshlang'ich (demo) ma'lumotlar bilan to'ldirish uchun skript.
Faqat bir marta, birinchi sozlashda ishga tushiring:

    python seed.py

Bu skript avval kategoriyalarni, so'ng har bir kategoriyaga tegishli
mahsulotlarni qo'shadi. Agar shop.db allaqachon mavjud bo'lsa va
qayta to'ldirmoqchi bo'lsangiz, avval shop.db faylini o'chiring.
"""

import asyncio

import database as db


async def main() -> None:
    await db.init_db()

    categories = ["Futbolka", "Ko'ylak", "Shim", "Kurtka", "Aksessuar"]
    cat_ids = {}
    for name in categories:
        cat = await db.add_category(name)
        cat_ids[name] = cat.id
        print(f"Kategoriya qo'shildi: {name} (id={cat.id})")

    products = [
        dict(name="Klassik oq futbolka", price=99000, size="L", color="Oq", stock=24,
             description="100% paxta, yozgi kolleksiya. Erkin fason.", category_id=cat_ids["Futbolka"]),
        dict(name="Qora futbolka", price=99000, size="M", color="Qora", stock=18,
             description="100% paxta, kundalik kiyish uchun.", category_id=cat_ids["Futbolka"]),
        dict(name="Sport futbolka", price=119000, size="L", color="Yashil", stock=30,
             description="Nafas oluvchi mato, sport uchun.", category_id=cat_ids["Futbolka"]),
        dict(name="Denim kurtka", price=349000, size="M", color="Ko'k", stock=6,
             description="Og'ir zichlikdagi denim, klassik kroy.", category_id=cat_ids["Kurtka"]),
        dict(name="Zamonaviy bomber", price=299000, size="L", color="Qora", stock=0,
             description="Yengil, shamolga chidamli.", category_id=cat_ids["Kurtka"]),
        dict(name="Rasmiy ko'ylak", price=189000, size="S", color="Oq", stock=15,
             description="Ish uchun ideal, dazmollashni talab qilmaydi.", category_id=cat_ids["Ko'ylak"]),
        dict(name="Chiziqli ko'ylak", price=169000, size="M", color="Ko'k-oq", stock=9,
             description="Yengil paxta mato, bahor-yoz kolleksiyasi.", category_id=cat_ids["Ko'ylak"]),
        dict(name="Slim fit shim", price=229000, size="32", color="Qora", stock=2,
             description="Cho'ziluvchan mato, kundalik va yarim rasmiy uchun.", category_id=cat_ids["Shim"]),
        dict(name="Klassik shim", price=209000, size="34", color="Kul rang", stock=11,
             description="To'g'ri kroy, ofis uchun.", category_id=cat_ids["Shim"]),
        dict(name="Teri kamar", price=79000, size="One Size", color="Jigarrang", stock=12,
             description="Tabiiy teridan, metall pryajka bilan.", category_id=cat_ids["Aksessuar"]),
    ]

    for p in products:
        prod = await db.add_product(**p)
        print(f"Mahsulot qo'shildi: {prod.name} (id={prod.id})")

    print("\n✅ Demo ma'lumotlar muvaffaqiyatli qo'shildi!")


if __name__ == "__main__":
    asyncio.run(main())
