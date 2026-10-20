import os, re

filepath = 'templates/panel_dashboard.html'
if not os.path.exists(filepath):
    print("⚠️ فایل پیدا نشد!")
    exit()

with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# استایل‌های دقیق و زورگویانه که تم صفحه کانال رو پیاده میکنه
force_css = """
<!-- ====== ULTIMATE FORCE THEME START ====== -->
<style>
    /* پس زمینه اصلی */
    body { background-color: #021222 !important; color: white !important; }
    
    /* کادرهای اصلی (شامل فرم ها و کارت ها) */
    .card, .glass-panel, form, .main-box, .content-box { 
        background: #06213b !important; 
        border: 1.5px solid #00a8ff !important; 
        border-radius: 20px !important; 
        padding: 20px !important; 
        box-shadow: 0 0 15px rgba(0,168,255,0.15) !important;
    }
    
    /* اینپوت ها و تکست آریا */
    input, textarea, select { 
        background: #031526 !important; 
        border: 1.5px solid #0066ff !important; 
        color: white !important; 
        padding: 15px !important; 
        border-radius: 12px !important; 
        font-family: Tahoma, Arial, sans-serif !important; 
        font-size: 14px !important;
        width: 100% !important;
        outline: none !important;
    }
    
    /* دکمه های ثبت و ارسال */
    button[type="submit"], .submit-btn, .btn-primary { 
        background: linear-gradient(90deg, #00ff88, #00d4ff) !important; 
        color: #021222 !important; 
        font-weight: bold !important; 
        border-radius: 15px !important; 
        padding: 15px !important; 
        border: none !important; 
        font-family: Tahoma !important;
        font-size: 16px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(0,180,219,0.3) !important;
    }

    /* دکمه بنفش رنگی که تو عکس قبلی بود رو کلا مخفی میکنه (اگه مونده باشه) */
    .btn-purple { background: transparent !important; border: 1px solid #00a8ff !important; }

    /* تیترها */
    h1, h2, h3 { color: #00d4ff !important; text-align: center !important; }
    
    /* لیبل ها */
    label { color: #fff !important; font-family: Tahoma !important; font-weight: bold !important; }
</style>
<!-- ====== ULTIMATE FORCE THEME END ====== -->
"""

# تزریق استایل به فایل
if 'ULTIMATE FORCE THEME START' not in html:
    if '</head>' in html:
        html = html.replace('</head>', force_css + '\n</head>')
    else:
        html = force_css + html
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ استایل‌های صفحه کانال با موفقیت به زور روی فایل اصلی اعمال شد.")
else:
    print("ℹ️ استایل از قبل اعمال شده بود.")
