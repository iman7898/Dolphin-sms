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
AMOOT_LINE = os.environ.get('AMOOT_LINE', 'Public')


def _normalize_phone(m):
    """اصلاح فرمت شماره موبایل"""
    m = (m or '').strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if m.startswith('+98'): m = '0' + m[3:]
    elif m.startswith('0098'): m = '0' + m[4:]
    elif m.startswith('98') and len(m) == 12: m = '0' + m[2:]
    elif m.startswith('9') and len(m) == 10: m = '0' + m
    return m


def _is_success(data):
    """چک موفقیت به هر فرمتی"""
    if not isinstance(data, dict):
        return False
    # فرمت ۱: Status=1
    if data.get('Status') == 1:
        return True
    # فرمت ۲: Status='Success'
    st = data.get('Status') or data.get('status')
    if isinstance(st, str) and st.lower() == 'success':
        return True
    # فرمت ۳: Data[0].Status.Success
    arr = data.get('Data') or data.get('data') or []
    if isinstance(arr, list) and arr:
        first = arr[0]
        if isinstance(first, dict):
            inner = first.get('Status')
            if isinstance(inner, dict) and inner.get('Success'):
                return True
            if isinstance(inner, str) and inner.lower() == 'success':
                return True
    return False


def _get_error(data):
    """استخراج پیام خطا"""
    if not isinstance(data, dict):
        return str(data)[:200]
    for k in ['Message', 'message', 'Error', 'error']:
        v = data.get(k)
        if v: return str(v)[:200]
    return str(data)[:200]


def send_sms(mobile, message):
    if not AMOOT_TOKEN:
        return {"status": "error", "message": "توکن آموت تنظیم نشده"}
    mob = _normalize_phone(mobile)
    if not mob or len(mob) != 11 or not mob.startswith('09'):
        return {"status": "error", "message": f"شماره نامعتبر: {mobile}"}
    try:
        payload = {
            'token': AMOOT_TOKEN,
            'Mobiles': mob,
            'SendDateTime': '0',
            'SMSMessageText': message,
            'LineNumber': AMOOT_LINE,
        }
        r = requests.post(AMOOT_URL, data=payload, timeout=20)
        try:
            data = r.json()
        except Exception:
            return {"status": "error", "message": f"پاسخ نامعتبر: {r.text[:200]}"}
        if _is_success(data):
            return {"status": "success", "response": data, "phone": mob}
        return {"status": "error", "message": _get_error(data)}
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}


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
