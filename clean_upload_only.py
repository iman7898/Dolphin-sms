import re, glob, os

upload_box = """
<div style="margin-bottom: 20px; padding: 30px 20px; background: #031526; border: 2px dashed #00ff88; border-radius: 15px; text-align: center; cursor: pointer;" onclick="document.querySelector('input[type=file]').click()">
    <div style="font-size: 50px; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(0,255,136,0.5));">📸</div>
    <div style="color: #00ff88; font-weight: bold; font-size: 18px; font-family: Tahoma;">برای آپلود عکس محصول کلیک کنید</div>
    <div style="color: #6688aa; font-size: 13px; margin-top: 8px; font-family: Tahoma;">فرمت‌های مجاز: JPG, PNG</div>
</div>
"""

for file in glob.glob('templates/**/*.html', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'افزودن محصول جدید' in html:
        # 1. جلوگیری از کش شدن مرورگر
        if 'Cache-Control' not in html:
            html = html.replace('<head>', '<head>\n<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />\n<meta http-equiv="Pragma" content="no-cache" />\n<meta http-equiv="Expires" content="0" />\n')

        # 2. پاک کردن اسکریپت قبلی اگه مونده باشه
        html = re.sub(r'<!-- REMOVE_AI_BUTTONS_SCRIPT -->.*?<!-- REMOVE_AI_BUTTONS_SCRIPT -->', '', html, flags=re.DOTALL)
        
        # 3. پیدا کردن و نابود کردن گرید ۶ دکمه ای و جایگزینی با کادر آپلود
        pattern1 = r'<div[^>]*class="[^"]*(?:btn-grid|ai-grid)[^"]*"[^>]*>.*?</div>\s*</div>'
        html = re.sub(pattern1, upload_box, html, flags=re.DOTALL)
        
        # 4. اگه با کلاس پیدا نشد، با استایل اینلاین پیدا و پاکش کن
        pattern2 = r'<div[^>]*style="[^"]*display:\s*grid[^"]*"[^>]*>.*?</div>\s*</div>'
        html = re.sub(pattern2, upload_box, html, flags=re.DOTALL)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ دکمه‌ها پاک و کادر آپلود در {file} جایگزین شد.")
