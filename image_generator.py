import os
import time
import requests

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
API_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"

def generate_image(prompt: str, max_retries: int = 3, timeout: int = 60) -> bytes:
    if not HF_TOKEN:
        raise RuntimeError("توکن HF_TOKEN تنظیم نشده است.")
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    }
    payload = {"inputs": prompt}
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.content
            if response.status_code in [429, 503]:
                time.sleep((attempt + 1) * 5)
                continue
            response.raise_for_status()
        except requests.exceptions.Timeout:
            time.sleep(5)
    raise RuntimeError("ساخت عکس با شکست مواجه شد.")
