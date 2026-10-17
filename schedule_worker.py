"""⏰ Schedule Worker — اجرای پست‌های زمان‌بندی شده"""
import time, sqlite3, requests
from datetime import datetime

BASE = "https://botapi.rubika.ir/v3"

def db(): return sqlite3.connect('panel.db', timeout=15)
def log(m): print(f"[{datetime.now().strftime('%H:%M')}] {m}", flush=True)

def get_token():
    c = db().cursor()
    c.execute("SELECT token FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    return r[0] if r else None

def get_due():
    now = datetime.now()
    hm = now.strftime('%H:%M')
    weekday = now.weekday()  # 0=Mon, 5=Sat, 6=Sun
    c = db().cursor()
    c.execute("""SELECT id, shop_id, channel_id, headline, tag, days, last_run, image
                 FROM channel_schedule
                 WHERE active=1 AND post_time = ?""", (hm,))
    rows = c.fetchall()
    due = []
    for r in rows:
        sid, shop_id, ch, headline, tag, days, last_run = r
        # چک روز
        if days == 'weekdays' and weekday in (5, 6): continue
        if days == 'weekend' and weekday not in (5, 6): continue
        # چک اینکه امروز اجرا نشده
        if last_run:
            try:
                lr = datetime.fromisoformat(str(last_run).replace('Z',''))
                if lr.date() == now.date(): continue
            except: pass
        due.append(r)
    return due

def make_post(headline, tag=''):
    from ai_service import ask_ai
    system = """تو یه ادمین حرفه‌ای کانال هستی. یه سرفصل بهت می‌دم، تو یه پست کامل و جذاب بساز.

قوانین:
1. متن حرفه‌ای و کامل بنویس (۲ تا ۴ پاراگراف)
2. ایموجی‌های مناسب و مرتبط استفاده کن
3. تیتر جذاب بالای پست
4. اطلاعات مفید و دقیق
5. CTA (دعوت به اقدام) آخر پست
6. هشتگ‌های مرتبط
7. فقط متن پست رو برگردون"""
    body = ask_ai(headline, system)
    if not body:
        body = f"📌 {headline}\n\n{headline} یکی از مهم‌ترین موضوعات امروزه..."
    if tag:
        body += f'\n\n🏪 {tag}'
    return body

def send_post(tok, ch, text):
    try:
        r = requests.post(f'{BASE}/{tok}/sendMessage',
                          json={'chat_id': ch, 'text': text}, timeout=30)
        return r.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def mark_run(sid):
    conn = db(); c = conn.cursor()
    c.execute("UPDATE channel_schedule SET last_run=? WHERE id=?",
              (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), sid))
    conn.commit(); conn.close()

def log_run(sid, ch, headline, result, status):
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO channel_schedule_log (schedule_id, channel_id, headline, result, status) VALUES (?,?,?,?,?)",
              (sid, ch, headline, result[:500], status))
    conn.commit(); conn.close()





def send_with_photo(tok, ch, img, caption=''):
    """آپلود و ارسال عکس — روش درست"""
    from rubika_file import upload_and_send_file
    return upload_and_send_file(tok, ch, img.lstrip('/'), caption)


def main():
    log('⏰ Schedule Worker')
    log('✅ آماده')
    while True:
        try:
            tok = get_token()
            if not tok:
                time.sleep(60); continue
            due = get_due()
            for r in due:
                if len(r) == 8:
                    sid, shop_id, ch, headline, tag, days, last_run, img = r
                else:
                    sid, shop_id, ch, headline, tag, days, last_run = r
                    img = None
                log(f'📝 اجرا: {headline[:40]} → {ch}')
                body = make_post(headline, tag)
                # اگه عکس داشت
                if img:
                    rr = send_with_photo(tok, ch, img, body)
                else:
                    rr = send_post(tok, ch, body)
                if rr.get('status') == 'OK':
                    log(f'✅ ارسال شد')
                    log_run(sid, ch, headline, body, 'success')
                else:
                    err = rr.get('dev_message') or rr.get('message') or 'خطا'
                    log(f'❌ {err}')
                    log_run(sid, ch, headline, str(err), 'error')
                mark_run(sid)
            time.sleep(30)
        except KeyboardInterrupt: break
        except Exception as e:
            log(f'❌ {e}')
            time.sleep(30)

if __name__ == '__main__':
    main()
