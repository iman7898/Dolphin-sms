import requests
BASE = "https://api.splus.ir/bot"

class SoroushBot:
    def __init__(self, token):
        self.token = token
        self.base = BASE + token
    def _post(self, method, data=None):
        try:
            r = requests.post(self.base + "/" + method, json=data or {}, timeout=20)
            try: return r.json()
            except: return {"ok": False}
        except: return {"ok": False}
    def _get(self, method, params=None):
        try:
            r = requests.get(self.base + "/" + method, params=params or {}, timeout=20)
            try: return r.json()
            except: return {"ok": False}
        except: return {"ok": False}
    def get_me(self): return self._get("getMe")
    def send_message(self, chat_id, text):
        return self._post("sendMessage", {"chat_id": str(chat_id), "text": text})
    def get_updates(self, offset=None):
        p = {"timeout": 5}
        if offset: p["offset"] = offset
        return self._get("getUpdates", p)
    def is_ok(self, r): return r and r.get("ok") is True
