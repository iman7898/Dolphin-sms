import os, glob

# کد HTML دقیقاً کپی شده از تم صفحه کانال خودت
matched_html = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>افزودن محصول | دلفین</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Tahoma, Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        
        body { 
            background-color: #031526; 
            color: white; 
            padding: 15px; 
            min-height: 100vh;
            display: flex; 
            justify-content: center; 
        }
        
        /* کادر اصلی با استایل دقیق صفحه کانال */
        .main-box { 
            width: 100%; 
            max-width: 500px; 
            background: #06213b; /* رنگ پس زمینه کادر */
            border: 1.5px solid #00a8ff; /* حاشیه آبی */
            border-radius: 20px; 
            padding: 20px; 
            box-shadow: 0 0 15px rgba(0,168,255,0.2), inset 0 0 15px rgba(0,168,255,0.1); 
            margin-top: 10px;
        }

        .header-title { 
            text-align: center; 
            color: #00d4ff; 
            font-size: 18px; 
            font-weight: bold;
            margin-bottom: 20px; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            gap: 10px; 
        }

        /* گرید ۶ دکمه ای دقیقا مثل عکس */
        .btn-grid { 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 12px; 
            margin-bottom: 25px; 
        }

        .grid-btn { 
            background: rgba(0, 0, 0, 0.2); 
            border-radius: 12px; 
            padding: 15px 5px; 
            text-align: center; 
            font-size: 13px; 
            font-weight: bold; 
            cursor: pointer; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            gap: 8px; 
            transition: 0.3s;
        }
        .grid-btn:active { transform: scale(0.95); }
        .grid-btn i { font-size: 22px; font-style: normal; }

        /* رنگ بندی دکمه ها مطابق عکس */
        .c-green { border: 1.5px solid #00ff88; color: #00ff88; box-shadow: 0 0 10px rgba(0,255,136,0.1); }
        .c-yellow { border: 1.5px solid #ffd700; color: #ffd700; box-shadow: 0 0 10px rgba(255,215,0,0.1); }
        .c-purple { border: 1.5px solid #b100ff; color: #b100ff; box-shadow: 0 0 10px rgba(177,0,255,0.1); }
        .c-blue { border: 1.5px solid #00d4ff; color: #00d4ff; box-shadow: 0 0 10px rgba(0,212,255,0.1); }
        .c-pink { border: 1.5px solid #ff69b4; color: #ff69b4; box-shadow: 0 0 10px rgba(255,105,180,0.1); }
        .c-teal { border: 1.5px solid #20b2aa; color: #20b2aa; box-shadow: 0 0 10px rgba(32,178,170,0.1); }

        /* فرم ها */
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 8px; color: #fff; font-size: 14px; font-weight: bold; }
        
        .form-control { 
            width: 100%; 
            background: #031526; /* پس زمینه تیره */
            border: 1.5px solid #00a8ff; /* حاشیه آبی */
            color: white; 
            padding: 12px 15px; 
            border-radius: 12px; 
            font-family: Tahoma; 
            font-size: 14px; 
            outline: none; 
            transition: 0.3s;
        }
        .form-control::placeholder { color: #777; }
        .form-control:focus { border-color: #00d4ff; box-shadow: 0 0 10px rgba(0,212,255,0.3); }
        
        textarea.form-control { resize: none; min-height: 90px; }

        /* دکمه ثبت نهایی (سبز/آبی مثل دکمه ارسال کانال) */
        .submit-btn { 
            width: 100%; 
            background: linear-gradient(90deg, #00b4db, #0083b0); 
            color: white; 
            border: none; 
            padding: 15px; 
            border-radius: 12px; 
            font-size: 16px; 
            font-weight: bold; 
            cursor: pointer; 
            margin-top: 10px; 
            box-shadow: 0 4px 15px rgba(0,180,219,0.3); 
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            transition: 0.3s;
        }
        .submit-btn:active { transform: scale(0.98); }

        #realImageInput { display: none; }
    </style>
</head>
<body>

    <div class="main-box">
        <div class="header-title">
            <span>➕</span> افزودن محصول جدید
        </div>

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
            <div class="grid-btn c-teal" onclick="document.getElementById('realImageInput').click()">
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
</html>"""

found = False
for filepath in glob.glob('templates/**/*.html', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # پیدا کردن دقیق صفحه افزودن محصول
    if 'ساخت عکس با هوش مصنوعی' in content or 'افزودن محصول جدید' in content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(matched_html)
        print(f"✅ فایل اصلی پیدا شد و دقیقاً مثل صفحه کانال بازنویسی شد: {filepath}")
        found = True
        break

if not found:
    print("⚠️ فایل پیدا نشد!")
