import requests, json
from database import get_bot_token

creds = get_bot_token(1)
if not creds or not creds.get('token'):
    print("❌ توکن ذخیره نشده")
    exit()

token = creds['token']
print(f"🔑 طول توکن: {len(token)}")
print(f"📱 پیام‌رسان: {creds.get('messenger')}")
print(f"📢 کانال: {creds.get('channel') or '(خالی)'}")
print("=" * 50)

# تست ۱: getMe
print("\n1️⃣ GET getMe:")
try:
    r = requests.get(f"https://botapi.rubika.ir/v3/{token}/getMe", timeout=10)
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text[:400]}")
except Exception as e:
    print(f"   ❌ {e}")

print("\n2️⃣ POST getMe:")
try:
    r = requests.post(f"https://botapi.rubika.ir/v3/{token}/getMe", timeout=10)
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text[:400]}")
except Exception as e:
    print(f"   ❌ {e}")

print("\n3️⃣ POST getUpdates:")
try:
    r = requests.post(f"https://botapi.rubika.ir/v3/{token}/getUpdates", timeout=15)
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text[:600]}")
except Exception as e:
    print(f"   ❌ {e}")

print("\n" + "=" * 50)
print("✅ دیاگنوستیک تموم شد")
