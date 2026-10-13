import os
import requests

AMOOT_TOKEN = os.environ.get('AMOOT_TOKEN', '').strip()
if not AMOOT_TOKEN:
    try:
        from config import AMOOT_TOKEN as _t
        AMOOT_TOKEN = (_t or '').strip()
    except Exception:
        pass

AMOOT_URL = 'https://portal.amootsms.com/rest/SendSimple'

def send_sms(mobile, message):
    if not AMOOT_TOKEN:
        return {"status": "error", "message": "توکن آموت تنظیم نشده"}
    try:
        payload = {
            'token': AMOOT_TOKEN,
            'Mobiles': mobile,
            'SendDateTime': '0',
            'SMSMessageText': message,
            'LineNumber': 'Public',
        }
        r = requests.post(AMOOT_URL, data=payload, timeout=15)
        # چک کن JSON باشه
        try:
            data = r.json()
        except Exception:
            return {"status": "error", "message": f"پاسخ نامعتبر: {r.text[:200]}"}
        # چک موفقیت
        status = data.get('Status') or data.get('status')
        if status == 1 or status == '1' or status == 'success':
            return {"status": "success", "response": data}
        return {"status": "error", "message": str(data)[:300]}
    except Exception as e:
        return {"status": "error", "message": str(e)[:300]}

def check_balance():
    if not AMOOT_TOKEN:
        return {"error": "توکن نیست"}
    try:
        r = requests.get(
            'https://portal.amootsms.com/rest/AccountStatus',
            params={'token': AMOOT_TOKEN}, timeout=15)
        return r.json()
    except Exception as e:
        return {'error': str(e)[:200]}
