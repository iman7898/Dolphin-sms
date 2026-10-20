import os, glob

# کد HTML جدید و شیشه‌ای
new_html = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>افزودن محصول | دلفین</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Tahoma, Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { 
            background-color: #020813; 
            background-image: radial-gradient(1.5px 1.5px at 20px 30px, #fff, rgba(0,0,0,0)), radial-gradient(1.5px 1.5px at 40px 70px, #fff, rgba(0,0,0,0)), radial-gradient(2px 2px at 50px 160px, #00d4ff, rgba(0,0,0,0));
            background-repeat: repeat; background-size: 200px 200px; color: white; padding: 20px; min-height: 100vh;
            display: flex; justify-content: center; align-items: flex-start;
        }
        .glass-panel { width: 100%; max-width: 500px; background: rgba(0, 30, 60, 0.6); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 20px; padding: 20px; box-shadow: 0 0 20px rgba(0,212,255,0.1), inset 0 0 20px rgba(0,212,255,0.05); backdrop-filter: blur(10px); margin-top: 10px; }
        .header-title { text-align: center; color: #00d4ff; font-size: 20px; margin-bottom: 20px; display: flex; justify-content: center; align-items: center; gap: 10px; text-shadow: 0 0 10px rgba(0,212,255,0.5); }
        .ai-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 25px; }
        .ai-btn { background: rgba(0, 0, 0, 0.3); border-radius: 12px; padding: 15px 5px; text-align: center; color: white; font-size: 12px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; display: flex; flex-direction: column; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
        .ai-btn:active { transform: scale(0.95); }
        .ai-btn i { font-size: 24px; font-style: normal; }
        .btn-img { border: 1px solid #00ff88; color: #00ff88; box-shadow: 0 0 10px rgba(0,255,136,0.2); }
        .btn-emoji { border: 1px solid #ffd700; color: #ffd700; box-shadow: 0 0 10px rgba(255,215,0,0.2); }
        .btn-text { border: 1px solid #ff00ff; color: #ff00ff; box-shadow: 0 0 10px rgba(255,0,255,0.2); }
        .btn-edit { border: 1px solid #00d4ff; color: #00d4ff; box-shadow: 0 0 10px rgba(0,212,255,0.2); }
        .btn-create { border: 1px solid #8a2be2; color: #8a2be2; box-shadow: 0 0 10px rgba(138,43,226,0.2); }
        .btn-upload { border: 1px solid #ff4d4d; color: #ff4d4d; box-shadow: 0 0 10px rgba(255,77,77,0.2); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 8px; color: #a0c4ff; font-size: 13px; }
        .form-control { width: 100%; box-sizing: border-box; background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(0, 212, 255, 0.3); color: white; padding: 12px 15px; border-radius: 12px; font-family: Tahoma; font-size: 14px; outline: none; transition: 0.3s; }
        .form-control:focus { border-color: #00d4ff; box-shadow: 0 0 10px rgba(0,212,255,0.3); }
        textarea.form-control { resize: none; min-height: 90px; }
        .submit-btn { width: 100%; background: linear-gradient(90deg, #00d4ff, #0055ff); color: white; border: none; padding: 15px; border-radius: 15px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; box-shadow: 0 5px 15px rgba(0,212,255,0.3); transition: 0.3s; }
        .submit-btn:active { transform: scale(0.98); }
        #realImageInput { display: none; }
    </style>
</head>
<body>
    <div class="glass-panel">
        <div class="header-title"><span style="font-size: 24px;">➕</span> افزودن محصول جدید</div>
        <div class="ai-grid">
            <div class="ai-btn btn-img" onclick="document.getElementById('realImageInput').click()"><i>📸</i> آپلود عکس</div>
            <div class="ai-btn btn-emoji"><i>😋</i> ایموجی</div>
            <div class="ai-btn btn-text"><i>🤖</i> قوی‌سازی متن</div>
            <div class="ai-btn btn-edit"><i>✨</i> تغییر با AI</div>
            <div class="ai-btn btn-create" onclick="alert('به هوش مصنوعی وصل می‌شود')"><i>🎨</i> ساخت با AI</div>
            <div class="ai-btn btn-upload" onclick="document.getElementById('realImageInput').click()"><i>📁</i> از گوشی</div>
        </div>
        <form method="POST" enctype="multipart/form-data" action="/panel/add-product">
            <input type="file" id="realImageInput" name="image" accept="image/*">
            <div class="form-group"><label>📦 نام محصول</label><input type="text" name="name" class="form-control" placeholder="مثلاً سیب قرمز" required></div>
            <div class="form-group"><label>💰 قیمت (تومان)</label><input type="number" name="price" class="form-control" placeholder="مثلاً ۵۰۰۰۰" required></div>
            <div class="form-group"><label>📝 توضیحات (اختیاری)</label><textarea name="description" class="form-control" placeholder="توضیح کوتاه..."></textarea></div>
            <button type="submit" class="submit-btn">💾 ثبت محصول</button>
        </form>
    </div>
</body>
</html>"""

found = False
for filepath in glob.glob('templates/**/*.html', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # پیدا کردن فایلی که این متن توش هست (همون صفحه‌ای که توی عکس بود)
    if 'ساخت عکس با هوش مصنوعی' in content or 'افزودن محصول جدید' in content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f"✅ فایل اصلی پیدا شد و بازنویسی شد: {filepath}")
        found = True
        break

if not found:
    print("⚠️ فایل پیدا نشد! شاید اسم دکمه توی HTML تو فرق داره.")
