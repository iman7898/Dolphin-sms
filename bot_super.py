"""🐬 Super Bot v2 - فروشگاه هوشمند با کد مغازه"""
import requests, sqlite3, time, re
from datetime import datetime, timedelta

BASE = "https://botapi.rubika.ir/v3"
DB = "panel.db"

def db(): return sqlite3.connect(DB, timeout=15)
def log(m): print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)

def get_token():
    c = db().cursor()
    c.execute("SELECT token FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    return r[0] if r else None

def send(tok, cid, txt, kb=None):
    payload = {'chat_id': str(cid), 'text': txt}
    if kb:
        payload['chat_keypad'] = kb
        payload['chat_keypad_type'] = 'New'
    try:
        r = requests.post(f"{BASE}/{tok}/sendMessage", json=payload, timeout=20)
        return r.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_updates(tok, off=None):
    try:
        d = {}
        r = requests.post(f"{BASE}/{tok}/getUpdates", json=d, timeout=20)
        return r.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# کیبورد
def kb_main():
    return {'rows': [
        {'buttons': [{'id': 'b_shop', 'type': 'Simple', 'button_text': '🛍 فروشگاه'}]},
        {'buttons': [
            {'id': 'b_cart', 'type': 'Simple', 'button_text': '🛒 سبد'},
            {'id': 'b_orders', 'type': 'Simple', 'button_text': '📦 سفارش‌ها'},
        ]},
        {'buttons': [{'id': 'b_help', 'type': 'Simple', 'button_text': '❓ راهنما'}]},
    ]}

def kb_shop():
    return {'rows': [
        {'buttons': [
            {'id': 's_add', 'type': 'Simple', 'button_text': '➕ افزودن'},
            {'id': 's_list', 'type': 'Simple', 'button_text': '📋 محصولات'},
        ]},
        {'buttons': [
            {'id': 's_orders', 'type': 'Simple', 'button_text': '📦 سفارش‌ها'},
            {'id': 's_stats', 'type': 'Simple', 'button_text': '📊 آمار'},
        ]},
        {'buttons': [{'id': 's_help', 'type': 'Simple', 'button_text': '❓ راهنما'}]},
    ]}

def init_db():
    conn = db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bot_sessions (
        chat_id TEXT PRIMARY KEY,
        shop_id INTEGER,
        state TEXT DEFAULT 'idle',
        data TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit(); conn.close()

def get_sess(cid):
    c = db().cursor()
    c.execute("SELECT shop_id, state, data FROM bot_sessions WHERE chat_id=?", (cid,))
    r = c.fetchone()
    if r: return {'shop_id': r[0], 'state': r[1] or 'idle', 'data': r[2] or ''}
    return {'shop_id': None, 'state': 'idle', 'data': ''}

def set_sess(cid, **kw):
    conn = db(); c = conn.cursor()
    c.execute("SELECT chat_id FROM bot_sessions WHERE chat_id=?", (cid,))
    if c.fetchone():
        for k, v in kw.items():
            c.execute(f"UPDATE bot_sessions SET {k}=?, updated_at=CURRENT_TIMESTAMP WHERE chat_id=?", (v, cid))
    else:
        c.execute("INSERT INTO bot_sessions (chat_id, shop_id, state, data) VALUES (?,?,?,?)",
                  (cid, kw.get('shop_id'), kw.get('state', 'idle'), kw.get('data', '')))
    conn.commit(); conn.close()

def shop_by_chat(cid):
    c = db().cursor()
    c.execute("SELECT id FROM users WHERE shop_image=?", (cid,))
    r = c.fetchone()
    return r[0] if r else None

def shop_by_code(code):
    code = (code or '').strip().upper()
    if not code.startswith('SHOP'):
        code = 'SHOP' + code
    c = db().cursor()
    c.execute("SELECT id, username FROM users WHERE UPPER(shop_code)=?", (code,))
    return c.fetchone()

def shop_name(sid):
    c = db().cursor()
    c.execute("SELECT username FROM users WHERE id=?", (sid,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("SELECT shop_name FROM shop_info WHERE id=?", (sid,))
    r = c.fetchone()
    return r[0] if r else f'فروشگاه {sid}'

def products(sid, q='', limit=20):
    c = db().cursor()
    if q:
        q2 = f'%{q}%'
        c.execute("SELECT id, name, price, unit FROM shop_products WHERE shop_id=? AND available=1 AND (name LIKE ? OR aliases LIKE ?) LIMIT ?",
                  (sid, q2, q2, limit))
    else:
        c.execute("SELECT id, name, price, unit FROM shop_products WHERE shop_id=? AND available=1 LIMIT ?",
                  (sid, limit))
    return c.fetchall()

def add_product(sid, name, price):
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO shop_products (shop_id, name, price, unit, available) VALUES (?,?,?,'عدد',1)",
              (sid, name, price))
    conn.commit(); conn.close()

def del_product(sid, name):
    conn = db(); c = conn.cursor()
    c.execute("UPDATE shop_products SET available=0 WHERE shop_id=? AND name=?", (sid, name))
    n = c.rowcount
    conn.commit(); conn.close()
    return n

def add_order(sid, prod, price, cust_cid):
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO customer_orders (customer_id, shop_id, subject, message, phone) VALUES (0,?,?,?,?)",
              (sid, f'سفارش: {prod}', f'ربات - چت: {cust_cid}', cust_cid))
    oid = c.lastrowid
    conn.commit(); conn.close()
    return oid

def orders_list(sid, limit=10):
    c = db().cursor()
    c.execute("SELECT id, subject, phone, created_at FROM customer_orders WHERE shop_id=? ORDER BY id DESC LIMIT ?",
              (sid, limit))
    return c.fetchall()

def count_orders(sid):
    c = db().cursor()
    c.execute("SELECT COUNT(*) FROM customer_orders WHERE shop_id=?", (sid,))
    return c.fetchone()[0] or 0

def handle_shop(tok, cid, sid, txt, btn=None):
    t = (txt or '').strip()
    if btn == 's_add' or t == 'افزودن':
        send(tok, cid, 'بنویس:\nافزودن [نام] [قیمت]\nمثال: افزودن سیب 50000', kb_shop()); return
    if btn == 's_list' or t in ('لیست', 'محصولات', '📋 محصولات'):
        prods = products(sid)
        if not prods: send(tok, cid, '📭 خالیه', kb_shop()); return
        msg = f'📋 {len(prods)} محصول:\n\n'
        for p in prods: msg += f'📦 {p[1]} — {p[2]:,} ت\n'
        send(tok, cid, msg, kb_shop()); return
    if btn == 's_orders' or t in ('سفارش‌ها', '📦 سفارش‌ها'):
        rows = orders_list(sid)
        if not rows: send(tok, cid, '📭 سفارشی نداری', kb_shop()); return
        msg = '📦 سفارش‌ها:\n\n'
        for r in rows: msg += f'🔢 #{r[0]} — {r[1]}\n📱 {r[2]}\n\n'
        send(tok, cid, msg, kb_shop()); return
    if btn == 's_stats' or t in ('آمار', '📊 آمار'):
        n = count_orders(sid)
        send(tok, cid, f'📊 آمار:\n\n📦 سفارش‌ها: {n}', kb_shop()); return
    if btn == 's_help' or t in ('راهنما', '❓ راهنما'):
        send(tok, cid, '🏪 راهنما:\n\n➕ افزودن [نام] [قیمت]\n🗑 حذف [نام]\n📋 لیست\n📦 سفارش‌ها\n📊 آمار', kb_shop()); return
    if t.startswith('افزودن '):
        parts = t[7:].strip().split()
        if len(parts) >= 2:
            try:
                name = ' '.join(parts[:-1]); price = int(parts[-1].replace(',', ''))
                add_product(sid, name, price)
                send(tok, cid, f'✅ {name} اضافه شد\n💰 {price:,} ت', kb_shop())
            except:
                send(tok, cid, '❌ قیمت عدد باشه', kb_shop())
        return
    if t.startswith('حذف '):
        name = t[4:].strip(); n = del_product(sid, name)
        send(tok, cid, f'✅ {name} حذف شد' if n else '❌ پیدا نشد', kb_shop()); return
    send(tok, cid, '🤔 متوجه نشدم\nبنویس: راهنما', kb_shop())

def handle_customer(tok, cid, txt, btn=None):
    sess = get_sess(cid); sid = sess['shop_id']
    t = (txt or '').strip()
    # کد مغازه
    m = re.match(r'^(SHOP)?(\d+)$', t.upper().replace(' ', ''))
    if m:
        shop = shop_by_code(t)
        if shop:
            set_sess(cid, shop_id=shop[0])
            send(tok, cid, f'✅ وصل شدی به {shop[1]}\n\nبنویس "لیست" یا اسم محصول', kb_main())
        else:
            send(tok, cid, '❌ کد اشتباهه', kb_main())
        return
    if t in ('سلام', '/start', 'شروع', 'منو') and not sid:
        send(tok, cid, '🐬 سلام!\n\nبرای اتصال به فروشگاه، کد مغازه‌دار رو بفرست.\nمثال: SHOP1001\n\nکد مغازه‌دار خودت رو از پنل مغازه‌دار بگیر', kb_main())
        return
    if btn == 'b_shop' or t == 'لیست':
        if not sid: send(tok, cid, '❌ اول کد مغازه رو بفرست', kb_main()); return
        prods = products(sid)
        if not prods: send(tok, cid, '📭 خالیه', kb_main()); return
        msg = f'🛍 {shop_name(sid)}:\n\n'
        for p in prods: msg += f'📦 {p[1]}\n💰 {p[2]:,} ت\n\n'
        send(tok, cid, msg, kb_main()); return
    if btn == 'b_help' or t in ('راهنما', '❓ راهنما'):
        send(tok, cid, '❓ راهنما:\n\n🔍 [اسم محصول] → قیمت\n📋 لیست → همه محصولات\n🛒 سفارش [نام] → ثبت سفارش\n🏪 [کد] → اتصال به مغازه\n\nمثال: SHOP1001', kb_main()); return
    if btn == 'b_cart' or t in ('سبد', '🛒 سبد'):
        send(tok, cid, '🛒 سبد خالیه\n\nاز لیست محصول انتخاب کن', kb_main()); return
    if btn == 'b_orders' or t in ('سفارش‌ها', '📦 سفارش‌ها'):
        send(tok, cid, '📦 برای دیدن سفارش‌هات به مغازه‌دار پیام بده', kb_main()); return
    if sid:
        if t.startswith('سفارش '):
            name = t[6:].strip(); prods = products(sid, q=name, limit=1)
            if prods:
                p = prods[0]; oid = add_order(sid, p[1], p[2], cid)
                send(tok, cid, f'✅ سفارش #{oid}\n📦 {p[1]}\n💰 {p[2]:,} ت\n\nمغازه‌دار تماس می‌گیره', kb_main())
            else:
                send(tok, cid, '❌ پیدا نشد', kb_main())
            return
        prods = products(sid, q=t)
        if prods:
            msg = f'🔍 {t}:\n\n'
            for p in prods: msg += f'📦 {p[1]} — {p[2]:,} ت\n'
            msg += '\nبرای سفارش بنویس: سفارش [اسم]'
            send(tok, cid, msg, kb_main())
        else:
            send(tok, cid, '❌ چیزی پیدا نشد', kb_main())
    else:
        send(tok, cid, '🔑 کد مغازه‌دار رو بفرست\nمثال: SHOP1001', kb_main())

def process(tok, cid, txt, btn=None):
    sid = shop_by_chat(cid)
    if sid: handle_shop(tok, cid, sid, txt, btn)
    else: handle_customer(tok, cid, txt, btn)

def main():
    init_db()
    tok = get_token()
    if not tok: log('❌ توکن نیست'); return
    log('🐬 Super Bot v2'); log('✅ آماده')
    off = None; seen = set()
    while True:
        try:
            r = get_updates(tok, off)
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
                    if mid and mid in seen: continue
                    if mid: seen.add(mid)
                    if not txt: continue
                    try: process(tok, cid, txt, btn)
                    except Exception as e: log(f'❌ {e}')
                    if mid: off = mid
            time.sleep(2)
        except KeyboardInterrupt: break
        except Exception as e: log(f'❌ {e}'); time.sleep(5)

if __name__ == '__main__':
    main()
