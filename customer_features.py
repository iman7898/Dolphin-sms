import sqlite3


def _db():
    return sqlite3.connect('panel.db', timeout=15)


def init_tables():
    conn = _db(); c = conn.cursor()

    # سبد خرید
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        shop_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(customer_id, shop_id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        price INTEGER DEFAULT 0,
        UNIQUE(cart_id, product_id))''')

    # پیگیری سفارش
    c.execute('''CREATE TABLE IF NOT EXISTS order_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        status TEXT,
        note TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # نظرسنجی
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        shop_id INTEGER,
        stars INTEGER DEFAULT 5,
        comment TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(customer_id, shop_id))''')

    # نوتیف مشتری
    c.execute('''CREATE TABLE IF NOT EXISTS customer_notifs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        title TEXT,
        body TEXT,
        icon TEXT DEFAULT '🔔',
        link TEXT DEFAULT '',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # کد تخفیف
    c.execute('''CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        discount_type TEXT DEFAULT 'percent',
        value INTEGER DEFAULT 0,
        min_order INTEGER DEFAULT 0,
        max_uses INTEGER DEFAULT 100,
        used_count INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS coupon_uses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coupon_id INTEGER,
        customer_id INTEGER,
        order_id INTEGER,
        discount_amount INTEGER DEFAULT 0,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # چت مستقیم
    c.execute('''CREATE TABLE IF NOT EXISTS customer_chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        shop_id INTEGER,
        sender TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()
    return True


def init_coupons():
    """کدهای تخفیف پیش‌فرض"""
    conn = _db(); c = conn.cursor()
    defaults = [
        ('WELCOME10', 'percent', 10, 0, 1000, 1),
        ('NEW20', 'percent', 20, 50000, 500, 1),
        ('OFF50000', 'fixed', 50000, 100000, 100, 1),
    ]
    for code, dtype, val, mino, mu, act in defaults:
        try:
            c.execute("""INSERT OR IGNORE INTO coupons 
                         (code, discount_type, value, min_order, max_uses, active)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (code, dtype, val, mino, mu, act))
        except: pass
    conn.commit()
    conn.close()


# ============ CART ============
def get_or_create_cart(cid, shop_id):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT id FROM cart WHERE customer_id=? AND shop_id=?", (cid, shop_id))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0]
    c.execute("INSERT INTO cart (customer_id, shop_id) VALUES (?, ?)", (cid, shop_id))
    cart_id = c.lastrowid
    conn.commit(); conn.close()
    return cart_id


def add_to_cart(cid, shop_id, product_id, price, qty=1):
    cart_id = get_or_create_cart(cid, shop_id)
    conn = _db(); c = conn.cursor()
    c.execute("SELECT id, quantity FROM cart_items WHERE cart_id=? AND product_id=?", (cart_id, product_id))
    row = c.fetchone()
    if row:
        c.execute("UPDATE cart_items SET quantity=quantity+? WHERE id=?", (qty, row[0]))
    else:
        c.execute("""INSERT INTO cart_items (cart_id, product_id, quantity, price)
                     VALUES (?, ?, ?, ?)""", (cart_id, product_id, qty, price))
    conn.commit(); conn.close()


def get_cart_items(cid, shop_id):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT ci.id, ci.product_id, sp.name, ci.quantity, ci.price
                 FROM cart_items ci
                 JOIN cart ca ON ca.id = ci.cart_id
                 JOIN shop_products sp ON sp.id = ci.product_id
                 WHERE ca.customer_id=? AND ca.shop_id=?""", (cid, shop_id))
    rows = c.fetchall(); conn.close()
    return rows


def update_cart_qty(item_id, qty):
    conn = _db(); c = conn.cursor()
    if qty <= 0:
        c.execute("DELETE FROM cart_items WHERE id=?", (item_id,))
    else:
        c.execute("UPDATE cart_items SET quantity=? WHERE id=?", (qty, item_id))
    conn.commit(); conn.close()


def remove_from_cart(item_id):
    conn = _db(); c = conn.cursor()
    c.execute("DELETE FROM cart_items WHERE id=?", (item_id,))
    conn.commit(); conn.close()


def clear_cart(cid, shop_id):
    conn = _db(); c = conn.cursor()
    c.execute("""DELETE FROM cart_items WHERE cart_id IN 
                 (SELECT id FROM cart WHERE customer_id=? AND shop_id=?)""", (cid, shop_id))
    conn.commit(); conn.close()


def count_cart(cid):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT COALESCE(SUM(ci.quantity), 0) FROM cart_items ci
                 JOIN cart ca ON ca.id = ci.cart_id WHERE ca.customer_id=?""", (cid,))
    n = c.fetchone()[0]; conn.close()
    return n


# ============ ORDER STATUS ============
def add_order_status(order_id, status, note=''):
    conn = _db(); c = conn.cursor()
    c.execute("INSERT INTO order_status (order_id, status, note) VALUES (?, ?, ?)",
              (order_id, status, note))
    conn.commit(); conn.close()


def get_order_status(order_id):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT status, note, created_at FROM order_status WHERE order_id=? ORDER BY id ASC", (order_id,))
    rows = c.fetchall(); conn.close()
    return rows


# ============ RATINGS ============
def add_rating(cid, shop_id, stars, comment=''):
    conn = _db(); c = conn.cursor()
    try:
        c.execute("""INSERT OR REPLACE INTO ratings (customer_id, shop_id, stars, comment)
                     VALUES (?, ?, ?, ?)""", (cid, shop_id, stars, comment))
        conn.commit()
    except: pass
    conn.close()


def get_rating(cid, shop_id):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT stars, comment FROM ratings WHERE customer_id=? AND shop_id=?", (cid, shop_id))
    row = c.fetchone(); conn.close()
    return row


def get_shop_avg_rating(shop_id):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT AVG(stars), COUNT(*) FROM ratings WHERE shop_id=?", (shop_id,))
    row = c.fetchone(); conn.close()
    if not row or not row[0]:
        return (0, 0)
    return (round(row[0], 1), row[1])


def get_shop_ratings(shop_id, limit=20):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT r.stars, r.comment, c.name, r.created_at
                 FROM ratings r JOIN customers c ON c.id = r.customer_id
                 WHERE r.shop_id=? ORDER BY r.id DESC LIMIT ?""", (shop_id, limit))
    rows = c.fetchall(); conn.close()
    return rows


