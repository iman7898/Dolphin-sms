import requests
import urllib.parse


def ask_ai(prompt, system=''):
    """چت AI با Pollinations"""
    if not prompt or not prompt.strip():
        return None
    if not system:
        system = "You are a helpful Persian assistant. Reply in Persian."
    prompt = prompt.strip()

    # GET ساده
    try:
        enc = urllib.parse.quote(prompt)
        r = requests.get("https://text.pollinations.ai/" + enc,
                        timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            t = r.text.strip()
            if t and len(t) > 2 and "credit" not in t.lower():
                return t
    except: pass

    # GET با system
    try:
        full = system + "\n\n" + prompt
        enc = urllib.parse.quote(full)
        r = requests.get("https://text.pollinations.ai/" + enc + "?model=openai",
                        timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            t = r.text.strip()
            if t and len(t) > 2 and "credit" not in t.lower():
                return t
    except: pass

    # POST
    try:
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}]}, timeout=35)
        if r.status_code == 200:
            t = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if t and len(t) > 2:
                return t
    except: pass

    return None


def enhance_for_channel(text):
    """قوی‌سازی متن + افزودن ایموجی هوشمند برای کانال"""
    if not text or not text.strip():
        return None
    system = """تو یه ادمین حرفه‌ای کانال تلگرام/روبیکا هستی.
متن کاربر رو بگیر و به یه پست جذاب و حرفه‌ای تبدیل کن.

قوانین:
1. متن رو قوی‌تر و جذاب‌تر کن
2. ایموجی‌های مناسب و مرتبط اضافه کن (نه زیاد، نه کم)
3. پاراگراف‌بندی کن
4. CTA (دعوت به اقدام) اضافه کن اگه مناسب بود
5. هشتگ‌های مرتبط اضافه کن
6. فارسی روان و طبیعی بنویس
7. طول متن رو حداکثر ۲ برابر کن
8. فقط متن نهایی رو برگردون، هیچ توضیح اضافه‌ای نده"""
    return ask_ai(text, system)


def suggest_emoji(word):
    """پیشنهاد ایموجی برای کلمه"""
    if not word:
        return '📌'
    system = """فقط یه ایموجی مناسب برای کلمه‌ای که کاربر می‌گه برگردون.
فقط خود ایموجی، هیچ چیز دیگه. مثلا: پرتغال → 🍊"""
    result = ask_ai(word, system)
    if result:
        result = result.strip()
        # فقط ایموجی
        import re as _re
        emojis = _re.findall(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF]', result)
        if emojis:
            return emojis[0]
    # fallback
    fallback = {
        'پرتغال': '🍊', 'سیب': '🍎', 'موز': '🍌', 'انگور': '🍇',
        'هندوانه': '🍉', 'توت': '🍓', 'نارگیل': '🥥', 'آناناس': '🍍',
        'گوشت': '🥩', 'مرغ': '🍗', 'ماهی': '🐟', 'تخم': '🥚',
        'شیر': '🥛', 'ماست': '🥣', 'پنیر': '🧀', 'کره': '🧈',
        'نان': '🍞', 'برنج': '🍚', 'ماکارونی': '🍝',
        'چای': '🍵', 'قهوه': '☕', 'آب': '💧', 'نوشابه': '🥤',
        'کیک': '🍰', 'شکلات': '🍫', 'بستنی': '🍦', 'شیرینی': '🍪',
        'لباس': '👕', 'کفش': '👟', 'کیف': '👜',
        'گل': '🌸', 'کتاب': '📚', 'موسیقی': '🎵',
    }
    for k, v in fallback.items():
        if k in word:
            return v
    return '📌'
