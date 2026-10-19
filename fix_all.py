import re
import os
if not os.path.exists('app.py'):
    print("❌ فایل app.py اصلا وجود نداره!")
    exit()
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()
print("\n🔍 لیست مسیرهای (Routes) فعلی توی app.py:")
routes = re.findall(r"@app\.route\(['\"](.*?)['\"]", code)
for r in routes:
    print("  ->", r)
if "/admin" not in routes and "/admin/" not in routes:
    print("\n⚠️ مسیر ادمین کلاً پاک شده بود! در حال ساخت مسیر موقت...")
    inject = "\n@app.route('/admin/', strict_slashes=False)\ndef temp_admin():\n    return '<h1 style=\"color:green;text-align:center;margin-top:50px;\">پنل ادمین موقت! کد اصلی رو برگردون.</h1>'\n"
    code += inject
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("✅ مسیر ادمین موقت اضافه شد.")
else:
    print("\n✅ مسیر ادمین توی فایل هست (مشکل از ران نشدن سرور بوده).")
