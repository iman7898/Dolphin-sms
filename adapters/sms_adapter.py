"""آداپتر هوشمند پیامک: اگه AMOOT_TOKEN باشه آموت، وگرنه MCI"""
import os

AMOOT_TOKEN = os.environ.get('AMOOT_TOKEN', '').strip()
if not AMOOT_TOKEN:
    try:
        from config import AMOOT_TOKEN as _cfg_token
        AMOOT_TOKEN = (_cfg_token or '').strip()
    except ImportError:
        pass

if AMOOT_TOKEN and not AMOOT_TOKEN.startswith('PUT-'):
    from adapters.amoot_adapter import send_sms as _amoot_send, check_balance as _amoot_balance
    def send_sms(mobile, message):
        return _amoot_send(mobile, message)
    def check_balance():
        return _amoot_balance()
    print(f"✅ SMS: Amoot فعال (token len={len(AMOOT_TOKEN)})")
else:
    from adapters.mci_adapter import send_sms as _mci_send, check_balance as _mci_balance
    def send_sms(mobile, message):
        return _mci_send(mobile, message)
    def check_balance():
        return _mci_balance()
    print("⚠️ SMS: MCI (TEST MODE) - چون AMOOT_TOKEN تنظیم نشده")
