"""📤 آپلود و ارسال فایل به روبیکا"""
import requests
import os
import mimetypes

BASE = "https://botapi.rubika.ir/v3"


def upload_and_send_file(tok, chat_id, file_path, caption=''):
    """آپلود فایل + ارسال به کانال"""
    if not os.path.exists(file_path):
        return {'status': 'error', 'message': f'file not found: {file_path}'}

    # تشخیص نوع فایل
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'image/jpeg'

    # ۱) گرفتن URL آپلود
    try:
        r1 = requests.post(f'{BASE}/{tok}/requestSendFile',
                           json={'type': 'Image'}, timeout=20)
        d1 = r1.json()
        if d1.get('status') != 'OK':
            return {'status': 'error', 'message': 'requestSendFile: ' + str(d1)[:200]}
        upload_url = d1.get('data', {}).get('upload_url')
        if not upload_url:
            return {'status': 'error', 'message': 'no upload_url'}
    except Exception as e:
        return {'status': 'error', 'message': 'step1: ' + str(e)[:200]}

    # ۲) آپلود فایل
    try:
        with open(file_path, 'rb') as f:
            fname = os.path.basename(file_path)
            files = {'file': (fname, f, mime_type)}
            r2 = requests.post(upload_url, files=files, timeout=60)
        d2 = r2.json()
        if d2.get('status') != 'OK':
            return {'status': 'error', 'message': 'upload: ' + str(d2)[:200]}
        file_id = d2.get('data', {}).get('file_id')
        if not file_id:
            return {'status': 'error', 'message': 'no file_id'}
    except Exception as e:
        return {'status': 'error', 'message': 'step2: ' + str(e)[:200]}

    # ۳) ارسال به کانال
    try:
        r3 = requests.post(f'{BASE}/{tok}/sendFile',
                           json={'chat_id': chat_id, 'file_id': file_id, 'text': caption},
                           timeout=30)
        return r3.json()
    except Exception as e:
        return {'status': 'error', 'message': 'step3: ' + str(e)[:200]}
