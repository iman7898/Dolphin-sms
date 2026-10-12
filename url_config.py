"""URL Config - خواندن آدرس عمومی از فایل یا IP"""
import os

CONFIG_FILE = os.path.expanduser("~/otp_panel/public_url.txt")


def get_public_url():
    """آدرس عمومی رو از فایل می‌خونه"""
    # ۱) از فایل
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                url = f.read().strip()
                if url:
                    return url.rstrip("/")
        except: pass

    # ۲) از متغیر محیطی
    env = os.environ.get("PUBLIC_URL", "").strip()
    if env:
        return env.rstrip("/")

    # ۳) Tailscale IP
    try:
        import subprocess
        r = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            ip = r.stdout.strip().split("\n")[0]
            return "http://" + ip + ":8080"
    except: pass

    # ۴) IP شبکه (لوکال)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return "http://" + ip + ":8080"
    except: pass

    # ۵) پیش‌فرض
    return "http://localhost:8080"


def set_public_url(url):
    """ذخیره آدرس عمومی"""
    with open(CONFIG_FILE, "w") as f:
        f.write(url.strip().rstrip("/"))


# آدرس‌های مشتق
def get_panel_url():
    return get_public_url() + "/customer"

def get_shop_url():
    return get_public_url() + "/panel/login"

def get_register_url():
    return get_public_url() + "/customer/register"
