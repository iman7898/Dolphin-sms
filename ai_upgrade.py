import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# پیدا کردن تابع یا بخشی که به Pollinations وصل میشه
if 'pollinations.ai' in code:
    print("🔍 سرویس هوش مصنوعی پیدا شد. در حال ارتقا به سطح ChatGPT...")
    
    # تغییر مدل به flux-realism (واقع گرایانه) و اضافه کردن پارامترهای کیفیت
    # ما از مدل flux استفاده می‌کنیم چون از openai پایدارتره و ارور کمتری میده
    code = code.replace("model=flux", "model=flux-realism")
    code = code.replace("model=openai", "model=flux-realism")
    
    # اگر مدلی تعریف نشده بود، پیش‌فرض رو قوی کن
    if 'model=flux-realism' not in code:
        code = code.replace("nologo=true", "model=flux-realism&nologo=true")
        code = code.replace("prompt/{prompt}", "prompt/{prompt}?width=1024&height=1024&model=flux-realism&nologo=true")
        # جلوگیری از تکرار علامت سوال
        code = code.replace("??", "?")
        code = code.replace("?&", "?")

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("✅ مدل هوش مصنوعی به Flux-Realism تغییر کرد.")
else:
    print("⚠️ سرویس pollinations در app.py پیدا نشد.")
