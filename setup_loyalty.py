import sqlite3
import os

# 1. آپدیت دیتابیس
print("1️⃣ در حال آپدیت دیتابیس...")
try:
    conn = sqlite3.connect('panel.db')
    cursor = conn.cursor()
    # اضافه کردن ستون points (امتیاز) به جدول کاربران
    cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    conn.commit()
    print("✅ ستون points با موفقیت به دیتابیس اضافه شد.")
except sqlite3.OperationalError:
    print("ℹ️ ستون points از قبل وجود داشت (نیازی به تغییر نبود).")
finally:
    conn.close()

# 2. آپدیت ظاهر پنل مشتری (اضافه کردن کارت امتیاز)
print("\n2️⃣ در حال آپدیت ظاهر پنل مشتری...")
file_path = 'templates/customer_dashboard.html'
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    if 'امتیاز وفاداری' not in html:
        # یه کارت گرادیانت خوشگل برای نمایش امتیاز
        card = """
        <div style="background: linear-gradient(135deg, #00d4ff, #0055ff); border-radius: 15px; padding: 20px; text-align: center; color: white; margin: 20px; box-shadow: 0 4px 15px rgba(0,212,255,0.3);">
            <h3 style="margin: 0; font-size: 16px; font-family: Tahoma;">✨ امتیاز وفاداری شما</h3>
            <h1 style="margin: 10px 0; font-size: 40px; font-weight: bold;">{{ points or 0 }}</h1>
            <p style="margin: 0; font-size: 12px; opacity: 0.9; font-family: Tahoma;">با هر ۱۰,۰۰۰ تومان خرید، ۱ امتیاز بگیرید!</p>
        </div>
        """
        # اضافه کردن کارت به بالای صفحه (بعد از تگ body)
        if '<body>' in html:
            html = html.replace('<body>', '<body>\n' + card)
        else:
            html = card + html
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ کارت نمایش امتیاز به پنل مشتری اضافه شد.")
    else:
        print("ℹ️ کارت امتیاز از قبل وجود داشت.")
else:
    print("⚠️ فایل customer_dashboard.html پیدا نشد! لطفاً اسم فایل داشبورد مشتری رو چک کن.")
