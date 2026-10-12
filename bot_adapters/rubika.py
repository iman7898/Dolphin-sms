import requests
BASE = "https://botapi.rubika.ir/v3"

class RubikaBot:
    def __init__(self, token):
        self.token = token
        self.base = BASE + "/" + token
    def _post(self, method, data=None):
        try:
            r = requests.post(self.base + "/" + method, json=data or {}, timeout=20)
            try: return r.json()
            except: return {"status": "error"}
        except: return {"status": "error"}
    def get_me(self): return self._post("getMe")
    def send_message(self, chat_id, text):
        return self._post("sendMessage", {"chat_id": str(chat_id), "text": text})
    def get_updates(self, offset=None):
        d = {}
        if offset: d["offset_id"] = offset
        return self._post("getUpdates", d)
    def is_ok(self, r): return r and r.get("status") == "OK"
