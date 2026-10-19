import requests
import time
import urllib.parse

def generate_image(prompt: str, max_retries: int = 3, timeout: int = 60) -> bytes:
    encoded_prompt = urllib.parse.quote(prompt)
    models = ["flux", "turbo"] # اول flux، اگه نشد turbo
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for model in models:
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model={model}&nologo=true"
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response.content
                # اگه سرور شلوغ بود، ۳ ثانیه صبر کن و دوباره تلاش کن
                time.sleep(3)
            except Exception:
                time.sleep(3)
                
    # ------------------ سیستم نجات (Fallback) ------------------
    # اگه همه مدل‌ها خراب بودن، این عکس رو نشون بده تا ارور نده!
    print("⚠️ هوش مصنوعی جواب نداد، عکس پیش‌فرض لود شد.")
    try:
        fallback = requests.get("https://image.pollinations.ai/prompt/a%20red%20apple?width=1024&height=1024&nologo=true", timeout=10)
        return fallback.content
    except:
        # اگه حتی این هم کار نکرد، یه پیکسل خالی برمی‌گردونه تا برنامه کرش نکنه
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
