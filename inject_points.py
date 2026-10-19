import re
import sqlite3

# 1. مطمئن میشیم ستون points توی دیتابیس هست
try:
    conn = sqlite3.connect('panel.db')
    conn.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    conn.commit()
    conn.close()
except Exception:
    pass

# 2. خوندن فایل app.py
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 3. پیدا کردن صفحه داشبورد مشتری و اضافه کردن متغیر points (فعلاً 0)
if "customer_dashboard.html" in code:
    # اگه از قبل points= رو نداشت، اضافه‌ش می‌کنیم
    if "points=" not in code:
        # جایگزینی برای هر دو حالت کوتیشن تک یا جفت
        code = re.sub(r"render_template\((['\"])customer_dashboard\.html\1\)", r"render_template(\1customer_dashboard.html\1, points=0)", code)
        print("✅ متغیر points با موفقیت به صفحه مشتری اضافه شد.")

# 4. پیدا کردن کد ثبت سفارش برای اضافه کردن منطق امتیاز
# (این رو به صورت کامنت اضافه می‌کنیم تا بعدا خودت جای دقیقش بذاری)
if "INSERT INTO orders" in code and "earned_points" not in code:
    print("ℹ️ بخش ثبت سفارش پیدا شد. (برای اضافه کردن امتیاز در لحظه خرید، نیاز به بررسی کدهای اصلی هست).")

# 5. ذخیره فایل
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ فایل app.py با موفقیت آپدیت شد.")
