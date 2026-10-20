import re

file = 'templates/panel_dashboard.html'
try:
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()
except FileNotFoundError:
    print("❌ فایل panel_dashboard.html پیدا نشد!")
    exit()

# 1. زور زدن استایل پس زمینه و کادرها به کل صفحه
force_css = """
<style>
    body { background-color: #021222 !important; color: white !important; font-family: Tahoma, sans-serif !important; }
    form, .card, .glass-panel, .main-box, div[style*="background"] { 
        background: #06213b !important; 
        border: 1.5px solid #00a8ff !important; 
        border-radius: 20px !important; 
        padding: 20px !important; 
        box-shadow: 0 0 15px rgba(0,168,255,0.15) !important;
    }
    label, h1, h2, h3, span, div { font-family: Tahoma, sans-serif !important; }
</style>
"""
if 'NUCLEAR_FIX' not in html:
    html = html.replace('</head>', force_css + '\n</head>')

# 2. زور زدن استایل کادرهای ورودی (دقیقا مثل صفحه کانال)
html = re.sub(r'<input([^>]*?)>', r'<input\1 style="background:#021222 !important; border:1.5px solid #0066ff !important; color:white !important; padding:15px !important; border-radius:12px !important; width:100% !important; font-family:Tahoma !important; outline:none !important; margin-bottom:10px !important;">', html)

# 3. زور زدن استایل به تکست آریا (توضیحات)
html = re.sub(r'<textarea([^>]*?)>', r'<textarea\1 style="background:#021222 !important; border:1.5px solid #0066ff !important; color:white !important; padding:15px !important; border-radius:12px !important; width:100% !important; font-family:Tahoma !important; min-height:100px !important; outline:none !important; margin-bottom:10px !important;">', html)

# 4. زور زدن استایل به دکمه ثبت محصول (گرادیانت سبز-آبی)
html = re.sub(r'<button([^>]*?)type="submit"([^>]*?)>', r'<button\1type="submit"\2 style="background:linear-gradient(90deg, #00ff88, #00d4ff) !important; color:#021222 !important; font-weight:bold !important; padding:15px !important; border-radius:15px !important; width:100% !important; border:none !important; font-size:16px !important; margin-top:10px !important; box-shadow: 0 4px 15px rgba(0,180,219,0.3) !important;">', html)

# 5. دکمه‌های رنگی 6 گانه (اگه از تگ a یا div استفاده کردن)
# این بخش سعی میکنه دکمه‌های رنگی بالای فرم رو هم با حاشیه نئونی هماهنگ کنه
html = html.replace('ساخت عکس با هوش مصنوعی', 'ساخت با AI')
html = html.replace('قوی‌سازی متن', 'قوی‌سازی متن')

with open(file, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ استایل‌های صفحه کانال با زور (Inline Styles) روی صفحه اصلی (panel_dashboard.html) اعمال شد.")
