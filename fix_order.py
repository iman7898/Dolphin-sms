import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. پاک کردن مسیر موقتی که خودم ساخته بودم
code = re.sub(r"@app\.route\('/admin/', strict_slashes=False\)\s*def admin_recovered\(\):\s*return '<h1.*?</h1>'\n*", "", code, flags=re.DOTALL)

# 2. پیدا کردن بلوک app.run و انتقالش به آخر فایل
main_match = re.search(r"if __name__ == [\"']__main__[\"']:.*?app\.run\(.*?\)\n*", code, flags=re.DOTALL)
if main_match:
    main_block = main_match.group(0)
    code = code.replace(main_block, "") # از وسط کد حذفش کن
    code = code.strip() + "\n\n" + main_block + "\n" # بچسبونش آخر فایل

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ ترتیب کدها اصلاح شد و app.run به آخر رفت.")
