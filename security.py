"""🔒 امنیت: Rate limiting + لاگ"""
from functools import wraps
from flask import request, jsonify, session
import time

# کش ساده در حافظه
_ATTEMPTS = {}  # {ip: [(time, path)]}
_LIMIT = 30  # حداکثر درخواست
_WINDOW = 60  # در ۶۰ ثانیه

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        now = time.time()
        # پاک کردن قدیمی‌ها
        attempts = [t for t in _ATTEMPTS.get(ip, []) if now - t < _WINDOW]
        attempts.append(now)
        _ATTEMPTS[ip] = attempts
        if len(attempts) > _LIMIT:
            return jsonify({'error': 'درخواست زیاد — ۶۰ ثانیه صبر کن'}), 429
        return f(*args, **kwargs)
    return decorated

def log_security(event, detail=''):
    """ثبت رویداد امنیتی"""
    print(f'[SECURITY] {event}: {detail}', flush=True)
