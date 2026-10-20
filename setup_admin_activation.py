import os, sqlite3, re

# 1. آپدیت دیتابیس برای ذخیره تنظیمات کانال
try:
    conn = sqlite3.connect('panel.db')
    conn.execute("CREATE TABLE IF NOT EXISTS shop_bot_settings (shop_id INTEGER PRIMARY KEY, channel_id TEXT, max_messages INTEGER, is_active INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()
    print("✅ دیتابیس آپدیت شد.")
except Exception as e:
    print("⚠️ خطا در دیتابیس:", e)

# 2. ساخت صفحه HTML جدید
html_content = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>فعال‌سازی ادمین | دلفین</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Tahoma, Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #021222; color: white; padding: 20px; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; }
        .main-box { width: 100%; max-width: 500px; background: #06213b; border: 1.5px solid #00a8ff; border-radius: 20px; padding: 25px; box-shadow: 0 0 20px rgba(0,168,255,0.15); }
        .header { text-align: center; color: #00d4ff; font-size: 18px; font-weight: bold; margin-bottom: 25px; display: flex; justify-content: center; align-items: center; gap: 10px; }
        .form-group { margin-bottom: 20px; text-align: right; }
        label { display: block; margin-bottom: 10px; color: #a0c4ff; font-size: 14px; font-weight: bold; }
        input { width: 100%; background: #021222; border: 1.5px solid #0066ff; color: white; padding: 15px; border-radius: 12px; font-size: 14px; outline: none; }
        .btn-submit { width: 100%; background: linear-gradient(90deg, #00ff88, #00d4ff); color: #021222; border: none; padding: 15px; border-radius: 15px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .guide-box { background: rgba(255, 215, 0, 0.1); border: 1px dashed #ffd700; padding: 15px; border-radius: 12px; margin-top: 20px; font-size: 13px; color: #ffd700; line-height: 1.8; }
        .back-btn { display: inline-block; color: #00d4ff; text-decoration: none; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="main-box">
        <a href="/panel/" class="back-btn">← بازگشت به پنل</a>
        <div class="header">⚙️ فعال‌سازی ادمین کانال</div>
        
        <form method="POST" action="/panel/activate-admin">
            <div class="form-group">
                <label>🆔 آیدی کانال (مثلاً @my_shop)</label>
                <input type="text" name="channel_id" placeholder="@channel_id" required>
            </div>
            <div class="form-group">
                <label>🔢 تعداد پیام‌های مجاز (شمارش)</label>
                <input type="number" name="max_messages" placeholder="مثلاً ۱۰۰" required>
            </div>
            <button type="submit" class="btn-submit">🚀 فعال‌سازی ادمین</button>
        </form>

        <div class="guide-box">
            <b>راهنمای ادمین کردن ربات:</b><br>
            برای اینکه ربات بتونه پیام بفرسته، باید بری توی کانال روبیکا، روی گزینه «مدیران» بزنی و یوزرنیم ربات رو به عنوان <b>مدیر (Admin)</b> اضافه کنی. این کار برای امنیت کانال شماست و فقط یک‌بار باید انجام بشه.
        </div>
    </div>
</body>
</html>"""

with open('templates/panel_admin_activation.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
print("✅ صفحه HTML ساخته شد.")

# 3. اضافه کردن مسیر (Route) به app.py
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

if '/panel/activate-admin' not in code:
    route_code = """
@app.route('/panel/activate-admin', methods=['GET', 'POST'])
def panel_activate_admin():
    if request.method == 'POST':
        channel_id = request.form.get('channel_id')
        max_messages = request.form.get('max_messages')
        shop_id = session.get('user_id') # یا هر چیزی که برای مغازه‌دار استفاده میکنی
        
        import sqlite3
        conn = sqlite3.connect('panel.db')
        conn.execute("INSERT OR REPLACE INTO shop_bot_settings (shop_id, channel_id, max_messages, is_active) VALUES (?, ?, ?, 1)", (shop_id, channel_id, max_messages))
        conn.commit()
        conn.close()
        
        flash('✅ ادمین کانال با موفقیت فعال شد!', 'success')
        return redirect('/panel/')
        
    return render_template('panel_admin_activation.html')
    
"""
    # تزریق قبل از app.run
    code = code.replace('if __name__ == "__main__":', route_code + '\nif __name__ == "__main__":')
    print("✅ مسیر /panel/activate-admin به app.py اضافه شد.")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

# 4. اضافه کردن دکمه به داشبورد مغازه‌دار
dash_file = 'templates/panel_dashboard.html'
if os.path.exists(dash_file):
    with open(dash_file, 'r', encoding='utf-8') as f:
        dash_html = f.read()
    
    if 'فعال‌سازی ادمین' not in dash_html:
        # یه دکمه خوشگل که به این صفحه لینک بشه
        btn_html = """
        <a href="/panel/activate-admin" style="text-decoration:none; color:inherit; display:block; margin-top:15px;">
            <div style="background: rgba(0, 212, 255, 0.1); border: 1.5px solid #00d4ff; border-radius: 15px; padding: 15px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 0 15px rgba(0,212,255,0.2);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">⚙️</span>
                    <span style="font-weight: bold; color: white; font-size: 15px;">فعال‌سازی ادمین کانال</span>
                </div>
                <span style="color: #00d4ff; font-size: 20px;">‹</span>
            </div>
        </a>
        """
        # اضافه کردن به اول یا آخر یه بخش مشخص (مثلاً اول بادی)
        if '<body>' in dash_html:
            dash_html = dash_html.replace('<body>', '<body>\n' + btn_html)
        else:
            dash_html = btn_html + dash_html
            
        with open(dash_file, 'w', encoding='utf-8') as f:
            f.write(dash_html)
        print("✅ دکمه به داشبورد مغازه‌دار اضافه شد.")
