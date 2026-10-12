import sqlite3


def _db():
    return sqlite3.connect('panel.db', timeout=15)


# ============ اطلاعات مشتری ============
def add_customer(phone, name, password):
    conn = _db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO customers (phone, name, password) VALUES (?, ?, ?)", (phone, name, password))
        cid = c.lastrowid
        conn.commit(); conn.close()
        return cid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_customer(phone):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT id, phone, name, password, created_at FROM customers WHERE phone=?", (phone,))
    row = c.fetchone(); conn.close()
    return row


def get_customer_by_id(cid):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT id, phone, name, created_at FROM customers WHERE id=?", (cid,))
    row = c.fetchone(); conn.close()
    return row


def update_last_login(cid):
    conn = _db(); c = conn.cursor()
    c.execute("UPDATE customers SET last_login=CURRENT_TIMESTAMP WHERE id=?", (cid,))
    conn.commit(); conn.close()


# ============ مغازه‌دارها ============
def get_all_shops():
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name, u.phone
                 FROM users u WHERE u.id != 1 AND u.status='active'
                 ORDER BY u.shop_name""")
    rows = c.fetchall(); conn.close()
    return rows


def search_shops(q):
    """جستجوی هوشمند - هر جای کلمه مچ بشه"""
    if not q or not q.strip():
        return get_all_shops()
    q = q.strip()
    qry = '%' + q + '%'
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name, u.phone
                 FROM users u WHERE u.id != 1 AND u.status='active'
                 AND (
                     LOWER(u.shop_name) LIKE LOWER(?) OR
                     LOWER(u.username) LIKE LOWER(?) OR
                     LOWER(IFNULL(u.phone, '')) LIKE LOWER(?)
                 )
                 ORDER BY 
                     CASE 
                         WHEN LOWER(u.shop_name) LIKE LOWER(?) THEN 1
                         WHEN LOWER(u.username) LIKE LOWER(?) THEN 2
                         ELSE 3
                     END,
                     u.shop_name""",
              (qry, qry, qry, q + '%', q + '%'))
    rows = c.fetchall(); conn.close()
    return rows


def search_products(q, shop_id=None):
    """جستجوی محصولات - هر جای کلمه"""
    if not q or not q.strip():
        return []
    q = q.strip()
    qry = '%' + q + '%'
    conn = _db(); c = conn.cursor()
    if shop_id:
        c.execute("""SELECT id, name, price, unit, description, category
                     FROM shop_products WHERE available=1 AND shop_id=?
                     AND (LOWER(name) LIKE LOWER(?) OR LOWER(IFNULL(aliases, '')) LIKE LOWER(?))
                     ORDER BY name""", (shop_id, qry, qry))
    else:
        c.execute("""SELECT id, name, price, unit, description, category
                     FROM shop_products WHERE available=1
                     AND (LOWER(name) LIKE LOWER(?) OR LOWER(IFNULL(aliases, '')) LIKE LOWER(?))
                     ORDER BY name""", (qry, qry))
    rows = c.fetchall(); conn.close()
    return rows


def get_shop(uid):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT id, username, shop_name, phone FROM users WHERE id=?", (uid,))
    row = c.fetchone(); conn.close()
    return row


def get_shop_info(uid):
    """اطلاعات مغازه از shop_info"""
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT shop_name, shop_type, address, phone, hours, instagram, description
                 FROM shop_info WHERE messenger=? LIMIT 1""", ('rubika_'+str(uid),))
    row = c.fetchone()
    if not row:
        c.execute("""SELECT shop_name, shop_type, address, phone, hours, instagram, description
                     FROM shop_info LIMIT 1""")
        row = c.fetchone()
    conn.close()
    return row


# ============ محصولات ============
def get_products(shop_id=1):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT id, name, price, unit, description, category
                 FROM shop_products WHERE available=1 ORDER BY category, name""")
    rows = c.fetchall(); conn.close()
    return rows


# ============ علاقه‌مندی‌ها ============
def add_favorite(cid, uid):
    conn = _db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO customer_favorites (customer_id, user_id) VALUES (?, ?)", (cid, uid))
        conn.commit(); conn.close()
        return True
    except:
        conn.close()
        return False


def remove_favorite(cid, uid):
    conn = _db(); c = conn.cursor()
    c.execute("DELETE FROM customer_favorites WHERE customer_id=? AND user_id=?", (cid, uid))
    conn.commit(); conn.close()


