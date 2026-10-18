"""📤 آپلود و ارسال فایل به روبیکا (نسخه نهایی و قطعی)"""
import requests
import os
import io
import re
from PIL import Image

BASE = "https://botapi.rubika.ir/v3"

def upload_and_send_file(tok, chat_id, file_path, caption=''):
    if not os.path.exists(file_path):
        return {'status': 'error', 'message': f'file not found: {file_path}'}

    # 🚨 فیلتر قوی: فقط حروف انگلیسی و عدد رو نگه می‌داره، بعد @ میذاره اولش
    clean_id = re.sub(r'[^a-zA-Z0-9_]', '', chat_id)
    if clean_id.startswith('-') or clean_id.isdigit():
        chat_id = '-' + clean_id  # برای کانال‌های خصوصی
    else:
        chat_id = '@' + clean_id

    try:
        img = Image.open(file_path).convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        file_data = buf
        fname = 'image.jpg'
    except Exception as e:
        return {'status': 'error', 'message': f'خطای تبدیل عکس: {e}'}

    # ۱. گرفتن لینک آپلود
    try:
        r1 = requests.post(f'{BASE}/{tok}/requestSendFile', json={'type': 'Image'}, timeout=20)
        d1 = r1.json()
        if d1.get('status') != 'OK':
            return {'status': 'error', 'message': f'خطای لینک: {d1}'}
        upload_url = d1.get('data', {}).get('upload_url')
    except Exception as e:
        return {'status': 'error', 'message': f'خطای شبکه ۱: {e}'}

    # ۲. آپلود به روبیکا
    try:
        files = {'file': (fname, file_data, 'image/jpeg')}
        r2 = requests.post(upload_url, files=files, timeout=60)
        d2 = r2.json()
        if d2.get('status') != 'OK':
            return {'status': 'error', 'message': f'خطای آپلود: {d2}'}
        file_id = d2.get('data', {}).get('file_id')
    except Exception as e:
        return {'status': 'error', 'message': f'خطای شبکه ۲: {e}'}

    # ۳. ارسال
    try:
        r3 = requests.post(f'{BASE}/{tok}/sendFile',
                           json={'chat_id': chat_id, 'file_id': file_id, 'text': caption},
                           timeout=30)
        d3 = r3.json()
        if d3.get('status') != 'OK':
            return {'status': 'error', 'message': str(d3)}
        return d3
    except Exception as e:
        return {'status': 'error', 'message': f'خطای شبکه ۳: {e}'}
