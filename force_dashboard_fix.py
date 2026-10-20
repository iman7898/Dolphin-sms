import os, re

dashboard_file = 'templates/panel_dashboard.html'
channel_file = 'templates/panel_channel_send.html'

if not os.path.exists(dashboard_file) or not os.path.exists(channel_file):
    print("⚠️ فایل‌ها پیدا نشدند!")
    exit()

# 1. کدهای استایل صفحه کانال رو بردار
with open(channel_file, 'r', encoding='utf-8') as f:
    channel_html = f.read()
style_match = re.search(r'<style>(.*?)</style>', channel_html, re.DOTALL)
channel_style = style_match.group(1) if style_match else ''

# 2. فایل اصلی داشبورد رو باز کن
with open(dashboard_file, 'r', encoding='utf-8') as f:
    dash_html = f.read()

# 3. استایل رو به فایل داشبورد تزریق کن (اگه از قبل نبود)
if '/* --- FORCED PRODUCT STYLE --- */' not in dash_html:
    force_css = f"""
    <style>
    /* --- FORCED PRODUCT STYLE --- */
    {channel_style}
    
    /* اعمال زورکی استایل‌های کانال به فرم محصول */
    .add-product-container, form#addProductForm {{
        background: #06213b !important;
        border: 1.5px solid #00a8ff !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 0 15px rgba(0,168,255,0.15) !important;
    }}
    
    .add-product-container input, .add-product-container textarea,
    form#addProductForm input, form#addProductForm textarea {{
        background: #021222 !important;
        border: 1.5px solid #0066ff !important;
        color: white !important;
        padding: 15px !important;
        border-radius: 12px !important;
        font-family: inherit !important;
    }}
    
    .add-product-container button[type="submit"],
    form#addProductForm button[type="submit"] {{
        background: linear-gradient(90deg, #00ff88, #00d4ff) !important;
        color: #021222 !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        padding: 15px !important;
        border: none !important;
    }}
    </style>
    """
    if '</head>' in dash_html:
        dash_html = dash_html.replace('</head>', force_css + '\n</head>')
    else:
        dash_html += force_css

with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(dash_html)

print("✅ استایل‌های صفحه کانال با زور روی فایل اصلی (panel_dashboard.html) اعمال شد.")
