"""🤖 ربات ادمین کانال — محتوا + عضوآوری"""
import requests, sqlite3, time, re
from datetime import datetime

BASE = "https://botapi.rubika.ir/v3"

def db(): return sqlite3.connect("panel.db", timeout=15)
def log(m): print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)

def get_token():
    c = db().cursor()
    c.execute("SELECT token FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    return r[0] if r else None

def send(tok, cid, txt, kb=None):
    p = {'chat_id': str(cid), 'text': txt}
    if kb:
        p['chat_keypad'] = kb
        p['chat_keypad_type'] = 'New'
    try:
        return requests.post(f"{BASE}/{tok}/sendMessage", json=p, timeout=20).json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_updates(tok):
    try:
        return requests.post(f"{BASE}/{tok}/getUpdates", json={}, timeout=20).json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def kb_main():
    return {'rows': [
        {'buttons': [
            {'id': 'b_content', 'type': 'Simple', 'button_text': '📥 محتوا'},
            {'id': 'b_recruit', 'type': 'Simple', 'button_text': '👥 عضوآوری'},
        ]},
        {'buttons': [
            {'id': 'b_status', 'type': 'Simple', 'button_text': '📊 وضعیت'},
            {'id': 'b_help', 'type': 'Simple', 'button_text': '❓ راهنما'},
        ]},
    ]}

def get_config():
    c = db().cursor()
    try:
        c.execute("""SELECT rubika_channel_id, target_channel, source_channels,
                            content_keywords, recruit_target_count, recruit_message
                     FROM ai_channel_config WHERE user_id=1 LIMIT 1""")
        r = c.fetchone()
        if r:
            return {
                'main': (r[0] or '').strip(),
                'target': (r[1] or r[0] or '').strip(),
                'sources': [s.strip() for s in (r[2] or '').split(',') if s.strip()],
                'keywords': [k.strip() for k in (r[3] or '').split(',') if k.strip()],
                'recruit_target': r[4] or 1000,
                'recruit_msg': r[5] or 'به کانال ما بپیوندید!',
            }
    except Exception as e:
        log(f'cfg err: {e}')
    return None

def update_config(**kw):
    conn = db(); c = conn.cursor()
    for k, v in kw.items():
        c.execute(f"UPDATE ai_channel_config SET {k}=? WHERE user_id=1", (v,))
    conn.commit(); conn.close()

def set_active(state):
    conn = db(); c = conn.cursor()
    c.execute("UPDATE ai_channel_config SET active=? WHERE user_id=1", (1 if state else 0,))
    conn.commit(); conn.close()

def is_active():
    c = db().cursor()
    c.execute("SELECT active FROM ai_channel_config WHERE user_id=1")
    r = c.fetchone()
    return r and r[0] == 1

def is_owner(cid):
    """چک کن کاربر مالک رباته (ادمین)"""
    c = db().cursor()
    c.execute("SELECT id FROM users WHERE shop_image=?", (cid,))
    r = c.fetchone()
    if r: return True
    return False

def link_owner(cid, phone):
    c = db().cursor()
    c.execute("SELECT id FROM users WHERE phone=?", (phone,))
    r = c.fetchone()
    if not r: return None
    conn = db(); cc = conn.cursor()
    cc.execute("UPDATE users SET shop_image=? WHERE id=?", (cid, r[0]))
    conn.commit(); conn.close()
    return r[0]

# ذخیره آخرین پیام برای جلوگیری از تکرار
_last_seen = {}
SEEN_FILE = 'offsets/bot_admin_seen.txt'
import os
os.makedirs('offsets', exist_ok=True)

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            for line in f: _last_seen[line.strip()] = True
    except: pass

def save_seen(mid):
    _last_seen[mid] = True
    try:
        with open(SEEN_FILE, 'a') as f: f.write(mid + '\n')
    except: pass

# ═══════════════════════════════════════
# 🎯 پردازش
# ═══════════════════════════════════════

def handle_admin(tok, cid, txt, btn):
    t = (txt or '').strip()
    cfg = get_config()
    
    if btn == 'b_content' or t in ('محتوا', '📥 محتوا'):
        sources = ', '.join(cfg['sources']) if cfg and cfg['sources'] else '❌ تنظیم نشده'
        target = cfg['target'] if cfg and cfg['target'] else '❌ تنظیم نشده'
        keywords = ', '.join(cfg['keywords']) if cfg and cfg['keywords'] else 'همه'
        active = '🟢 فعال' if is_active() else '🔴 غیرفعال'
        send(tok, cid, f"""📥 وضعیت جمع‌آوری محتوا:

{active}

📤 منابع: {sources}
🎯 مقصد: {target}
🔍 کلیدواژه: {keywords}

━━━━━━━━━━━━━━
📝 دستورات:
• افزودن منبع [آیدی]
• حذف منبع [آیدی]
• تنظیم مقصد [آیدی]
• کلیدواژه [کلمه]
• روشن / خاموش""", kb_main())
        return
    
    if btn == 'b_recruit' or t in ('عضوآوری', '👥 عضوآوری'):
        target = cfg['recruit_target'] if cfg else 1000
        send(tok, cid, f"""👥 وضعیت عضوآوری:

🎯 هدف: {target} عضو
💬 پیام: {cfg['recruit_msg'][:60] if cfg else '-'}

━━━━━━━━━━━━━━
📝 دستورات:
• هدف [عدد]
• پیام [متن]""", kb_main())
        return
    
    if btn == 'b_status' or t in ('وضعیت', '📊 وضعیت'):
        active = '🟢 فعال' if is_active() else '🔴 غیرفعال'
        n_src = len(cfg['sources']) if cfg else 0
        send(tok, cid, f"""📊 وضعیت کلی:

🤖 ربات: {active}
📥 منابع: {n_src} کانال
🎯 مقصد: {cfg['target'] if cfg else '-'}

برای تنظیم، بنویس: راهنما""", kb_main())
        return
    
    if btn == 'b_help' or t in ('راهنما', '❓ راهنما', 'سلام', '/start', 'شروع', 'منو'):
        send(tok, cid, """🤖 ربات ادمین کانال

📥 جمع‌آوری محتوا:
• افزودن منبع @channel
• حذف منبع @channel
• تنظیم مقصد @mychannel
• کلیدواژه فروش, تخفیف
• روشن / خاموش

👥 عضوآوری:
• هدف 1000
• پیام سلام به کانال ما بپیوندید

📊 وضعیت

🔗 اتصال: [شماره]""", kb_main())
        return
    
    # روشن/خاموش
    if t == 'روشن':
        set_active(True)
        send(tok, cid, '🟢 فعال شد!', kb_main()); return
    if t == 'خاموش':
        set_active(False)
        send(tok, cid, '🔴 غیرفعال شد', kb_main()); return
    
    # افزودن منبع
    if 'افزودن منبع' in t:
        src = re.sub(r'.*افزودن منبع\s*', '', t).strip()
        src = src.strip('@').strip()
        if not src:
            send(tok, cid, '❌ مثال: افزودن منبع @mychannel', kb_main()); return
        src = '@' + src
        cfg = get_config()
        sources = cfg['sources'] if cfg else []
        if src not in sources: sources.append(src)
        update_config(source_channels=', '.join(sources))
        send(tok, cid, f'✅ {src} اضافه شد\n\nکل منابع: {len(sources)}', kb_main()); return
    
    if 'حذف منبع' in t:
        src = re.sub(r'.*حذف منبع\s*', '', t).strip().strip('@').strip()
        if not src:
            send(tok, cid, '❌ مثال: حذف منبع @mychannel', kb_main()); return
        src = '@' + src
        cfg = get_config()
        sources = [s for s in (cfg['sources'] if cfg else []) if s.lower().strip('@') != src.lower().strip('@')]
        update_config(source_channels=', '.join(sources))
        send(tok, cid, f'✅ {src} حذف شد\n\nباقیمانده: {len(sources)}', kb_main()); return
    
    if 'تنظیم مقصد' in t:
        tgt = re.sub(r'.*تنظیم مقصد\s*', '', t).strip().strip('@').strip()
        if not tgt:
            send(tok, cid, '❌ مثال: تنظیم مقصد @mychannel', kb_main()); return
        tgt = '@' + tgt
        update_config(target_channel=tgt)
        send(tok, cid, f'✅ مقصد: {tgt}', kb_main()); return
    
    if 'کلیدواژه' in t:
        kw = re.sub(r'.*کلیدواژه\s*', '', t).strip()
        update_config(content_keywords=kw)
        send(tok, cid, f'✅ کلیدواژه: {kw}', kb_main()); return
    
    if 'هدف' in t and re.search(r'\d', t):
        try:
            n = int(re.sub(r'[^\d]', '', t))
            update_config(recruit_target_count=n)
            send(tok, cid, f'✅ هدف: {n} عضو', kb_main())
        except: send(tok, cid, '❌ عدد بده', kb_main())
        return
    
    if 'پیام' in t and t.strip() != 'پیام':
        msg = t[5:].strip()
        update_config(recruit_message=msg)
        send(tok, cid, f'✅ پیام ذخیره شد', kb_main()); return
    
    # اتصال
    m = re.match(r'^(09\d{9})$', t)
    if m:
        sid = link_owner(cid, t)
        if sid:
            send(tok, cid, f'✅ وصل شدی!\n\nبنویس: راهنما', kb_main())
        else:
            send(tok, cid, '❌ این شماره ثبت نشده. از پنل ثبت‌نام کن', kb_main())
        return
    
    send(tok, cid, '🤔 بنویس: راهنما', kb_main())

def auto_collect(tok, cfg):
    """جمع‌آوری خودکار از منابع"""
    if not cfg['sources'] or not cfg['target']: return
    # چک کردن پیام‌های جدید
    r = get_updates(tok)
    if r.get('status') != 'OK': return
    ups = r.get('data', {}).get('updates', []) or []
    for u in ups:
        nm = u.get('new_message')
        if not nm: continue
        cid = str(u.get('chat_id', ''))
        txt = nm.get('text', '')
        mid = nm.get('message_id')
        if not mid or mid in _last_seen: continue
        save_seen(mid)
        if not txt: continue
        # چک کن از کانال منبع باشه
        for src in cfg['sources']:
            src_clean = src.lstrip('@').lower()
            if src_clean in cid.lower():
                # کلیدواژه
                if cfg['keywords']:
                    if not any(k in txt for k in cfg['keywords']): continue
                # کپی به مقصد
                new_txt = txt + '\n\n🏪 Dolphin SMS'
                rr = send(tok, cfg['target'], new_txt)
                log(f'📥 {cid} → {cfg["target"]}: {txt[:30]}')
                break

def main():
    load_seen()
    tok = get_token()
    if not tok: log('❌ توکن نیست'); return
    log('🤖 Admin Bot v1')
    log('✅ آماده')
    while True:
        try:
            # پردازش پیام‌های خصوصی
            r = get_updates(tok)
            if r.get('status') == 'OK':
                ups = r.get('data', {}).get('updates', []) or []
                for u in ups:
                    nm = u.get('new_message')
                    if not nm: continue
                    cid = str(u.get('chat_id', ''))
                    txt = nm.get('text', '')
                    mid = nm.get('message_id')
                    aux = nm.get('aux_data') or {}
                    btn = aux.get('button_id') if isinstance(aux, dict) else None
                    if not mid or mid in _last_seen: continue
                    save_seen(mid)
                    if not txt: continue
                    # اگه چت خصوصی (نه کانال)
                    ct = nm.get('chat_type') or u.get('chat_type') or ''
                    if 'User' in ct or 'Bot' in ct or cid.startswith('b'):
                        if is_owner(cid):
                            handle_admin(tok, cid, txt, btn)
                        else:
                            # فقط اگه شماره بود اتصال
                            if re.match(r'^09\d{9}$', txt.strip()):
                                handle_admin(tok, cid, txt, btn)
                            else:
                                send(tok, cid, '🔑 برای اتصال، شماره‌ای که با اون ثبت‌نام کردی رو بفرست\nمثال: 09123456789')
            # جمع‌آوری خودکار
            if is_active():
                cfg = get_config()
                if cfg: auto_collect(tok, cfg)
            time.sleep(3)
        except KeyboardInterrupt: break
        except Exception as e: log(f'❌ {e}'); time.sleep(5)

if __name__ == '__main__':
    main()
