import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# پیدا کردن آدرس Pollinations و تزریق مدل Flux
url_pattern = r'(https://image\.pollinations\.ai/prompt/[^\"\'\s]+)'
def fix_url(match):
    url = match.group(1)
    if '?' not in url: url += '?'
    else: url += '&'
    if 'model=flux' not in url: url += 'model=flux&nologo=true&width=1024&height=1024'
    return url

new_code = re.sub(url_pattern, fix_url, code)

if new_code == code:
    print("⚠️ آدرس هوش مصنوعی پیدا نشد (شاید اسم فایل فرق داره).")
else:
    print("✅ هوش مصنوعی با موفقیت به مدل فوق‌قوی Flux ارتقا پیدا کرد!")
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_code)
