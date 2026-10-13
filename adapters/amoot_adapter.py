import os
import requests

AMOOT_TOKEN = os.environ.get('AMOOT_TOKEN', '')
AMOOT_URL = 'https://portal.amootsms.com/rest/SendSimple'

def send_sms(mobile, message):
    """ارسال پیامک با آموت"""
    if not AMOOT_TOKEN:
        return False, 'توکن آموت تنظیم نشده'
    try:
        payload = {
            'token': AMOOT_TOKEN,
            'Mobiles': mobile,
            'SendDateTime': '0',
            'SMSMessageText': message,
            'LineNumber': 'Public',
        }
        r = requests.post(AMOOT_URL, data=payload, timeout=15)
        data = r.json()
        if data.get('Status') == 1:
            return True, data
        return False, data.get('Message', 'خطای نامشخص')
    except Exception as e:
        return False, str(e)

def check_balance():
    """چک اعتبار"""
    if not AMOOT_TOKEN:
        return None
    try:
        r = requests.get(
            'https://portal.amootsms.com/rest/AccountStatus',
            params={'token': AMOOT_TOKEN}, timeout=15)
        return r.json()
    except Exception as e:
        return {'error': str(e)}
