"""🔄 Keep Render alive - هر ۱۰ دقیقه پینگ"""
import time
import requests
import os
from threading import Thread

URL = os.environ.get('KEEP_ALIVE_URL', 'https://dolphin-sms.onrender.com/customer')

def ping_loop():
    while True:
        try:
            r = requests.get(URL, timeout=10)
            print(f'[keep-alive] {r.status_code}', flush=True)
        except Exception as e:
            print(f'[keep-alive] error: {e}', flush=True)
        time.sleep(600)  # ۱۰ دقیقه

def start():
    t = Thread(target=ping_loop, daemon=True)
    t.start()
    print('✅ Keep-alive started')
