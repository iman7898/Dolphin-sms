# -*- coding: utf-8 -*-
import sqlite3

DATA = [
 ("رستوران و کافه", "🍔", "#fb923c", [
    ("رستوران","🍽️","#fb923c"),
    ("فست‌فود","🍔","#f97316"),
    ("کافه و چای","☕","#a16207"),
 ]),
 ("سوپرمارکت", "🛒", "#22d3ee", [
    ("خواروبار","🛒","#22d3ee"),
    ("کنسرو و رب","🥫","#dc2626"),
    ("تنقلات","🍿","#f59e0b"),
    ("نوشیدنی","🥤","#06b6d4"),
 ]),
 ("میوه و سبزیجات", "🥬", "#00ff9d", [
    ("میوه","🍎","#ff6b6b"),
    ("سبزیجات","🥦","#00ff9d"),
    ("خشکبار و عسل","🍯","#eab308"),
 ]),
 ("گوشت و لبنیات", "🥩", "#ff4d6d", [
    ("گوشت و مرغ","🍖","#ff4d6d"),
    ("ماهی","🐟","#00d4ff"),
    ("لبنیات","🥛","#7de5ff"),
    ("نان و شیرینی","🍞","#f59e0b"),
 ]),
 ("داروخانه", "💊", "#10b981", [
    ("دارو","💊","#10b981"),
    ("آرایشی و بهداشتی","💄","#ec4899"),
 ]),
 ("خدمات و پوشاک", "🔑", "#8b5cf6", [
    ("پوشاک","👕","#bf00ff"),
    ("کیف و کفش","👟","#3b82f6"),
    ("کلیدسازی","🔑","#f59e0b"),
    ("آرایشگاه","💇","#ec4899"),
    ("تعمیرات","🔧","#64748b"),
 ]),
]

conn = sqlite3.connect('panel.db', timeout=15)
c = conn.cursor()
c.execute("DELETE FROM product_categories")
print("🗑 پاک شد")

order = 0
mc = 0
sc = 0
for name, icon, color, subs in DATA:
    order += 1
    c.execute("INSERT INTO product_categories (name,icon,color,sort_order,is_main) VALUES (?,?,?,?,1)",
              (name, icon, color, order))
    mc += 1
    for sn, si, sc2 in subs:
        order += 1
        c.execute("INSERT INTO product_categories (name,icon,color,sort_order,is_main) VALUES (?,?,?,?,0)",
                  (sn, si, sc2, order))
        sc += 1

conn.commit()
conn.close()
print(f"✅ {mc} دستهٔ اصلی + {sc} زیرمجموعه")
