"""
آداپتر کاوه‌نگار — مستقیم با HTTP (بدون SDK)
فقط به requests نیاز داره که از قبل نصبه
"""
import requests
from config import MCI_API_KEY, MCI_SENDER, TEST_MODE

BASE_URL = "https://api.kavenegar.com/v1"


def send_sms(phone, message):
    if TEST_MODE:
        print(f"[TEST MODE] {phone}: {message}")
        return {"status": "success", "test_mode": True}

    if not MCI_API_KEY or MCI_API_KEY == "PUT-YOUR-KEY-HERE":
        return {"status": "error", "message": "کلید API تنظیم نشده"}

    url = f"{BASE_URL}/{MCI_API_KEY}/sms/send.json"
    data = {"receptor": phone, "message": message}
    if MCI_SENDER:
        data["sender"] = MCI_SENDER

    try:
        r = requests.post(url, data=data, timeout=20)
        j = r.json()
        status = j.get("return", {}).get("status")
        if status == 200:
            return {"status": "success", "response": j}
        return {
            "status": "error",
            "code": status,
            "message": j.get("return", {}).get("message", "خطای نامشخص")
        }
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "تایم‌اوت — اینترنت رو چک کن"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "خطای اتصال — اینترنت رو چک کن"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_otp(phone, code, template=None):
    """ارسال OTP با پترن کاوه‌نگار"""
    if TEST_MODE:
        print(f"[TEST MODE OTP] {phone}: {code}")
        return {"status": "success", "test_mode": True}

    if not MCI_API_KEY or MCI_API_KEY == "PUT-YOUR-KEY-HERE":
        return {"status": "error", "message": "کلید API تنظیم نشده"}

    url = f"{BASE_URL}/{MCI_API_KEY}/verify/lookup.json"
    data = {
        "receptor": phone,
        "token": str(code),
        "template": template or MCI_SENDER,
        "type": "sms",
    }

    try:
        r = requests.get(url, params=data, timeout=20)
        j = r.json()
        status = j.get("return", {}).get("status")
        if status == 200:
            return {"status": "success", "response": j}
        return {
            "status": "error",
            "code": status,
            "message": j.get("return", {}).get("message", "خطای نامشخص")
        }
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "تایم‌اوت — اینترنت رو چک کن"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "خطای اتصال"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_balance():
    if TEST_MODE:
        return {"balance": 1000, "test_mode": True}
    if not MCI_API_KEY or MCI_API_KEY == "PUT-YOUR-KEY-HERE":
        return {"balance": 0, "error": "کلید API تنظیم نشده"}
    url = f"{BASE_URL}/{MCI_API_KEY}/account/info.json"
    try:
        r = requests.get(url, timeout=15)
        j = r.json()
        entries = j.get("entries", {})
        return {"balance": entries.get("remainingcredit", 0)}
    except Exception as e:
        return {"balance": 0, "error": str(e)}
