import requests
import time
import urllib.parse

def generate_image(prompt: str, max_retries: int = 5, timeout: int = 60) -> bytes:
    encoded_prompt = urllib.parse.quote(prompt)
    # استفاده از مدل Flux (قوی‌ترین مدل رایگان) و سایز بالا
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.content
            elif response.status_code in [429, 500, 502, 503, 504]:
                print(f"⏳ سرور شلوغه، 10 ثانیه صبر می‌کنم... (تلاش {attempt+1})")
                time.sleep(10)
                continue
        except requests.exceptions.Timeout:
            print("⏳ تایم‌اوت، تلاش مجدد...")
            time.sleep(5)
            
    raise RuntimeError("ساخت عکس بعد از چند بار تلاش با شکست مواجه شد.")
