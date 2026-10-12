import requests, time, random

phones = [
    "09121111111",
    "09122222222",
    "09123333333",
    "09124444444",
    "09125555555",
]

print("سنسور مجازی روشن شد. Ctrl+C برای توقف.")
print("-" * 40)

while True:
    phone = random.choice(phones)
    try:
        r = requests.post(
            "http://127.0.0.1:8080/api/trigger",
            json={"phone": phone, "location": "در ورودی"},
            timeout=5
        )
        print(f"OK {phone} -> {r.json().get('status')}")
    except Exception as e:
        print(f"ERROR: {e}")
    time.sleep(5)
