import os
file = 'app.py'
if not os.path.exists(file):
    print("❌ فایل app.py پیدا نشد!")
    exit()
with open(file, 'r', encoding='utf-8') as f:
    code = f.read()
with open(file + '.bak', 'w', encoding='utf-8') as f:
    f.write(code)

# رفع مشکل اسلش انتهایی
code = code.replace("@app.route('/admin/')", "@app.route('/admin/', strict_slashes=False)")
code = code.replace("@app.route('/admin')", "@app.route('/admin', strict_slashes=False)")

# اگه مسیر کلا پاک شده بود، برگردونش
if "'/admin'" not in code and "'/admin/'" not in code:
    print("⚠️ مسیر ادمین پاک شده بود! در حال بازسازی...")
    fallback = "\n@app.route('/admin/', strict_slashes=False)\ndef admin_recovered():\n    return '<h1 style=\"color:green;text-align:center;margin-top:50px;\">پنل ادمین بازیابی شد! کد اصلی رو برگردون.</h1>'\n"
    code = code.replace("if __name__", fallback + "\nif __name__")

with open(file, 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ فایل app.py اصلاح شد و بکاپ (app.py.bak) گرفته شد.")