def get_favorites(cid):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name, u.phone
                 FROM customer_favorites f
                 JOIN users u ON u.id = f.user_id
                 WHERE f.customer_id=?""", (cid,))
    rows = c.fetchall(); conn.close()
    return rows


def is_favorite(cid, uid):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT 1 FROM customer_favorites WHERE customer_id=? AND user_id=?", (cid, uid))
    row = c.fetchone(); conn.close()
    return row is not None


# ============ سفارش‌ها ============
def add_order(cid, uid, subject, message, phone=''):
    conn = _db(); c = conn.cursor()
    c.execute("""INSERT INTO customer_orders (customer_id, user_id, subject, message, phone)
                 VALUES (?, ?, ?, ?, ?)""", (cid, uid, subject, message, phone))
    oid = c.lastrowid
    conn.commit(); conn.close()
    return oid


def get_my_orders(cid):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT o.id, u.shop_name, o.subject, o.message, o.status, o.reply, o.created_at
                 FROM customer_orders o
                 LEFT JOIN users u ON u.id = o.user_id
                 WHERE o.customer_id=? ORDER BY o.id DESC""", (cid,))
    rows = c.fetchall(); conn.close()
    return rows


# ============ امتیاز ============
def get_points(cid):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT points, tier FROM loyalty WHERE user_id=?", (cid + 1000,))
    row = c.fetchone(); conn.close()
    if not row:
        return {'points': 0, 'tier': 'bronze'}
    return {'points': row[0] or 0, 'tier': row[1] or 'bronze'}


def count_orders(cid):
    conn = _db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customer_orders WHERE customer_id=?", (cid,))
    n = c.fetchone()[0]; conn.close()
    return n


# ============ CATEGORIES ============
def get_categories():
    conn = _db(); c = conn.cursor()
    c.execute("SELECT id, name, icon, color FROM product_categories ORDER BY sort_order")
    rows = c.fetchall(); conn.close()
    return rows


# ============ TOP SHOPS ============
def get_top_shops(limit=6):
    """مغازه‌های برتر بر اساس امتیاز"""
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name, u.phone,
                 COALESCE(AVG(r.stars), 0) AS avg_stars,
                 COUNT(r.id) AS rating_count
                 FROM users u
                 LEFT JOIN ratings r ON r.shop_id = u.id
                 WHERE u.id != 1 AND u.status='active'
                 GROUP BY u.id
                 ORDER BY avg_stars DESC, rating_count DESC
                 LIMIT ?""", (limit,))
    rows = c.fetchall(); conn.close()
    return rows


# ============ FEATURED PRODUCTS ============
def get_featured_products(limit=8):
    """محصولات پیشنهادی"""
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT id, name, price, unit, description, category
                 FROM shop_products WHERE available=1
                 ORDER BY RANDOM() LIMIT ?""", (limit,))
    rows = c.fetchall(); conn.close()
    return rows


# ============ PRODUCTS BY CATEGORY ============
def get_products_by_category(cat, limit=50):
    conn = _db(); c = conn.cursor()
    c.execute("""SELECT id, name, price, unit, description, category
                 FROM shop_products WHERE available=1 AND category=?
                 ORDER BY name LIMIT ?""", (cat, limit))
    rows = c.fetchall(); conn.close()
    return rows


# ============ SUGGEST (برای جستجوی زنده) ============
def suggest(q, limit=8):
    """پیشنهاد سریع برای جستجوی زنده"""
    if not q or len(q) < 1:
        return []
    qry = '%' + q + '%'
    conn = _db(); c = conn.cursor()

    # مغازه‌ها
    c.execute("""SELECT 'shop' AS type, u.id, u.shop_name AS title, u.username AS sub
                 FROM users u WHERE u.id != 1 AND u.status='active'
                 AND (LOWER(u.shop_name) LIKE LOWER(?) OR LOWER(u.username) LIKE LOWER(?))
                 LIMIT ?""", (qry, qry, limit))
    shops = c.fetchall()

    # محصولات
    c.execute("""SELECT 'product' AS type, id, name AS title, 
                 CAST(price AS TEXT) || ' ت' AS sub
                 FROM shop_products WHERE available=1
                 AND (LOWER(name) LIKE LOWER(?) OR LOWER(IFNULL(aliases, '')) LIKE LOWER(?))
                 LIMIT ?""", (qry, qry, limit))
    products = c.fetchall()
    conn.close()

    return shops + products


# ============ SHOP STATS ============
def get_shop_stats(shop_id):
    """آمار مغازه"""
    conn = _db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM shop_products WHERE shop_id=? AND available=1", (shop_id,))
    products = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ratings WHERE shop_id=?", (shop_id,))
    ratings = c.fetchone()[0]
    c.execute("SELECT AVG(stars) FROM ratings WHERE shop_id=?", (shop_id,))
    avg = c.fetchone()[0] or 0
    conn.close()
    return {'products': products, 'ratings': ratings, 'avg': round(avg, 1)}
