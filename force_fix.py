import os, re
file = 'app.py'
if not os.path.exists(file):
    print("❌ فایل app.py پیدا نشد!")
    exit()
with open(file, 'r', encoding='utf-8') as f:
    code = f.read()

# پیدا کردن مسیرهای فعلی
routes = re.findall(r"@app\.route\(['\"](.*?)['\"]", code)
print("🔍 مسیرهایی که الان توی app.py هست:", routes)

# اگه مسیر ادمین کلاً نبود، به زور اضافه‌ش می‌کنیم
if not any('admin' in r for r in routes):
    print("⚠️ مسیر ادمین پیدا نشد! الان با زور اضافه‌ش می‌کنم...")
    inject = "\n\n# --- مسیر اجباری ادمین ---\n@app.route('/admin/', strict_slashes=False)\ndef forced_admin():\n    return '<h1 style=\"color:lime;text-align:center;margin-top:50px;font-family:tahoma;\">پنل ادمین با موفقیت بازیابی شد! (نسخه موقت)</h1>'\n# --------------------------\n\n"
    
    if "if __name__" in code:
        code = code.replace("if __name__", inject + "if __name__")
    else:
        code += inject
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(code)
    print("✅ مسیر ادمین با موفقیت به app.py تزریق شد.")
else:
    print("✅ مسیر ادمین از قبل وجود داره. مشکل احتمالاً از کدهای دیگه‌ست.")
