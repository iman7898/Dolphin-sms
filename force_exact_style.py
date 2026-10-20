import os, re

# 1. خوندن فایل صفحه کانال
source_file = 'templates/panel_channel_send.html'
if not os.path.exists(source_file):
    print("⚠️ فایل panel_channel_send.html پیدا نشد!")
    exit()

with open(source_file, 'r', encoding='utf-8') as f:
    source = f.read()

# 2. استخراج کدهای CSS و فونت‌ها دقیقا از خودش
style_match = re.search(r'<style>(.*?)</style>', source, re.DOTALL)
style = style_match.group(1) if style_match else ''

# 3. ساخت فایل جدید با استایل‌های کپی شده
html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>افزودن محصول | دلفین</title>
    <style>
        {style}
        
        /* استایل‌های اختصاصی این صفحه (با استایل‌های خودت هماهنگ شده) */
        * {{ font-family: inherit !important; box-sizing: border-box; }}
        body {{ background-color: #021222 !important; color: white !important; }}
        
        .main-box {{ 
            width: 100%; max-width: 500px; margin: 15px auto; 
            background: #06213b !important; 
            border: 1.5px solid #00a8ff !important; 
            border-radius: 20px; padding: 20px; 
        }}
        
        .header-title {{ 
            text-align: center; color: #00d4ff !important; 
            font-size: 18px; font-weight: bold; margin-bottom: 20px; 
        }}
        
        .btn-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 25px; }}
        
        .grid-btn {{ 
            background: rgba(0,0,0,0.2) !important; 
            border-radius: 12px; padding: 15px 5px; text-align: center; 
            font-size: 13px; font-weight: bold; display: flex; 
            flex-direction: column; align-items: center; gap: 8px; cursor: pointer;
        }}
        .grid-btn i {{ font-size: 24px; font-style: normal; }}
        
        .c-green {{ border: 1.5px solid #00ff88 !important; color: #00ff88 !important; }}
        .c-yellow {{ border: 1.5px solid #ffd700 !important; color: #ffd700 !important; }}
        .c-purple {{ border: 1.5px solid #b100ff !important; color: #b100ff !important; }}
        .c-pink {{ border: 1.5px solid #ff69b4 !important; color: #ff69b4 !important; }}

        .form-group {{ margin-bottom: 20px; text-align: right; }}
        .form-group label {{ display: block; margin-bottom: 10px; color: white !important; font-size: 14px; font-weight: bold; }}
        
        .form-control {{ 
            width: 100%; 
            background: #021222 !important; 
            border: 1.5px solid #0066ff !important; 
            color: white !important; 
            padding: 15px; border-radius: 12px; 
            font-size: 14px; outline: none; 
        }}
        
        textarea.form-control {{ resize: none; min-height: 120px; }}
        
        .submit-btn {{ 
            width: 100%; 
            background: linear-gradient(90deg, #00ff88, #00d4ff) !important; 
            color: #021222 !important; 
            border: none; padding: 15px; 
            border-radius: 15px; font-size: 16px; 
            font-weight: bold; cursor: pointer; margin-top: 10px; 
        }}
        #realImageInput {{ display: none; }}
    </style>
</head>
<body>

    <div class="main-box">
        <div class="header-title">
            <span>➕</span> افزودن محصول جدید
        </div>
        
        <div style="border-bottom: 1px dashed rgba(0, 168, 255, 0.4); margin-bottom: 20px;"></div>

        <div class="btn-grid">
            <div class="grid-btn c-green" onclick="document.getElementById('realImageInput').click()">
                <i>📷</i> عکس
            </div>
            <div class="grid-btn c-yellow">
                <i>😋</i> ایموجی
            </div>
            <div class="grid-btn c-purple">
                <i>🤖</i> قوی‌سازی<br>متن
            </div>
            <div class="grid-btn c-yellow">
                <i>✨</i> تغییر با AI
            </div>
            <div class="grid-btn c-pink">
                <i>🎨</i> ساخت با AI
            </div>
            <div class="grid-btn c-green" onclick="document.getElementById('realImageInput').click()">
                <i>📁</i> آپلود از گوشی
            </div>
        </div>

        <form method="POST" enctype="multipart/form-data" action="/panel/add-product">
            <input type="file" id="realImageInput" name="image" accept="image/*">
            
            <div class="form-group">
                <label>📦 نام محصول</label>
                <input type="text" name="name" class="form-control" placeholder="مثلاً سیب قرمز" required>
            </div>

            <div class="form-group">
                <label>💰 قیمت (تومان)</label>
                <input type="number" name="price" class="form-control" placeholder="مثلاً ۵۰۰۰۰" required>
            </div>

            <div class="form-group">
                <label>📝 توضیحات (اختیاری)</label>
                <textarea name="description" class="form-control" placeholder="توضیح کوتاه درباره محصول..."></textarea>
            </div>

            <button type="submit" class="submit-btn">
                💾 ثبت محصول
            </button>
        </form>
    </div>

</body>
</html>
"""

with open('templates/add_product.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ فایل add_product.html با استایل دقیق و فونت صفحه کانال بازنویسی شد.")
