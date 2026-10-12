import requests
from config import MCI_API_URL, MCI_API_KEY, MCI_SENDER, TEST_MODE

def send_sms(phone, message):
    if TEST_MODE:
        print(f"[TEST MODE] به {phone} پیامک: {message}")
        return {"status": "success", "test_mode": True, "phone": phone}
    headers = {"Authorization": f"Bearer {MCI_API_KEY}", "Content-Type": "application/json"}
    payload = {"sender": MCI_SENDER, "receptor": phone, "message": message}
    try:
        r = requests.post(MCI_API_URL, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        return {"status": "success", "response": r.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_balance():
    if TEST_MODE:
        return {"balance": 1000, "test_mode": True}
    return {"balance": 0, "test_mode": False}