# ============ NOTIFS ============
def add_notif(cid, title, body, icon='🔔', link=''):
    conn = _db(); c = conn.cursor()
    c.execute("""INSERT INTO customer_notifs (customer_id, title, body, icon, link)
                 VALUES (?, ?, ?, ?, ?)""", (cid, title, body, icon, link))
    conn.commit(); conn.close()


def get_notifs(cid, limit=50):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT id, title, body, icon, link, is_read, created_at
                 FROM customer_notifs WHERE customer_id=? ORDER BY id DESC LIMIT ?""", (cid, limit))
    rows = c.fetchall(); conn.close()
    return rows


def count_unread_notifs(cid):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customer_notifs WHERE customer_id=? AND is_read=0", (cid,))
    n = c.fetchone()[0]; conn.close()
    return n


def mark_notif_read(nid):
    conn = _db(); c = conn.cursor()
    c.execute("UPDATE customer_notifs SET is_read=1 WHERE id=?", (nid,))
    conn.commit(); conn.close()


def mark_all_notifs_read(cid):
    conn = _db(); c = conn.cursor()
    c.execute("UPDATE customer_notifs SET is_read=1 WHERE customer_id=?", (cid,))
    conn.commit(); conn.close()


# ============ COUPONS ============
def check_coupon(code):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT id, discount_type, value, min_order, max_uses, used_count
                 FROM coupons WHERE code=? AND active=1""", (code,))
    row = c.fetchone(); conn.close()
    if not row: return None
    if row[5] >= row[4]: return None  # اگه از حد گذشته
    return {
        'id': row[0], 'type': row[1], 'value': row[2],
        'min_order': row[3], 'max_uses': row[4], 'used': row[5]
    }


def calc_discount(coupon, total):
    if not coupon: return 0
    if total < coupon['min_order']: return 0
    if coupon['type'] == 'percent':
        return int(total * coupon['value'] / 100)
    return min(coupon['value'], total)


def use_coupon(coupon_id, cid, order_id, discount_amount):
    conn = _db(); c = conn.cursor()
    c.execute("""INSERT INTO coupon_uses (coupon_id, customer_id, order_id, discount_amount)
                 VALUES (?, ?, ?, ?)""", (coupon_id, cid, order_id, discount_amount))
    c.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?", (coupon_id,))
    conn.commit(); conn.close()


# ============ CHAT ============
def send_customer_msg(cid, shop_id, message):
    conn = _db(); c = conn.cursor()
    c.execute("""INSERT INTO customer_chat (customer_id, shop_id, sender, message)
                 VALUES (?, ?, 'customer', ?)""", (cid, shop_id, message))
    conn.commit(); conn.close()


def send_shop_msg(cid, shop_id, message):
    conn = _db(); c = conn.cursor()
    c.execute("""INSERT INTO customer_chat (customer_id, shop_id, sender, message)
                 VALUES (?, ?, 'shop', ?)""", (cid, shop_id, message))
    conn.commit(); conn.close()


def get_chat(cid, shop_id, limit=200):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT sender, message, created_at FROM customer_chat
                 WHERE customer_id=? AND shop_id=? ORDER BY id ASC LIMIT ?""",
              (cid, shop_id, limit))
    rows = c.fetchall(); conn.close()
    return rows


# ============ INIT ============
if __name__ == "__main__":
    init_tables()
    init_coupons()
    print("✅ جدول‌های قابلیت‌های مشتری ساخته شد")
