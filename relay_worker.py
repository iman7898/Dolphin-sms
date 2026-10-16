"""🔄 Relay Worker — فوروارد خودکار از کانال منبع به مقصد"""
import time, sqlite3, requests, sys
from datetime import datetime

BASE = "https://botapi.rubika.ir/v3"
DB = "panel.db"

def db():
    return sqlite3.connect(DB, timeout=15)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_config():
    """گرفتن توکن + کانال‌ها"""
    conn = db(); c = conn.cursor()
    # توکن
    c.execute("SELECT token, messenger FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    if not r:
        conn.close()
        return None
    token, messenger = r
    # تنظیمات AI
    c.execute("""SELECT rubika_channel_id, target_channel, source_channels, content_keywords
                 FROM ai_channel_config WHERE user_id=1 LIMIT 1""")
    r2 = c.fetchone()
    conn.close()
    if not r2:
        return None
    channel_id, target, sources_raw, keywords_raw = r2
    sources = [s.strip() for s in (sources_raw or '').split(',') if s.strip()]
    keywords = [k.strip() for k in (keywords_raw or '').split(',') if k.strip()]
    real_target = (target or channel_id or '').strip()
    return {
        'token': token,
        'messenger': messenger,
        'channel_id': (channel_id or '').strip(),
        'target': real_target,
        'sources': sources,
        'keywords': keywords,
    }

def send(token, chat_id, text):
    try:
        r = requests.post(f"{BASE}/{token}/sendMessage",
                          json={'chat_id': str(chat_id), 'text': text}, timeout=20)
        return r.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_updates(token, offset=None):
    try:
        d = {'offset_id': offset} if offset else {}
        r = requests.post(f"{BASE}/{token}/getUpdates", json=d, timeout=20)
        return r.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def main():
    log("🔄 Relay Worker v1.0")
    cfg = get_config()
    if not cfg:
        log("❌ تنظیمات پیدا نشد")
        return
    log(f"✅ پیام‌رسان: {cfg['messenger']}")
    log(f"✅ مقصد: {cfg['target']}")
    log(f"✅ منابع: {', '.join(cfg['sources']) or 'خالی'}")
    log(f"✅ کلیدواژه: {', '.join(cfg['keywords']) or 'همه'}")
    
    # تست ارسال به مقصد
    test_msg = "🔄 Relay فعال شد"
    r = send(cfg['token'], cfg['target'], test_msg)
    log(f"📤 تست ارسال: {r.get('status', 'unknown')} - {r.get('dev_message', r.get('message', ''))}")
    
    offset = None
    log("⏳ در حال گوش دادن به پیام‌ها...")
    while True:
        try:
            r = get_updates(cfg['token'], offset)
            if r.get('status') == 'OK':
                updates = r.get('result', {}).get('updates', []) or r.get('updates', [])
                for u in updates:
                    if 'new_message' in u:
                        nm = u['new_message']
                        cid = str(u.get('chat_id', ''))
                        text = nm.get('text', '')
                        # چک کن از کانال منبع باشه
                        is_source = False
                        for src in cfg['sources']:
                            src_clean = src.lstrip('@').lower()
                            if src_clean in cid.lower() or src.lower() in cid.lower():
                                is_source = True
                                break
                        if is_source and text:
                            log(f"📥 پیام از {cid}: {text[:50]}")
                            # فیلتر کلیدواژه
                            if cfg['keywords']:
                                if not any(k in text for k in cfg['keywords']):
                                    log("⏭ کلیدواژه مچ نشد")
                                    continue
                            # فوروارد
                            fr = send(cfg['token'], cfg['target'], text)
                            log(f"📤 فوروارد: {fr.get('status', 'unknown')}")
                    if 'new_message' in u:
                        mid = nm.get('message_id')
                        if mid:
                            offset = mid
            time.sleep(3)
        except KeyboardInterrupt:
            log("⏹ خروج")
            break
        except Exception as e:
            log(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
