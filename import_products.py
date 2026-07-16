"""
mahsulotlar_50ta.xlsx faylidan mahsulotlarni to'g'ridan-to'g'ri bazaga import qiladi.

Ishlatish (lokal kompyuteringizda, loyiha papkasida):
    pip install openpyxl
    python import_products.py mahsulotlar_50ta.xlsx

Fayl formati (ustunlar):
    Nomi | Kategoriya | Narx (so'm) | O'lchamlar (vergul bilan) | Ranglar (vergul bilan) |
    Miqdor (dona) | Tavsif | Rasm URL

Har bir qatordagi "O'lchamlar" va "Ranglar" vergul bilan ajratilgan bo'lsa (masalan "S, M, L"),
har bir kombinatsiya uchun alohida mahsulot yaratiladi (masalan 3 o'lcham x 2 rang = 6 mahsulot).

Eslatma: 2-qator (sariq rangda belgilangan) — bu namuna qator, avtomatik o'tkazib yuboriladi.
"""

import asyncio
import sys

import openpyxl

import database as db


async def import_from_excel(path: str) -> None:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    await db.init_db()

    # Mavjud kategoriyalarni olib, nom -> id lug'atini tuzamiz
    existing_categories = await db.list_categories()
    category_map = {c.name: c.id for c in existing_categories}

    created_count = 0
    skipped_count = 0

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row_idx == 2:
            continue  # namuna (legend) qatorni o'tkazib yuboramiz

        name, category_name, price, sizes_raw, colors_raw, stock, description, image_url = (
            list(row) + [None] * (8 - len(row))
        )[:8]

        if not name or not price:
            skipped_count += 1
            continue

        # Kategoriya mavjud bo'lmasa, avtomatik yaratamiz
        category_id = None
        if category_name:
            category_name = str(category_name).strip()
            if category_name not in category_map:
                new_cat = await db.add_category(category_name)
                category_map[category_name] = new_cat.id
                print(f"  Yangi kategoriya yaratildi: {category_name}")
            category_id = category_map[category_name]

        sizes = [s.strip() for s in str(sizes_raw).split(',')] if sizes_raw else [None]
        colors = [c.strip() for c in str(colors_raw).split(',')] if colors_raw else [None]

        for size in sizes:
            for color in colors:
                await db.add_product(
                    name=str(name).strip(),
                    price=float(price),
                    size=size,
                    color=color,
                    stock=int(stock) if stock else 0,
                    description=str(description).strip() if description else None,
                    image_url=str(image_url).strip() if image_url else None,
                    category_id=category_id,
                )
                created_count += 1

    print(f"\n✅ Import tugadi: {created_count} ta mahsulot qo'shildi, {skipped_count} ta qator o'tkazib yuborildi (bo'sh).")


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "mahsulotlar_50ta.xlsx"
    print(f"Import boshlanmoqda: {file_path}")
    asyncio.run(import_from_excel(file_path))
