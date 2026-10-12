import requests
import urllib.parse


def ask_ai(prompt, system=''):
    """چت AI با Pollinations"""
    if not prompt or not prompt.strip():
        return None
    if not system:
        system = "You are a helpful Persian assistant. Reply in Persian."
    prompt = prompt.strip()

    # GET ساده
    try:
        enc = urllib.parse.quote(prompt)
        r = requests.get("https://text.pollinations.ai/" + enc,
                        timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            t = r.text.strip()
            if t and len(t) > 2 and "credit" not in t.lower():
                return t
    except: pass

    # GET با system
    try:
        full = system + "\n\n" + prompt
        enc = urllib.parse.quote(full)
        r = requests.get("https://text.pollinations.ai/" + enc + "?model=openai",
                        timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            t = r.text.strip()
            if t and len(t) > 2 and "credit" not in t.lower():
                return t
    except: pass

    # POST
    try:
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}]}, timeout=35)
        if r.status_code == 200:
            t = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if t and len(t) > 2:
                return t
    except: pass

    return None
