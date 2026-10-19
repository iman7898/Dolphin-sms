import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()
if "from image_generator import generate_image" not in code:
    code = "from image_generator import generate_image\n" + code
pattern = r"requests\.(get|post)\([^)]*pollinations\.ai[^)]*\)"
if re.search(pattern, code):
    code = re.sub(pattern, "image_bytes = generate_image(prompt)", code)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ فایل app.py اصلاح شد.")
