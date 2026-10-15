from datetime import datetime as _dt, timedelta

import sqlite3

DB_PATH = "panel.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        shop_name TEXT,
        phone TEXT,
        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP,
        status TEXT DEFAULT 'active',
        sms_limit INTEGER DEFAULT 1000,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS sent_sms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, phone TEXT, message TEXT, status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, phone TEXT, location TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT, ip TEXT, user_agent TEXT,
        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        logout_time TIMESTAMP, duration_seconds INTEGER DEFAULT 0,
        status TEXT DEFAULT 'success')""")

    conn.commit()
    conn.close()
    init_schedule_table()
    init_chat_table()
    init_ai_table()
    init_dm_table()
    init_security_table()
    init_notif_table()
    init_chat_requests_table()

def init_schedule_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        message TEXT,
        start_date TEXT,
        end_date TEXT,
        daily_limit INTEGER DEFAULT 100,
        sent_today INTEGER DEFAULT 0,
        last_sent_date TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

# ==== کاربران ====
def add_user(username, password, shop_name, phone, days=30, sms_limit=1000):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    end = _dt.now() + timedelta(days=days)
    try:
        c.execute("""INSERT INTO users (username, password, shop_name, phone, end_date, sms_limit)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (username, password, shop_name, phone,
                   end.strftime("%Y-%m-%d %H:%M:%S"), sms_limit))
        conn.commit()
        return True, c.lastrowid
    except sqlite3.IntegrityError:
        return False, "نام کاربری تکراری است"
    finally:
        conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def get_user_by_phone(phone):
    """جستجو با شماره موبایل (با یا بدون ۰)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    p = (phone or '').strip()
    variants = [p]
    if p.startswith('0'):
        variants.append(p[1:])
        variants.append('98' + p[1:])
    else:
        variants.append('0' + p)
        variants.append('98' + p)
    for v in variants:
        c.execute("SELECT * FROM users WHERE phone=?", (v,))
        row = c.fetchone()
        if row:
            conn.close()
            return row
    conn.close()
    return None

def get_user_by_username_or_phone(identifier):
    """اول با username بعد با phone"""
    u = get_user_by_username(identifier)
    if u:
        return u
    return get_user_by_phone(identifier)

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def suspend_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET status='suspended' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def activate_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET status='active' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    c.execute("DELETE FROM sent_sms WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM events WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM login_logs WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def extend_user_days(user_id, days):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT end_date FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if row and row[0]:
        current_end = _dt.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    else:
        current_end = _dt.now()
    new_end = max(current_end, _dt.now()) + timedelta(days=days)
    c.execute("UPDATE users SET end_date=?, status='active' WHERE id=?",
              (new_end.strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    conn.close()

def update_sms_limit(user_id, new_limit):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET sms_limit=? WHERE id=?", (new_limit, user_id))
    conn.commit()
    conn.close()

def days_remaining(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT end_date FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return 0
    end = _dt.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    diff = (end - _dt.now()).days
    return max(diff, 0)

def sms_remaining(user_id):
    """چند پیامک برای این کاربر باقی مونده"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT sms_limit FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return 0
    limit = row[0] or 0
    c.execute("SELECT COUNT(*) FROM sent_sms WHERE user_id=?", (user_id,))
    used = c.fetchone()[0]
    conn.close()
    return max(limit - used, 0)

def sms_used(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sent_sms WHERE user_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

def is_user_active(user_id):
    user = get_user(user_id)
    if not user:
        return False
    if user[7] == 'suspended':
        return False
    if days_remaining(user_id) <= 0:
        return False
    if sms_remaining(user_id) <= 0:
        return False
    return True

# ==== پیامک‌ها ====
def log_sms(phone, message, status, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sent_sms (user_id, phone, message, status) VALUES (?, ?, ?, ?)",
              (user_id, phone, message, status))
    conn.commit()
    conn.close()

def log_event(phone, location, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO events (user_id, phone, location) VALUES (?, ?, ?)",
              (user_id, phone, location))
    conn.commit()
    conn.close()

def get_all_sms(limit=100, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT * FROM sent_sms WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    else:
        c.execute("SELECT * FROM sent_sms ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def count_sms(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT COUNT(*) FROM sent_sms WHERE user_id=? AND status IN ('success','ok','sent')", (user_id,))
    else:
        c.execute("SELECT COUNT(*) FROM sent_sms WHERE status IN ('success','ok','sent')")
    n = c.fetchone()[0]
    conn.close()
    return n

def clear_all():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sent_sms")
    c.execute("DELETE FROM events")
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('sent_sms', 'events')")
    conn.commit()
    conn.close()

# ==== لاگ ورود ====
def log_login(username, ip, user_agent, user_id=None, status="success"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO login_logs (user_id, username, ip, user_agent, status)
                 VALUES (?, ?, ?, ?, ?)""", (user_id, username, ip, user_agent, status))
    log_id = c.lastrowid
    conn.commit()
    conn.close()
    return log_id

def log_logout(log_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT login_time FROM login_logs WHERE id=?", (log_id,))
    row = c.fetchone()
    if row:
        login_time = _dt.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        duration = int((_dt.now() - login_time).total_seconds())
        c.execute("UPDATE login_logs SET logout_time=CURRENT_TIMESTAMP, duration_seconds=? WHERE id=?",
                  (duration, log_id))
    conn.commit()
    conn.close()

def get_user_logins(user_id, limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM login_logs WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_logins(limit=200):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM login_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_login_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM login_logs")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT ip) FROM login_logs")
    unique_ips = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM login_logs WHERE logout_time IS NULL")
    online = c.fetchone()[0]
    conn.close()
    return {"total": total, "unique_ips": unique_ips, "online": online}

def clear_login_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM login_logs")
    c.execute("DELETE FROM sqlite_sequence WHERE name='login_logs'")
    conn.commit()
    conn.close()

def time_remaining_detailed(user_id):
    """برگرداندن زمان دقیق باقی‌مونده به روز، ساعت، دقیقه"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT end_date FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return {"days": 0, "hours": 0, "minutes": 0, "total_seconds": 0, "expired": True}
    end = _dt.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    diff = end - _dt.now()
    total = int(diff.total_seconds())
    if total <= 0:
        return {"days": 0, "hours": 0, "minutes": 0, "total_seconds": 0, "expired": True}
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    return {
        "days": days, "hours": hours, "minutes": minutes,
        "total_seconds": total, "expired": False,
        "end_date": row[0]
    }

def update_end_date(user_id, new_end_date):
    """آپدیت تاریخ پایان اشتراک"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET end_date=?, status='active' WHERE id=?",
              (new_end_date, user_id))
    conn.commit()
    conn.close()

# ===== برنامه‌ریزی پیام‌ها =====
def add_schedule(user_id, title, message, start_date, end_date, daily_limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO schedules (user_id, title, message, start_date, end_date, daily_limit)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (user_id, title, message, start_date, end_date, daily_limit))
    conn.commit()
    conn.close()

def get_user_schedules(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM schedules WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_schedule(schedule_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id=? AND user_id=?", (schedule_id, user_id))
    conn.commit()
    conn.close()

def toggle_schedule(schedule_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT active FROM schedules WHERE id=? AND user_id=?", (schedule_id, user_id))
    row = c.fetchone()
    if row:
        new_state = 0 if row[0] == 1 else 1
        c.execute("UPDATE schedules SET active=? WHERE id=?", (new_state, schedule_id))
        conn.commit()
    conn.close()

def get_active_schedule_for_user(user_id):
    """برگرداندن برنامه فعال که الان توی بازه‌ست"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""SELECT * FROM schedules
                 WHERE user_id=? AND active=1
                 AND start_date <= ? AND end_date >= ?
                 ORDER BY id DESC LIMIT 1""",
              (user_id, now, now))
    row = c.fetchone()
    conn.close()
    return row

def increment_schedule_sent(schedule_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT sent_today, last_sent_date FROM schedules WHERE id=?", (schedule_id,))
    row = c.fetchone()
    today = _dt.now().strftime("%Y-%m-%d")
    if row:
        sent = row[0] or 0
        last = row[1] or ""
        if last != today:
            sent = 0
        c.execute("UPDATE schedules SET sent_today=?, last_sent_date=? WHERE id=?",
                  (sent + 1, today, schedule_id))
        conn.commit()
    conn.close()

def can_send_by_schedule(schedule_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT daily_limit, sent_today, last_sent_date FROM schedules WHERE id=?", (schedule_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    limit, sent, last = row
    today = _dt.now().strftime("%Y-%m-%d")
    if last != today:
        return True
    return (sent or 0) < (limit or 100)

# ===== چت =====
def init_chat_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sender TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def add_chat_message(user_id, sender, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (user_id, sender, message) VALUES (?, ?, ?)",
              (user_id, sender, message))
    conn.commit()
    conn.close()

def get_chat_messages(user_id, limit=200):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT * FROM chat_messages WHERE user_id=?
                 ORDER BY id ASC LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_chat_users():
    """لیست کاربرانی که پیام دارن + آواتار"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT DISTINCT u.id, u.username, u.shop_name,
                 (SELECT message FROM chat_messages WHERE user_id=u.id ORDER BY id DESC LIMIT 1),
                 (SELECT created_at FROM chat_messages WHERE user_id=u.id ORDER BY id DESC LIMIT 1),
                 (SELECT COUNT(*) FROM chat_messages WHERE user_id=u.id AND sender='shopkeeper' AND is_read=0),
                 (SELECT avatar_path FROM user_settings WHERE user_id=u.id)
                 FROM users u
                 WHERE u.id IN (SELECT DISTINCT user_id FROM chat_messages)
                 ORDER BY (SELECT id FROM chat_messages WHERE user_id=u.id ORDER BY id DESC LIMIT 1) DESC""")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_messages_read(user_id, reader):
    """علامت‌گذاری پیام‌ها به‌عنوان خوانده‌شده"""
    other = "admin" if reader == "shopkeeper" else "shopkeeper"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE chat_messages SET is_read=1 WHERE user_id=? AND sender=?", (user_id, other))
    conn.commit()
    conn.close()

def count_unread_for_admin():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM chat_messages WHERE sender='shopkeeper' AND is_read=0")
    n = c.fetchone()[0]
    conn.close()
    return n

def count_unread_for_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id=? AND sender='admin' AND is_read=0", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

# ===== هوش مصنوعی =====
def init_ai_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS ai_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        daily_count INTEGER DEFAULT 0,
        last_reset_date TEXT,
        total_count INTEGER DEFAULT 0,
        is_premium INTEGER DEFAULT 0,
        premium_until TEXT)""")
    conn.commit()
    conn.close()

def get_ai_usage(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM ai_usage WHERE user_id=?", (user_id,))
    row = c.fetchone()
    today = _dt.now().strftime("%Y-%m-%d")
    if not row:
        c.execute("INSERT INTO ai_usage (user_id, daily_count, last_reset_date) VALUES (?, 0, ?)",
                  (user_id, today))
        conn.commit()
        row = (c.lastrowid, user_id, 0, today, 0, 0, None)
    elif row[3] != today:
        c.execute("UPDATE ai_usage SET daily_count=0, last_reset_date=? WHERE user_id=?",
                  (today, user_id))
        conn.commit()
        row = (row[0], user_id, 0, today, row[4], row[5], row[6])
    conn.close()
    return {
        "daily_count": row[2],
        "total_count": row[4],
        "is_premium": row[5],
        "premium_until": row[6]
    }

def increment_ai_usage(user_id):
    today = _dt.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE ai_usage SET daily_count=daily_count+1, total_count=total_count+1,
                 last_reset_date=? WHERE user_id=?""", (today, user_id))
    conn.commit()
    conn.close()

def set_ai_premium(user_id, days=30):
    
    until = (_dt.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM ai_usage WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE ai_usage SET is_premium=1, premium_until=? WHERE user_id=?", (until, user_id))
    else:
        c.execute("INSERT INTO ai_usage (user_id, is_premium, premium_until) VALUES (?, 1, ?)", (user_id, until))
    conn.commit()
    conn.close()

# ===== پروفایل =====
def update_user_username(user_id, new_username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        conn.commit()
        conn.close()
        return True, "OK"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "این نام کاربری قبلاً استفاده شده"

def update_user_password(user_id, new_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()

def update_user_shop_name(user_id, shop_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET shop_name=? WHERE id=?", (shop_name, user_id))
    conn.commit()
    conn.close()

def update_user_phone(user_id, phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET phone=? WHERE id=?", (phone, user_id))
    conn.commit()
    conn.close()

def update_user_theme(user_id, theme):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # ستون theme رو اضافه کن اگه نیست
    try:
        c.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'neon'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    c.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
    conn.commit()
    conn.close()

def get_user_theme(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT theme FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] else "neon"
    except sqlite3.OperationalError:
        conn.close()
        return "neon"

# ===== چت بین کاربران =====
def init_dm_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS direct_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def send_dm(sender_id, receiver_id, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO direct_messages (sender_id, receiver_id, message)
                 VALUES (?, ?, ?)""", (sender_id, receiver_id, message))
    conn.commit()
    conn.close()

def get_conversation(user1, user2, limit=200):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT * FROM direct_messages
                 WHERE (sender_id=? AND receiver_id=?)
                    OR (sender_id=? AND receiver_id=?)
                 ORDER BY id ASC LIMIT ?""",
              (user1, user2, user2, user1, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_dm_read(user_id, other_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE direct_messages SET is_read=1
                 WHERE sender_id=? AND receiver_id=?""", (other_id, user_id))
    conn.commit()
    conn.close()

def get_dm_conversations(user_id):
    """لیست آخرین پیام با هر کاربر + آواتار"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name, u.status,
               (SELECT message FROM direct_messages
                WHERE (sender_id=? AND receiver_id=u.id)
                   OR (sender_id=u.id AND receiver_id=?)
                ORDER BY id DESC LIMIT 1) as last_msg,
               (SELECT created_at FROM direct_messages
                WHERE (sender_id=? AND receiver_id=u.id)
                   OR (sender_id=u.id AND receiver_id=?)
                ORDER BY id DESC LIMIT 1) as last_time,
               (SELECT COUNT(*) FROM direct_messages
                WHERE sender_id=u.id AND receiver_id=? AND is_read=0) as unread,
               (SELECT avatar_path FROM user_settings WHERE user_id=u.id)
        FROM users u
        WHERE u.id != ?
          AND u.id IN (
            SELECT CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END
            FROM direct_messages
            WHERE sender_id=? OR receiver_id=?
          )
        ORDER BY last_time DESC
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    rows = c.fetchall()
    conn.close()
    return rows

def search_users(query, exclude_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name,
                        (SELECT avatar_path FROM user_settings WHERE user_id=u.id)
                 FROM users u
                 WHERE u.id != ? AND (u.username LIKE ? OR u.shop_name LIKE ?)
                 LIMIT 20""",
              (exclude_id, f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return rows

def count_dm_unread(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM direct_messages WHERE receiver_id=? AND is_read=0", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

# ===== امنیت =====
def init_security_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # تلاش‌های ورود
    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        username TEXT,
        attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # تنظیمات کاربر (آواتار، پس‌زمینه)
    c.execute("""CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        avatar_path TEXT,
        bg_path TEXT,
        theme TEXT DEFAULT 'neon')""")
    conn.commit()
    conn.close()

def add_login_attempt(ip, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO login_attempts (ip, username) VALUES (?, ?)", (ip, username))
    conn.commit()
    conn.close()

def count_recent_attempts(ip, minutes=15):
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (_dt.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("SELECT COUNT(*) FROM login_attempts WHERE ip=? AND attempted_at > ?", (ip, since))
    n = c.fetchone()[0]
    conn.close()
    return n

def clear_login_attempts(ip):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM login_attempts WHERE ip=?", (ip,))
    conn.commit()
    conn.close()

_SETTINGS_CACHE = {}
_SETTINGS_CACHE_TIME = {}

def get_user_settings(user_id):
    """⚡ نسخه کش‌شده - 60 ثانیه اعتبار"""
    import time
    now = time.time()
    if user_id in _SETTINGS_CACHE and (now - _SETTINGS_CACHE_TIME.get(user_id, 0)) < 60:
        return _SETTINGS_CACHE[user_id]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM user_settings WHERE user_id=?", (user_id,))
        row = c.fetchone()
    except Exception:
        row = None
    conn.close()
    _SETTINGS_CACHE[user_id] = row
    _SETTINGS_CACHE_TIME[user_id] = now
    return row

def clear_settings_cache(user_id=None):
    global _SETTINGS_CACHE, _SETTINGS_CACHE_TIME
    if user_id:
        _SETTINGS_CACHE.pop(user_id, None)
        _SETTINGS_CACHE_TIME.pop(user_id, None)
    else:
        _SETTINGS_CACHE = {}
        _SETTINGS_CACHE_TIME = {}


def update_user_avatar(user_id, path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_settings WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE user_settings SET avatar_path=? WHERE user_id=?", (path, user_id))
    else:
        c.execute("INSERT INTO user_settings (user_id, avatar_path) VALUES (?, ?)", (user_id, path))
    conn.commit()
    conn.close()

def update_user_bg(user_id, path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_settings WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE user_settings SET bg_path=? WHERE user_id=?", (path, user_id))
    else:
        c.execute("INSERT INTO user_settings (user_id, bg_path) VALUES (?, ?)", (user_id, path))
    conn.commit()
    conn.close()

# ===== تنظیمات ادمین =====
ADMIN_ID = -1

def get_admin_settings():
    return get_user_settings(ADMIN_ID)

def update_admin_avatar(path):
    update_user_avatar(ADMIN_ID, path)

def update_admin_bg(path):
    update_user_bg(ADMIN_ID, path)

# ===== قابلیت‌های پیشرفته چت =====
def edit_chat_message(msg_id, new_text, user_id, is_admin=False):
    """ویرایش پیام (فقط پیام خودت)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if is_admin:
        c.execute("UPDATE chat_messages SET message=? WHERE id=? AND sender='admin'", (new_text, msg_id))
    else:
        c.execute("UPDATE chat_messages SET message=? WHERE id=? AND sender='shopkeeper' AND user_id=?",
                  (new_text, msg_id, user_id))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_chat_message(msg_id, user_id, is_admin=False):
    """حذف پیام"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if is_admin:
        c.execute("DELETE FROM chat_messages WHERE id=? AND sender='admin'", (msg_id,))
    else:
        c.execute("DELETE FROM chat_messages WHERE id=? AND sender='shopkeeper' AND user_id=?",
                  (msg_id, user_id))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def search_chat_messages(user_id, query, limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT * FROM chat_messages
                 WHERE user_id=? AND message LIKE ?
                 ORDER BY id DESC LIMIT ?""", (user_id, f"%{query}%", limit))
    rows = c.fetchall()
    conn.close()
    return rows

def clear_chat(user_id, is_admin=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if is_admin:
        c.execute("DELETE FROM chat_messages WHERE user_id=?", (user_id,))
    else:
        c.execute("DELETE FROM chat_messages WHERE user_id=? AND sender='shopkeeper'", (user_id,))
    conn.commit()
    conn.close()

# ===== نوتیفیکیشن =====
def init_notif_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        body TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def add_notification(user_id, title, body):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO notifications (user_id, title, body) VALUES (?, ?, ?)",
              (user_id, title, body))
    conn.commit()
    conn.close()

def get_notifications(user_id, limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT * FROM notifications WHERE user_id=?
                 ORDER BY id DESC LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_notif_read(notif_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (notif_id, user_id))
    conn.commit()
    conn.close()

def count_unread_notifs(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

def get_avatar_for_user(user_id):
    """گرفتن مسیر آواتار کاربر (ادمین = -1)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT avatar_path FROM user_settings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def get_admin_avatar():
    return get_avatar_for_user(-1)

def get_user_avatar(user_id):
    return get_avatar_for_user(user_id)

# ===== پرمیوم =====
def is_user_premium(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT is_premium, premium_until FROM ai_usage WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if not row or not row[0]:
            return {"active": False, "until": None}
        # چک کن هنوز معتبره
        if row[1]:
            try:
                until = _dt.strptime(row[1], "%Y-%m-%d").date()
                if until >= _dt.now().date():
                    return {"active": True, "until": row[1]}
                return {"active": False, "until": None}
            except:
                return {"active": False, "until": None}
        return {"active": False, "until": None}
    except:
        conn.close()
        return {"active": False, "until": None}

def get_premium_status(user_id):
    return is_user_premium(user_id)

def extend_premium(user_id, days=30):
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT premium_until FROM ai_usage WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row and row[0]:
        try:
            current = _dt.strptime(row[0], "%Y-%m-%d")
            if current < _dt.now():
                current = _dt.now()
        except:
            current = _dt.now()
    else:
        current = _dt.now()
    new_until = (current + timedelta(days=days)).strftime("%Y-%m-%d")
    c.execute("SELECT id FROM ai_usage WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE ai_usage SET is_premium=1, premium_until=? WHERE user_id=?", (new_until, user_id))
    else:
        c.execute("INSERT INTO ai_usage (user_id, is_premium, premium_until) VALUES (?, 1, ?)", (user_id, new_until))
    conn.commit()
    conn.close()
    return new_until

def revoke_premium(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE ai_usage SET is_premium=0, premium_until=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ===== درخواست چت =====
def init_chat_requests_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS chat_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER,
        to_id INTEGER,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(from_id, to_id))""")
    conn.commit()
    conn.close()

def send_chat_request(from_id, to_id):
    if from_id == to_id:
        return False, "نمی‌تونی به خودت درخواست بدی"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # چک کن قبلاً درخواست داده یا دوستن
    c.execute("""SELECT status FROM chat_requests
                 WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)""",
              (from_id, to_id, to_id, from_id))
    row = c.fetchone()
    if row:
        conn.close()
        if row[0] == 'accepted':
            return False, "شما قبلاً دوست هستید"
        elif row[0] == 'pending':
            return False, "درخواست قبلاً ارسال شده"
        elif row[0] == 'rejected':
            # اجازه بده دوباره بفرسته
            c.execute("DELETE FROM chat_requests WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
                      (from_id, to_id, to_id, from_id))
    try:
        c.execute("INSERT INTO chat_requests (from_id, to_id) VALUES (?, ?)", (from_id, to_id))
        conn.commit()
        conn.close()
        return True, "درخواست ارسال شد"
    except Exception as e:
        conn.close()
        return False, str(e)

def get_incoming_requests(user_id):
    """درخواست‌های دریافتی"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT r.id, r.from_id, u.username, u.shop_name,
                        (SELECT avatar_path FROM user_settings WHERE user_id=u.id),
                        r.created_at
                 FROM chat_requests r
                 JOIN users u ON u.id = r.from_id
                 WHERE r.to_id=? AND r.status='pending'
                 ORDER BY r.id DESC""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_outgoing_requests(user_id):
    """درخواست‌های ارسالی"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT r.id, r.to_id, u.username, u.shop_name,
                        (SELECT avatar_path FROM user_settings WHERE user_id=u.id),
                        r.created_at, r.status
                 FROM chat_requests r
                 JOIN users u ON u.id = r.to_id
                 WHERE r.from_id=?
                 ORDER BY r.id DESC""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def accept_request(req_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE chat_requests SET status='accepted' WHERE id=? AND to_id=?", (req_id, user_id))
    conn.commit()
    conn.close()

def reject_request(req_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE chat_requests SET status='rejected' WHERE id=? AND to_id=?", (req_id, user_id))
    conn.commit()
    conn.close()

def delete_request(req_id, user_id):
    """حذف درخواست توسط فرستنده"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM chat_requests WHERE id=? AND from_id=?", (req_id, user_id))
    conn.commit()
    conn.close()

def are_friends(user1, user2):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT id FROM chat_requests
                 WHERE ((from_id=? AND to_id=?) OR (from_id=? AND to_id=?))
                 AND status='accepted'""", (user1, user2, user2, user1))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_friends(user_id):
    """لیست دوستان قبول‌شده"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name,
               (SELECT avatar_path FROM user_settings WHERE user_id=u.id),
               (SELECT message FROM direct_messages
                WHERE (sender_id=? AND receiver_id=u.id)
                   OR (sender_id=u.id AND receiver_id=?)
                ORDER BY id DESC LIMIT 1),
               (SELECT created_at FROM direct_messages
                WHERE (sender_id=? AND receiver_id=u.id)
                   OR (sender_id=u.id AND receiver_id=?)
                ORDER BY id DESC LIMIT 1),
               (SELECT COUNT(*) FROM direct_messages
                WHERE sender_id=u.id AND receiver_id=? AND is_read=0)
        FROM users u
        WHERE u.id != ?
          AND u.id IN (
              SELECT CASE WHEN from_id=? THEN to_id ELSE from_id END
              FROM chat_requests
              WHERE (from_id=? OR to_id=?) AND status='accepted'
          )
        ORDER BY (SELECT id FROM direct_messages
                  WHERE (sender_id=? AND receiver_id=u.id)
                     OR (sender_id=u.id AND receiver_id=?)
                  ORDER BY id DESC LIMIT 1) DESC
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    rows = c.fetchall()
    conn.close()
    return rows

def search_users_advanced(query, exclude_id):
    """جستجو با آیدی عددی یا نام کاربری"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if query.isdigit():
        c.execute("""SELECT u.id, u.username, u.shop_name,
                            (SELECT avatar_path FROM user_settings WHERE user_id=u.id),
                            (SELECT status FROM chat_requests
                             WHERE ((from_id=? AND to_id=u.id) OR (from_id=u.id AND to_id=?))
                             LIMIT 1)
                     FROM users u
                     WHERE u.id = ? AND u.id != ?""",
                  (exclude_id, exclude_id, int(query), exclude_id))
    else:
        c.execute("""SELECT u.id, u.username, u.shop_name,
                            (SELECT avatar_path FROM user_settings WHERE user_id=u.id),
                            (SELECT status FROM chat_requests
                             WHERE ((from_id=? AND to_id=u.id) OR (from_id=u.id AND to_id=?))
                             LIMIT 1)
                     FROM users u
                     WHERE u.id != ? AND (u.username LIKE ? OR u.shop_name LIKE ?)
                     LIMIT 20""",
                  (exclude_id, exclude_id, exclude_id, f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return rows

def count_pending_requests(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM chat_requests WHERE to_id=? AND status='pending'", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

# ===== همه پیام‌های کاربر =====
def get_all_user_messages(user_id, limit=100):
    """
    همه پیام‌هایی که کاربر توش درگیره:
    - چت با ادمین
    - چت با دوستان
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    messages = []

    # 1) چت با ادمین
    c.execute("""SELECT id, sender, message, created_at, 'admin' as chat_type, NULL as other_id
                 FROM chat_messages WHERE user_id=?
                 ORDER BY id DESC LIMIT ?""", (user_id, limit))
    for r in c.fetchall():
        sender_label = "👑 پشتیبانی" if r[1] == 'admin' else "🏪 من"
        is_mine = (r[1] == 'shopkeeper')
        messages.append({
            "id": f"adm_{r[0]}",
            "type": "admin",
            "sender": sender_label,
            "text": r[2],
            "time": r[3],
            "is_mine": is_mine,
            "other_id": None
        })

    # 2) چت با کاربران (فقط دوستانی که تایید شدن)
    c.execute("""
        SELECT dm.id, dm.sender_id, dm.receiver_id, dm.message, dm.created_at,
               CASE WHEN dm.sender_id=? THEN dm.receiver_id ELSE dm.sender_id END as other
        FROM direct_messages dm
        WHERE (dm.sender_id=? OR dm.receiver_id=?)
          AND (
              CASE WHEN dm.sender_id=? THEN dm.receiver_id ELSE dm.sender_id END
          ) IN (
              SELECT CASE WHEN from_id=? THEN to_id ELSE from_id END
              FROM chat_requests
              WHERE (from_id=? OR to_id=?) AND status='accepted'
          )
        ORDER BY dm.id DESC LIMIT ?
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, limit))
    for r in c.fetchall():
        other_id = r[5]
        is_mine = (r[1] == user_id)
        # اسم طرف مقابل
        c2 = conn.cursor()
        c2.execute("SELECT username, shop_name FROM users WHERE id=?", (other_id,))
        ou = c2.fetchone()
        other_name = (ou[1] or ou[0]) if ou else f"کاربر #{other_id}"
        messages.append({
            "id": f"dm_{r[0]}",
            "type": "personal",
            "sender": ("👤 من" if is_mine else f"💬 {other_name}"),
            "text": r[3],
            "time": r[4],
            "is_mine": is_mine,
            "other_id": other_id
        })

    conn.close()
    # مرتب‌سازی بر اساس زمان
    messages.sort(key=lambda x: x["time"], reverse=True)
    return messages[:limit]

def get_message_counts(user_id):
    """تعداد پیام‌ها به تفکیک نوع"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # چت با ادمین
    c.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id=?", (user_id,))
    admin_count = c.fetchone()[0]

    # چت شخصی
    c.execute("""
        SELECT COUNT(*) FROM direct_messages
        WHERE sender_id=? OR receiver_id=?
    """, (user_id, user_id))
    personal_count = c.fetchone()[0]

    # چت با مغازه‌دارها (دوستان - شخصی)
    c.execute("""
        SELECT COUNT(*) FROM direct_messages
        WHERE (sender_id=? OR receiver_id=?)
    """, (user_id, user_id))
    shopkeeper_count = personal_count  # موقتاً همون

    conn.close()
    return {
        "all": admin_count + personal_count,
        "admin": admin_count,
        "personal": personal_count,
        "shopkeeper": shopkeeper_count,
        "group": 0  # فعلاً گروه نداریم
    }

def get_all_user_messages_v2(user_id, limit=100):
    """همه پیام‌ها با آواتار و اطلاعات کامل"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    messages = []

    # آواتار خود کاربر
    c.execute("SELECT avatar_path, username, shop_name FROM user_settings s JOIN users u ON u.id=s.user_id WHERE u.id=?", (user_id,))
    row = c.fetchone()
    my_avatar = row[0] if row else None
    c.execute("SELECT username, shop_name FROM users WHERE id=?", (user_id,))
    ur = c.fetchone()
    my_name = (ur[1] or ur[0]) if ur else "من"

    # آواتار ادمین
    c.execute("SELECT avatar_path FROM user_settings WHERE user_id=-1")
    row = c.fetchone()
    admin_avatar = row[0] if row and row[0] else None

    # 1) چت با ادمین
    c.execute("""SELECT id, sender, message, created_at
                 FROM chat_messages WHERE user_id=?
                 ORDER BY id DESC LIMIT ?""", (user_id, limit))
    for r in c.fetchall():
        is_mine = (r[1] == 'shopkeeper')
        messages.append({
            "id": f"adm_{r[0]}",
            "type": "admin",
            "sender_name": my_name if is_mine else "Creator",
            "sender_avatar": my_avatar if is_mine else admin_avatar,
            "text": r[2],
            "time": r[3],
            "is_mine": is_mine,
            "other_id": None,
            "chat_link": "/panel/chat"
        })

    # 2) چت شخصی
    c.execute("""
        SELECT dm.id, dm.sender_id, dm.receiver_id, dm.message, dm.created_at,
               CASE WHEN dm.sender_id=? THEN dm.receiver_id ELSE dm.sender_id END as other
        FROM direct_messages dm
        WHERE (dm.sender_id=? OR dm.receiver_id=?)
          AND (CASE WHEN dm.sender_id=? THEN dm.receiver_id ELSE dm.sender_id END)
          IN (SELECT CASE WHEN from_id=? THEN to_id ELSE from_id END
              FROM chat_requests WHERE (from_id=? OR to_id=?) AND status='accepted')
        ORDER BY dm.id DESC LIMIT ?
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, limit))

    for r in c.fetchall():
        other_id = r[5]
        is_mine = (r[1] == user_id)
        c2 = conn.cursor()
        c2.execute("""SELECT u.username, u.shop_name,
                             (SELECT avatar_path FROM user_settings WHERE user_id=u.id)
                      FROM users u WHERE u.id=?""", (other_id,))
        ou = c2.fetchone()
        if ou:
            other_name = ou[1] or ou[0]
            other_avatar = ou[2]
        else:
            other_name = f"کاربر #{other_id}"
            other_avatar = None
        messages.append({
            "id": f"dm_{r[0]}",
            "type": "personal",
            "sender_name": my_name if is_mine else other_name,
            "sender_avatar": my_avatar if is_mine else other_avatar,
            "text": r[3],
            "time": r[4],
            "is_mine": is_mine,
            "other_id": other_id,
            "chat_link": f"/panel/dm/{other_id}"
        })

    conn.close()
    messages.sort(key=lambda x: x["time"], reverse=True)
    return messages[:limit]

def get_all_conversations(user_id):
    """همه چت‌های کاربر (پی‌وی‌ها)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    conversations = []

    # آواتار خود کاربر
    c.execute("SELECT avatar_path FROM user_settings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    my_avatar = row[0] if row and row[0] else None

    # آواتار ادمین
    c.execute("SELECT avatar_path FROM user_settings WHERE user_id=-1")
    row = c.fetchone()
    admin_avatar = row[0] if row and row[0] else None

    # 1) چت با پشتیبانی (اگه پیامی هست)
    c.execute("""SELECT COUNT(*), MAX(created_at),
                 (SELECT message FROM chat_messages WHERE user_id=? ORDER BY id DESC LIMIT 1),
                 (SELECT COUNT(*) FROM chat_messages WHERE user_id=? AND sender='admin' AND is_read=0)
                 FROM chat_messages WHERE user_id=?""", (user_id, user_id, user_id))
    r = c.fetchone()
    if r and r[0] > 0:
        conversations.append({
            "type": "admin",
            "id": "admin",
            "name": "Creator",
            "avatar": admin_avatar,
            "last_msg": r[2] or "",
            "last_time": r[1] or "",
            "unread": r[3] or 0,
            "link": "/panel/chat",
            "icon": "👑"
        })

    # 2) چت‌های شخصی با دوستان
    c.execute("""
        SELECT dm.id, dm.sender_id, dm.receiver_id, dm.message, dm.created_at,
               CASE WHEN dm.sender_id=? THEN dm.receiver_id ELSE dm.sender_id END as other
        FROM direct_messages dm
        WHERE (dm.sender_id=? OR dm.receiver_id=?)
        ORDER BY dm.id DESC
    """, (user_id, user_id, user_id))

    seen = set()
    for r in c.fetchall():
        other_id = r[5]
        if other_id in seen:
            continue
        seen.add(other_id)

        # چک دوست بودن
        c2 = conn.cursor()
        c2.execute("""SELECT status FROM chat_requests
                     WHERE ((from_id=? AND to_id=?) OR (from_id=? AND to_id=?))
                     AND status='accepted'""",
                  (user_id, other_id, other_id, user_id))
        if not c2.fetchone():
            continue

        c2.execute("""SELECT u.username, u.shop_name,
                             (SELECT avatar_path FROM user_settings WHERE user_id=u.id)
                      FROM users u WHERE u.id=?""", (other_id,))
        ou = c2.fetchone()
        if not ou:
            continue
        name = ou[1] or ou[0]
        avatar = ou[2]

        # تعداد پیام‌های نخوانده
        c2.execute("SELECT COUNT(*) FROM direct_messages WHERE sender_id=? AND receiver_id=? AND is_read=0",
                   (other_id, user_id))
        unread = c2.fetchone()[0]

        conversations.append({
            "type": "personal",
            "id": other_id,
            "name": name,
            "avatar": avatar,
            "last_msg": r[3] or "",
            "last_time": r[4] or "",
            "unread": unread,
            "link": f"/panel/dm/{other_id}",
            "icon": "🏪"
        })

    conn.close()
    # مرتب‌سازی بر اساس زمان آخرین پیام
    conversations.sort(key=lambda x: x["last_time"], reverse=True)
    return conversations

def get_conversation_counts(user_id):
    """تعداد چت‌ها به تفکیک نوع"""
    convs = get_all_conversations(user_id)
    return {
        "all": len(convs),
        "admin": sum(1 for c in convs if c["type"] == "admin"),
        "personal": sum(1 for c in convs if c["type"] == "personal"),
        "group": 0
    }

# ===== مخاطبین =====
def init_contacts_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, name TEXT, phone TEXT,
        group_name TEXT DEFAULT 'معمولی', notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def add_contact(user_id, name, phone, group_name="معمولی", notes=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO contacts (user_id, name, phone, group_name, notes) VALUES (?, ?, ?, ?, ?)",
              (user_id, name, phone, group_name, notes))
    nid = c.lastrowid
    conn.commit()
    conn.close()
    return nid

def get_user_contacts(user_id, search="", group_filter=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q = "SELECT * FROM contacts WHERE user_id=?"
    p = [user_id]
    if search:
        q += " AND (name LIKE ? OR phone LIKE ?)"
        p.extend([f"%{search}%", f"%{search}%"])
    if group_filter:
        q += " AND group_name=?"
        p.append(group_filter)
    q += " ORDER BY name ASC"
    c.execute(q, p)
    rows = c.fetchall()
    conn.close()
    return rows

def get_contact(contact_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM contacts WHERE id=? AND user_id=?", (contact_id, user_id))
    r = c.fetchone()
    conn.close()
    return r

def update_contact(contact_id, user_id, name, phone, group_name, notes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE contacts SET name=?, phone=?, group_name=?, notes=? WHERE id=? AND user_id=?",
              (name, phone, group_name, notes, contact_id, user_id))
    conn.commit()
    conn.close()

def delete_contact(contact_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE id=? AND user_id=?", (contact_id, user_id))
    conn.commit()
    conn.close()

def get_contact_groups(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT group_name, COUNT(*) FROM contacts WHERE user_id=? GROUP BY group_name ORDER BY group_name", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"name": r[0], "count": r[1]} for r in rows]

def count_contacts(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM contacts WHERE user_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

def import_contacts(user_id, contacts_list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    added = 0
    for ct in contacts_list:
        try:
            c.execute("INSERT INTO contacts (user_id, name, phone, group_name, notes) VALUES (?, ?, ?, ?, ?)",
                      (user_id, ct.get("name", ""), ct.get("phone", ""), ct.get("group", "معمولی"), ct.get("notes", "")))
            added += 1
        except:
            pass
    conn.commit()
    conn.close()
    return added

# ===== قالب‌های پیامک =====
def init_templates_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sms_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, title TEXT, body TEXT,
        category TEXT DEFAULT 'عمومی', use_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def add_template(user_id, title, body, category="عمومی"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sms_templates (user_id, title, body, category) VALUES (?, ?, ?, ?)",
              (user_id, title, body, category))
    nid = c.lastrowid
    conn.commit()
    conn.close()
    return nid

def get_user_templates(user_id, category=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM sms_templates WHERE user_id=? AND category=? ORDER BY use_count DESC", (user_id, category))
    else:
        c.execute("SELECT * FROM sms_templates WHERE user_id=? ORDER BY use_count DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_template(template_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM sms_templates WHERE id=? AND user_id=?", (template_id, user_id))
    r = c.fetchone()
    conn.close()
    return r

def update_template(template_id, user_id, title, body, category):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE sms_templates SET title=?, body=?, category=? WHERE id=? AND user_id=?",
              (title, body, category, template_id, user_id))
    conn.commit()
    conn.close()

def delete_template(template_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sms_templates WHERE id=? AND user_id=?", (template_id, user_id))
    conn.commit()
    conn.close()

def increment_template_use(template_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE sms_templates SET use_count=use_count+1 WHERE id=? AND user_id=?", (template_id, user_id))
    conn.commit()
    conn.close()

def count_templates(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sms_templates WHERE user_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

def get_template_categories(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT category, COUNT(*) FROM sms_templates WHERE user_id=? GROUP BY category ORDER BY category", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"name": r[0], "count": r[1]} for r in rows]

# ===== بکاپ =====
def init_backup_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT, size INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        type TEXT DEFAULT 'manual', status TEXT DEFAULT 'success')""")
    conn.commit()
    conn.close()

def log_backup(filename, size, backup_type="manual", status="success"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO backups (filename, size, type, status) VALUES (?, ?, ?, ?)",
              (filename, size, backup_type, status))
    conn.commit()
    conn.close()

def get_backup_history(limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM backups ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def count_backups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM backups")
    n = c.fetchone()[0]
    conn.close()
    return n

def delete_backup_record(backup_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM backups WHERE id=?", (backup_id,))
    conn.commit()
    conn.close()

def clear_old_backups(keep=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM backups WHERE id NOT IN (SELECT id FROM backups ORDER BY id DESC LIMIT ?)", (keep,))
    conn.commit()
    conn.close()

# ===== آمار =====
def get_sms_stats_by_day(days=7, user_id=None):
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    result = []
    for i in range(days-1, -1, -1):
        d = (_dt.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if user_id:
            c.execute("SELECT COUNT(*) FROM sent_sms WHERE DATE(created_at)=? AND user_id=?", (d, user_id))
        else:
            c.execute("SELECT COUNT(*) FROM sent_sms WHERE DATE(created_at)=?", (d,))
        result.append({"date": d, "count": c.fetchone()[0]})
    conn.close()
    return result

def get_sms_stats_by_hour():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    result = []
    for h in range(24):
        c.execute("SELECT COUNT(*) FROM sent_sms WHERE strftime('%H', created_at)=?", (f"{h:02d}",))
        result.append({"hour": h, "count": c.fetchone()[0]})
    conn.close()
    return result

def get_top_users(limit=5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name,
                 (SELECT COUNT(*) FROM sent_sms WHERE user_id=u.id) as cnt
                 FROM users u ORDER BY cnt DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "shop": r[2], "count": r[3]} for r in rows]

def get_status_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM sent_sms GROUP BY status")
    rows = c.fetchall()
    conn.close()
    return [{"status": r[0] or "unknown", "count": r[1]} for r in rows]

def get_monthly_revenue():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""SELECT strftime('%Y-%m', premium_until), COUNT(*)
                     FROM ai_usage WHERE is_premium=1
                     GROUP BY strftime('%Y-%m', premium_until)
                     ORDER BY premium_until DESC LIMIT 6""")
        rows = c.fetchall()
    except:
        rows = []
    conn.close()
    return [{"month": r[0] or "نامشخص", "count": r[1]} for r in rows]

# ===== نوتیفیکیشن =====
def create_notification(user_id, title, body, icon="🔔", link=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO notifications (user_id, title, body, icon, link) VALUES (?, ?, ?, ?, ?)",
              (user_id, title, body, icon, link))
    conn.commit()
    conn.close()

def get_user_notifications(user_id, limit=30):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_all_read(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def delete_notification(notif_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM notifications WHERE id=? AND user_id=?", (notif_id, user_id))
    conn.commit()
    conn.close()

def clear_user_notifications(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM notifications WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def count_unread_notifications(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

def notify_all_users(title, body, icon="🔔", link=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    ids = [r[0] for r in c.fetchall()]
    for uid in ids:
        c.execute("INSERT INTO notifications (user_id, title, body, icon, link) VALUES (?, ?, ?, ?, ?)",
                  (uid, title, body, icon, link))
    conn.commit()
    conn.close()
    return len(ids)

# ===== QR =====
def log_qr_scan(user_id, phone, name=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO qr_scans (user_id, phone, name) VALUES (?, ?, ?)",
              (user_id, phone, name))
    conn.commit()
    conn.close()

def get_qr_scans(user_id, limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM qr_scans WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def count_qr_scans(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM qr_scans WHERE user_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

# ==================== WALLET / کیف پول ====================

def get_wallet(user_id):
    conn = sqlite3.connect(DB_PATH) if 'DB_PATH' in dir() else sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM wallets WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO wallets (user_id, balance) VALUES (?, 0)", (user_id,))
        conn.commit()
        balance = 0
    else:
        balance = row[0]
    conn.close()
    return balance or 0

def charge_wallet(user_id, amount, description="شارژ دستی"):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM wallets WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO wallets (user_id, balance) VALUES (?, 0)", (user_id,))
        current = 0
    else:
        current = row[0] or 0
    new_balance = current + amount
    c.execute("UPDATE wallets SET balance=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
              (new_balance, user_id))
    c.execute("INSERT INTO transactions (user_id, amount, type, description, balance_after) VALUES (?,?,?,?,?)",
              (user_id, amount, 'charge', description, new_balance))
    conn.commit()
    conn.close()
    return new_balance

def deduct_wallet(user_id, amount, description="کسر"):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM wallets WHERE user_id=?", (user_id,))
    row = c.fetchone()
    current = row[0] if row else 0
    if current < amount:
        conn.close()
        return False
    new_balance = current - amount
    c.execute("UPDATE wallets SET balance=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
              (new_balance, user_id))
    c.execute("INSERT INTO transactions (user_id, amount, type, description, balance_after) VALUES (?,?,?,?,?)",
              (user_id, -amount, 'deduct', description, new_balance))
    conn.commit()
    conn.close()
    return True

def get_transactions(user_id, limit=50):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, amount, type, description, balance_after, created_at FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT ?",
              (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_wallets():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name, COALESCE(w.balance, 0)
        FROM users u
        LEFT JOIN wallets w ON w.user_id = u.id
        ORDER BY u.id
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# ==================== PAYMENTS / درگاه پرداخت ====================

def get_setting(key, default=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def create_payment(user_id, amount, authority=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO payments (user_id, amount, authority, status) VALUES (?, ?, ?, 'pending')",
              (user_id, amount, authority))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid

def set_payment_authority(payment_id, authority):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE payments SET authority=? WHERE id=?", (authority, payment_id))
    conn.commit()
    conn.close()

def get_payment_by_authority(authority):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, authority, ref_id, status, created_at FROM payments WHERE authority=? ORDER BY id DESC LIMIT 1",
              (authority,))
    row = c.fetchone()
    conn.close()
    return row

def get_payment(payment_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, authority, ref_id, status, created_at FROM payments WHERE id=?",
              (payment_id,))
    row = c.fetchone()
    conn.close()
    return row

def mark_payment_verified(payment_id, ref_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE payments SET status='verified', ref_id=?, verified_at=CURRENT_TIMESTAMP WHERE id=?",
              (str(ref_id), payment_id))
    conn.commit()
    conn.close()

def mark_payment_failed(payment_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE payments SET status='failed' WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()

def get_user_payments(user_id, limit=30):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, amount, status, ref_id, created_at FROM payments WHERE user_id=? ORDER BY id DESC LIMIT ?",
              (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

# ==================== TICKETS / تیکت پشتیبانی ====================

def create_ticket(user_id, subject, message, priority='normal'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO tickets (user_id, subject, priority) VALUES (?, ?, ?)",
              (user_id, subject, priority))
    tid = c.lastrowid
    c.execute("INSERT INTO ticket_replies (ticket_id, sender, message) VALUES (?, 'user', ?)",
              (tid, message))
    conn.commit()
    conn.close()
    return tid

def get_user_tickets(user_id, limit=100):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT t.id, t.subject, t.priority, t.status, t.created_at, t.updated_at,
               (SELECT COUNT(*) FROM ticket_replies r WHERE r.ticket_id = t.id) AS replies
        FROM tickets t WHERE t.user_id = ?
        ORDER BY t.updated_at DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_tickets(limit=300, status_filter=None):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    base = """
        SELECT t.id, t.user_id, u.username, u.shop_name, t.subject, t.priority,
               t.status, t.created_at, t.updated_at,
               (SELECT COUNT(*) FROM ticket_replies r WHERE r.ticket_id = t.id) AS replies
        FROM tickets t LEFT JOIN users u ON u.id = t.user_id
    """
    if status_filter:
        c.execute(base + " WHERE t.status = ? ORDER BY t.updated_at DESC LIMIT ?",
                  (status_filter, limit))
    else:
        c.execute(base + " ORDER BY t.updated_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_ticket(ticket_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT t.id, t.user_id, u.username, u.shop_name, t.subject, t.priority,
               t.status, t.created_at, t.updated_at
        FROM tickets t LEFT JOIN users u ON u.id = t.user_id WHERE t.id = ?
    """, (ticket_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_ticket_replies(ticket_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, sender, message, created_at FROM ticket_replies WHERE ticket_id = ? ORDER BY id ASC",
              (ticket_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_ticket_reply(ticket_id, sender, message):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO ticket_replies (ticket_id, sender, message) VALUES (?, ?, ?)",
              (ticket_id, sender, message))
    if sender == 'admin':
        c.execute("UPDATE tickets SET status='answered', updated_at=CURRENT_TIMESTAMP WHERE id=?", (ticket_id,))
    else:
        c.execute("UPDATE tickets SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()

def update_ticket_status(ticket_id, status):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE tickets SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
              (status, ticket_id))
    conn.commit()
    conn.close()

def count_open_tickets():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tickets WHERE status='open'")
    n = c.fetchone()[0]
    conn.close()
    return n

def count_user_unread_tickets(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tickets WHERE user_id=? AND status='answered'", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

# ==================== LOYALTY / باشگاه مشتریان ====================

TIERS = [
    ('diamond', 5000, '💎', 'الماس'),
    ('gold',    2000, '🥇', 'طلا'),
    ('silver',  500,  '🥈', 'نقره'),
    ('bronze',  0,    '🥉', 'برنز'),
]

def _tier_of(total):
    for key, mn, ic, fa in TIERS:
        if total >= mn:
            return key
    return 'bronze'

def get_loyalty(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT points, total_points, tier, free_sms, birthday FROM loyalty WHERE user_id=?",
              (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO loyalty (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = (0, 0, 'bronze', 0, '')
    conn.close()
    return {
        'points': row[0] or 0,
        'total_points': row[1] or 0,
        'tier': row[2] or 'bronze',
        'free_sms': row[3] or 0,
        'birthday': row[4] or '',
    }

def add_loyalty_points(user_id, n, note=''):
    """n می‌تونه مثبت یا منفی باشه"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT points, total_points FROM loyalty WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO loyalty (user_id, points, total_points) VALUES (?, ?, ?)",
                  (user_id, max(n, 0), max(n, 0)))
        cur_pts, tot_pts = max(n, 0), max(n, 0)
    else:
        cur_pts = (row[0] or 0) + n
        if cur_pts < 0: cur_pts = 0
        tot_pts = (row[1] or 0) + max(n, 0)
        c.execute("UPDATE loyalty SET points=?, total_points=? WHERE user_id=?",
                  (cur_pts, tot_pts, user_id))
    new_tier = _tier_of(tot_pts)
    c.execute("UPDATE loyalty SET tier=? WHERE user_id=?", (new_tier, user_id))
    c.execute("INSERT INTO loyalty_log (user_id, action, points, note) VALUES (?, ?, ?, ?)",
              (user_id, 'add' if n >= 0 else 'deduct', n, note))
    conn.commit()
    conn.close()
    return cur_pts, tot_pts, new_tier

def redeem_points(user_id, cost=100, reward_sms=10):
    """۱۰۰ امتیاز = ۱۰ پیامک رایگان"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT points, free_sms FROM loyalty WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row or (row[0] or 0) < cost:
        conn.close()
        return False, 'امتیاز کافی نداری'
    new_pts = (row[0] or 0) - cost
    new_free = (row[1] or 0) + reward_sms
    c.execute("UPDATE loyalty SET points=?, free_sms=? WHERE user_id=?",
              (new_pts, new_free, user_id))
    c.execute("INSERT INTO loyalty_log (user_id, action, points, note) VALUES (?, 'redeem', ?, ?)",
              (user_id, -cost, f'{reward_sms} پیامک رایگان'))
    conn.commit()
    conn.close()
    return True, f'✅ {reward_sms} پیامک رایگان گرفتی!'

def use_free_sms(user_id, count=1):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT free_sms FROM loyalty WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row or (row[0] or 0) < count:
        conn.close()
        return False
    c.execute("UPDATE loyalty SET free_sms=free_sms-? WHERE user_id=?", (count, user_id))
    conn.commit()
    conn.close()
    return True

def get_loyalty_log(user_id, limit=30):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT action, points, note, created_at FROM loyalty_log
                 WHERE user_id=? ORDER BY id DESC LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_loyalty():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name,
               COALESCE(l.points,0), COALESCE(l.total_points,0),
               COALESCE(l.tier,'bronze'), COALESCE(l.free_sms,0)
        FROM users u LEFT JOIN loyalty l ON l.user_id = u.id
        ORDER BY l.total_points DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def set_user_birthday(user_id, birthday):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO loyalty (user_id) VALUES (?)", (user_id,))
    c.execute("UPDATE loyalty SET birthday=? WHERE user_id=?", (birthday, user_id))
    conn.commit()
    conn.close()

def count_tier_users():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT tier, COUNT(*) FROM loyalty GROUP BY tier")
    rows = dict(c.fetchall())
    conn.close()
    return rows

def check_birthday_bonus(user_id):
    """اگه امروز تولدشه، ۱۰۰ امتیاز هدیه"""
    l = get_loyalty(user_id)
    if not l['birthday']:
        return False
    try:
        bd = l['birthday']  # فرمت: MM-DD یا YYYY-MM-DD
        today = _dt.now().strftime('%m-%d')
        if bd.endswith(today) or bd == today:
            # چک کن قبلاً امروز نگرفته
            conn = sqlite3.connect('panel.db')
            c = conn.cursor()
            c.execute("""SELECT COUNT(*) FROM loyalty_log
                         WHERE user_id=? AND action='birthday' AND DATE(created_at)=DATE('now')""",
                      (user_id,))
            got = c.fetchone()[0]
            conn.close()
            if got == 0:
                add_loyalty_points(user_id, 100, '🎂 هدیه تولد')
                return True
    except Exception:
        pass
    return False

def is_double_points_day():
    """آخر هفته (پنجشنبه و جمعه) امتیاز ۲ برابر"""
    wd = _dt.now().weekday()  # 0=دوشنبه
    return wd in (3, 4)  # پنجشنبه=3, جمعه=4

def loyalty_multiplier():
    return 2 if is_double_points_day() else 1


# ==================== REFERRAL / سیستم ارجاع ====================
import secrets as _secrets, string as _string

REFERRER_BONUS_POINTS = 50
REFERRER_BONUS_CASH = 50000
REFERRED_BONUS_POINTS = 25
REFERRED_BONUS_CASH = 25000


def _gen_ref_code(username):
    prefix = ''.join(ch for ch in (username or 'USER')[:4].upper() if ch.isalnum()) or 'USER'
    for _ in range(20):
        rand = ''.join(_secrets.choice(_string.ascii_uppercase + _string.digits) for _ in range(4))
        code = f"{prefix}-{rand}"
        conn = sqlite3.connect('panel.db')
        c = conn.cursor()
        c.execute("SELECT 1 FROM referral_codes WHERE code=?", (code,))
        exists = c.fetchone()
        conn.close()
        if not exists:
            return code
    return None


def get_or_create_referral_code(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT code FROM referral_codes WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0]
    c.execute("SELECT username FROM users WHERE id=?", (user_id,))
    u = c.fetchone()
    conn.close()
    uname = u[0] if u else 'USER'
    new_code = _gen_ref_code(uname)
    if not new_code:
        return None
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO referral_codes (user_id, code) VALUES (?, ?)", (user_id, new_code))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return new_code


def find_user_by_ref_code(code):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM referral_codes WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def process_referral(referrer_id, referred_id, code):
    """وقتی کاربر جدید با کد دعوت ثبت‌نام کرد"""
    if referrer_id == referred_id:
        return False
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    # چک نکن قبلاً ثبت شده
    c.execute("SELECT 1 FROM referrals WHERE referred_id=?", (referred_id,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO referrals (referrer_id, referred_id, code, reward_given) VALUES (?, ?, ?, 1)",
              (referrer_id, referred_id, code))
    conn.commit()
    conn.close()

    # 🎁 پاداش دعوت‌کننده
    try:
        add_loyalty_points(referrer_id, REFERRER_BONUS_POINTS, f'🎯 دعوت موفق ({code})')
    except Exception:
        pass
    try:
        charge_wallet(referrer_id, REFERRER_BONUS_CASH, f'🎁 پاداش دعوت ({code})')
    except Exception:
        pass

    # 🎁 پاداش دعوت‌شده
    try:
        add_loyalty_points(referred_id, REFERRED_BONUS_POINTS, f'🎯 ثبت‌نام با کد دعوت')
    except Exception:
        pass
    try:
        charge_wallet(referred_id, REFERRED_BONUS_CASH, f'🎁 هدیه خوش‌آمدگویی')
    except Exception:
        pass

    return True


def get_user_referrals(user_id):
    """آمار ارجاع کاربر"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT r.id, u.username, u.shop_name, r.created_at
        FROM referrals r
        LEFT JOIN users u ON u.id = r.referred_id
        WHERE r.referrer_id = ?
        ORDER BY r.id DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def count_referrals(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


def get_top_referrers(limit=10):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name, COUNT(r.id) AS cnt,
               SUM(CASE WHEN r.reward_given=1 THEN 1 ELSE 0 END) AS rewarded
        FROM users u
        LEFT JOIN referrals r ON r.referrer_id = u.id
        GROUP BY u.id
        HAVING cnt > 0
        ORDER BY cnt DESC, u.id ASC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


# ==================== NOTIFY HELPERS / اعلان‌های خودکار ====================

def notify(user_id, title, body, icon='🔔', link=''):
    try:
        return create_notification(user_id, title, body, icon, link)
    except Exception:
        return None


def notify_ticket_reply(user_id, ticket_id, subject):
    return notify(user_id,
        'پاسخ تیکت شما',
        f'ادمین به تیکت «{subject}» جواب داد',
        '🎫', f'/panel/tickets/{ticket_id}')


def notify_ticket_new(ticket_id, subject, username):
    """اطلاع به همه ادمین‌ها — فعلاً فقط یه ادمین داریم، به user_id=1"""
    try:
        return notify(1,
            'تیکت جدید',
            f'{username} یه تیکت جدید فرستاد: {subject}',
            '🎫', f'/admin/tickets/{ticket_id}')
    except Exception:
        return None


def notify_reward_ready(user_id):
    return notify(user_id,
        '🎁 جایزه آماده‌ست!',
        'به ۱۰۰ امتیاز رسیدی — ۱۰ پیامک رایگان بگیر',
        '🎁', '/panel/loyalty')


def notify_referral_success(referrer_id, referred_username, cash, pts):
    return notify(referrer_id,
        '🎯 دعوت موفق!',
        f'{referred_username} با کد تو ثبت‌نام کرد. {cash:,} ریال + {pts} امتیاز گرفتی',
        '🎯', '/panel/referrals')


def notify_wallet_charge(user_id, amount, by='ادمین'):
    return notify(user_id,
        '💰 کیف پول شارژ شد',
        f'{amount:,} ریال توسط {by} به کیف پولت اضافه شد',
        '💰', '/panel/wallet')


def notify_wallet_sms_paid(user_id, amount, remaining):
    """وقتی از کیف پول کسر شد (اختیاری — می‌تونه زیاد بشه)"""
    if remaining < 50000:
        return notify(user_id,
            '⚠️ موجودی کم',
            f'موجودی کیف پولت کمتر از ۵۰,۰۰۰ ریال شد — شارژ کن',
            '⚠️', '/panel/wallet/charge')
    return None


# ==================== LOYALTY CHART / نمودار ====================

def get_weekly_points(user_id):
    """امتیاز روزانه ۷ روز اخیر"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    result = {}
    for i in range(6, -1, -1):
        day = (_dt.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        c.execute("""SELECT COALESCE(SUM(points), 0) FROM loyalty_log
                     WHERE user_id=? AND DATE(created_at)=? AND points > 0""",
                  (user_id, day))
        pts = c.fetchone()[0] or 0
        result[day] = pts
    conn.close()
    return result


def get_weekly_labels():
    """برچسب روزها به فارسی"""
    fa_days = ['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']
    labels = []
    for i in range(6, -1, -1):
        d = _dt.now() - timedelta(days=i)
        labels.append(fa_days[d.weekday()])
    return labels


# ==================== LEADERBOARD / رتبه‌بندی ====================

def get_top_users_by_points(limit=10, period='all'):
    """
    period: 'all' | 'week' | 'month'
    """
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()

    if period == 'all':
        c.execute("""
            SELECT u.id, u.username, u.shop_name,
                   COALESCE(l.total_points, 0) AS pts,
                   COALESCE(l.tier, 'bronze')
            FROM users u
            LEFT JOIN loyalty l ON l.user_id = u.id
            WHERE u.id != 1
            ORDER BY pts DESC, u.id ASC
            LIMIT ?
        """, (limit,))
    else:
        # امتیاز هفته/ماه اخیر از loyalty_log
        days = 7 if period == 'week' else 30
        since = (_dt.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""
            SELECT u.id, u.username, u.shop_name,
                   COALESCE(SUM(CASE WHEN ll.points > 0 THEN ll.points ELSE 0 END), 0) AS pts,
                   COALESCE(l.tier, 'bronze')
            FROM users u
            LEFT JOIN loyalty l ON l.user_id = u.id
            LEFT JOIN loyalty_log ll ON ll.user_id = u.id AND ll.created_at >= ?
            WHERE u.id != 1
            GROUP BY u.id
            ORDER BY pts DESC, u.id ASC
            LIMIT ?
        """, (since, limit))

    rows = c.fetchall()
    conn.close()
    return rows


def get_my_rank(user_id, period='all'):
    """رتبه کاربر جاری"""
    all_users = get_top_users_by_points(1000, period)
    for i, r in enumerate(all_users):
        if r[0] == user_id:
            return i + 1, r[3], len(all_users)
    return None, 0, len(all_users)


def get_top_sms_senders(limit=10, days=30):
    """رتبه‌بندی بر اساس تعداد پیامک"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    since = (_dt.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute("""
        SELECT u.id, u.username, u.shop_name, COUNT(s.id) AS cnt
        FROM users u
        LEFT JOIN sent_sms s ON s.user_id = u.id AND s.created_at >= ?
        WHERE u.id != 1
        GROUP BY u.id
        HAVING cnt > 0
        ORDER BY cnt DESC, u.id ASC
        LIMIT ?
    """, (since, limit))
    rows = c.fetchall()
    conn.close()
    return rows


# ==================== REPORTS / گزارش‌ها ====================

def get_user_sms_history(user_id, limit=200, phone_filter='', period='all'):
    """تاریخچه پیامک‌های مغازه‌دار"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    q = "SELECT id, phone, message, status, created_at FROM sent_sms WHERE user_id=?"
    params = [user_id]

    if phone_filter:
        q += " AND phone LIKE ?"
        params.append(f'%{phone_filter}%')

    if period == 'today':
        q += " AND DATE(created_at) = DATE('now')"
    elif period == 'week':
        since = (_dt.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        q += " AND created_at >= ?"
        params.append(since)
    elif period == 'month':
        since = (_dt.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        q += " AND created_at >= ?"
        params.append(since)

    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows


def count_user_sms(user_id, period='all'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    q = "SELECT COUNT(*) FROM sent_sms WHERE user_id=? AND status IN ('success','ok','sent')"
    params = [user_id]
    if period == 'today':
        q += " AND DATE(created_at) = DATE('now')"
    elif period == 'week':
        since = (_dt.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        q += " AND created_at >= ?"
        params.append(since)
    elif period == 'month':
        since = (_dt.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        q += " AND created_at >= ?"
        params.append(since)
    c.execute(q, params)
    n = c.fetchone()[0]
    conn.close()
    return n


def count_user_sms_by_status(user_id, status, period='all'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    q = "SELECT COUNT(*) FROM sent_sms WHERE user_id=? AND status=?"
    params = [user_id, status]
    if period == 'today':
        q += " AND DATE(created_at) = DATE('now')"
    elif period == 'week':
        since = (_dt.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        q += " AND created_at >= ?"
        params.append(since)
    elif period == 'month':
        since = (_dt.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        q += " AND created_at >= ?"
        params.append(since)
    c.execute(q, params)
    n = c.fetchone()[0]
    conn.close()
    return n


def get_user_sms_daily(user_id, days=7):
    """تعداد پیامک روزانه برای نمودار"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    result = {}
    for i in range(days - 1, -1, -1):
        day = (_dt.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        c.execute("SELECT COUNT(*) FROM sent_sms WHERE user_id=? AND DATE(created_at)=?",
                  (user_id, day))
        result[day] = c.fetchone()[0]
    conn.close()
    return result


def get_user_premium_history(user_id, limit=50):
    """تاریخچه خرید پرمیوم (از transactions با type='premium')"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, amount, type, description, balance_after, created_at
        FROM transactions
        WHERE user_id=? AND (type='premium' OR description LIKE '%پرمیوم%')
        ORDER BY id DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_payments_history(user_id, limit=100):
    """تاریخچه پرداخت‌های آنلاین کاربر"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, amount, status, ref_id, created_at, verified_at
        FROM payments WHERE user_id=?
        ORDER BY id DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


# ==================== ADMIN REPORTS / گزارش‌های ادمین ====================

def get_total_revenue():
    """مجموع درآمد از همه پرداخت‌های موفق"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='verified'")
    total = c.fetchone()[0] or 0
    conn.close()
    return total


def get_total_revenue_by_period(period='month'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    q = "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='verified'"
    if period == 'today':
        q += " AND DATE(verified_at) = DATE('now')"
    elif period == 'week':
        since = (_dt.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        q += f" AND verified_at >= '{since}'"
    elif period == 'month':
        since = (_dt.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        q += f" AND verified_at >= '{since}'"
    c.execute(q)
    n = c.fetchone()[0] or 0
    conn.close()
    return n


def get_daily_revenue(days=30):
    """درآمد روزانه برای نمودار"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    result = {}
    for i in range(days - 1, -1, -1):
        day = (_dt.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        c.execute("""SELECT COALESCE(SUM(amount), 0) FROM payments
                     WHERE status='verified' AND DATE(verified_at)=?""", (day,))
        result[day] = c.fetchone()[0] or 0
    conn.close()
    return result


def get_revenue_by_user(limit=50):
    """درآمد به تفکیک کاربر"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name,
               COALESCE(SUM(p.amount), 0) AS total,
               COUNT(p.id) AS cnt
        FROM users u
        LEFT JOIN payments p ON p.user_id = u.id AND p.status='verified'
        WHERE u.id != 1
        GROUP BY u.id
        ORDER BY total DESC, u.id ASC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_daily_sms_all(days=30):
    """پیامک روزانه همه کاربران"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    result = {}
    for i in range(days - 1, -1, -1):
        day = (_dt.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        c.execute("SELECT COUNT(*) FROM sent_sms WHERE DATE(created_at)=?", (day,))
        result[day] = c.fetchone()[0]
    conn.close()
    return result


def get_admin_overview():
    """آمار کلی ادمین"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) FROM users WHERE id != 1")
    stats['total_users'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sent_sms")
    stats['total_sms'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM payments WHERE status='verified'")
    stats['total_payments'] = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(balance), 0) FROM wallets")
    stats['total_wallet_balance'] = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM tickets WHERE status='open'")
    stats['open_tickets'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM referrals")
    stats['total_referrals'] = c.fetchone()[0]
    today = _dt.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM sent_sms WHERE DATE(created_at)=?", (today,))
    stats['today_sms'] = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='verified' AND DATE(verified_at)=?",
              (today,))
    stats['today_revenue'] = c.fetchone()[0] or 0
    conn.close()
    return stats


def get_top_paying_users(limit=10):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name,
               COALESCE(SUM(p.amount), 0) AS total
        FROM users u
        LEFT JOIN payments p ON p.user_id = u.id AND p.status='verified'
        WHERE u.id != 1
        GROUP BY u.id
        HAVING total > 0
        ORDER BY total DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


# ==================== BIRTHDAYS / هشدار تولد ====================

def get_upcoming_birthdays(days=7):
    """کاربرانی که توی N روز آینده تولدشونه"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.shop_name, l.birthday
        FROM users u
        LEFT JOIN loyalty l ON l.user_id = u.id
        WHERE l.birthday != '' AND l.birthday IS NOT NULL AND u.id != 1
    """)
    rows = c.fetchall()
    conn.close()

    today = _dt.now().date()
    result = []
    for uid, uname, shop, bd in rows:
        try:
            # فرمت‌های ممکن: MM-DD یا YYYY-MM-DD
            parts = bd.split('-')
            if len(parts) == 2:
                mm, dd = int(parts[0]), int(parts[1])
            elif len(parts) == 3:
                mm, dd = int(parts[1]), int(parts[2])
            else:
                continue
            # تولد امسال
            this_year = today.replace(month=mm, day=dd)
            if this_year < today:
                next_year = this_year.replace(year=today.year + 1)
            else:
                next_year = this_year
            delta = (next_year - today).days
            if 0 <= delta <= days:
                result.append({
                    'id': uid, 'username': uname, 'shop': shop or '',
                    'birthday': bd, 'days_left': delta,
                    'date': next_year.strftime('%Y-%m-%d'),
                    'is_today': delta == 0
                })
        except Exception:
            continue
    result.sort(key=lambda x: x['days_left'])
    return result


def give_birthday_gift(user_id, cash=100000, points=100):
    """هدیه تولد: شارژ کیف پول + امتیاز وفاداری"""
    try:
        charge_wallet(user_id, cash, '🎂 هدیه تولد')
    except Exception:
        pass
    try:
        add_loyalty_points(user_id, points, '🎂 هدیه تولد')
    except Exception:
        pass
    # نوتیف
    try:
        notify(user_id, '🎂 تولدت مبارک!',
               f'هدیه تولد: {cash:,} ریال + {points} امتیاز',
               '🎂', '/panel/wallet')
    except Exception:
        pass
    return True


def get_birthday_history(limit=50):
    """کاربرانی که هدیه تولد گرفتن"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT user_id, note, points, created_at
        FROM loyalty_log
        WHERE note LIKE '%تولد%'
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


# ==================== 2FA / ورود دو مرحله‌ای ====================
import secrets as _sec, random as _rnd


def get_2fa(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT enabled, phone, code, expires_at, attempts FROM user_2fa WHERE user_id=?",
              (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {'enabled': 0, 'phone': '', 'code': '', 'expires_at': None, 'attempts': 0}
    return {
        'enabled': row[0] or 0,
        'phone': row[1] or '',
        'code': row[2] or '',
        'expires_at': row[3],
        'attempts': row[4] or 0,
    }


def set_2fa_enabled(user_id, enabled, phone=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id FROM user_2fa WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE user_2fa SET enabled=?, phone=? WHERE user_id=?",
                  (1 if enabled else 0, phone, user_id))
    else:
        c.execute("INSERT INTO user_2fa (user_id, enabled, phone) VALUES (?, ?, ?)",
                  (user_id, 1 if enabled else 0, phone))
    conn.commit()
    conn.close()


def generate_2fa_code(user_id):
    """کد ۶ رقمی + اعتبار ۵ دقیقه"""
    code = str(_rnd.randint(100000, 999999))
    expires = (_dt.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""UPDATE user_2fa SET code=?, expires_at=?, attempts=0 WHERE user_id=?""",
              (code, expires, user_id))
    if c.rowcount == 0:
        c.execute("INSERT INTO user_2fa (user_id, code, expires_at, attempts) VALUES (?, ?, ?, 0)",
                  (user_id, code, expires))
    conn.commit()
    conn.close()
    return code


def verify_2fa_code(user_id, code):
    """(موفق/ناموفق, پیام)"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT code, expires_at, attempts FROM user_2fa WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, 'اطلاعات 2FA پیدا نشد'
    stored_code, expires_at, attempts = row
    if not stored_code:
        conn.close()
        return False, 'کدی ارسال نشده'
    if attempts is not None and attempts >= 5:
        conn.close()
        return False, 'تلاش بیش از حد — دوباره کد بگیر'
    # چک انقضا
    try:
        exp = _dt.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
        if _dt.now() > exp:
            conn.close()
            return False, 'کد منقضی شده'
    except Exception:
        conn.close()
        return False, 'خطای اعتبار'
    # چک کد
    if str(code).strip() != str(stored_code):
        c.execute("UPDATE user_2fa SET attempts = COALESCE(attempts,0) + 1 WHERE user_id=?",
                  (user_id,))
        conn.commit()
        conn.close()
        return False, 'کد اشتباه است'
    # موفق → پاک کردن کد
    c.execute("UPDATE user_2fa SET code='', attempts=0, expires_at=NULL WHERE user_id=?",
              (user_id,))
    conn.commit()
    conn.close()
    return True, 'OK'


# ==================== AUTO-REPLY / پاسخ خودکار ====================

def add_auto_reply(user_id, keyword, response, match_type='contains'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT INTO auto_replies (user_id, keyword, response, match_type)
                 VALUES (?, ?, ?, ?)""", (user_id, keyword, response, match_type))
    rid = c.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_user_auto_replies(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, keyword, response, match_type, active, hits, created_at
                 FROM auto_replies WHERE user_id=? ORDER BY id DESC""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_auto_reply(reply_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, user_id, keyword, response, match_type, active, hits
                 FROM auto_replies WHERE id=?""", (reply_id,))
    row = c.fetchone()
    conn.close()
    return row


def update_auto_reply(reply_id, keyword, response, match_type):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""UPDATE auto_replies SET keyword=?, response=?, match_type=?
                 WHERE id=?""", (keyword, response, match_type, reply_id))
    conn.commit()
    conn.close()


def delete_auto_reply(reply_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM auto_replies WHERE id=?", (reply_id,))
    conn.commit()
    conn.close()


def toggle_auto_reply(reply_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE auto_replies SET active = CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?",
              (reply_id,))
    conn.commit()
    conn.close()


def find_matching_rule(user_id, message):
    """پیدا کردن قاعده‌ای که با پیام ورودی مچ می‌شه"""
    if not message:
        return None
    msg_lower = message.strip().lower()
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, keyword, response, match_type FROM auto_replies
                 WHERE user_id=? AND active=1 ORDER BY id ASC""", (user_id,))
    rules = c.fetchall()
    conn.close()

    for rid, keyword, response, mtype in rules:
        kw = (keyword or '').strip().lower()
        if not kw:
            continue
        if mtype == 'exact' and msg_lower == kw:
            return (rid, response)
        elif mtype == 'starts' and msg_lower.startswith(kw):
            return (rid, response)
        elif mtype == 'contains' and kw in msg_lower:
            return (rid, response)
    return None


def increment_auto_reply_hit(reply_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE auto_replies SET hits = COALESCE(hits,0) + 1 WHERE id=?", (reply_id,))
    conn.commit()
    conn.close()


def log_incoming_sms(user_id, from_phone, message, matched_rule=None, auto_reply_sent=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT INTO incoming_sms (user_id, from_phone, message, matched_rule, auto_reply_sent)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, from_phone, message, matched_rule, auto_reply_sent))
    conn.commit()
    conn.close()


def get_user_incoming_sms(user_id, limit=100):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, from_phone, message, matched_rule, auto_reply_sent, created_at
                 FROM incoming_sms WHERE user_id=? ORDER BY id DESC LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def count_auto_replies(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM auto_replies WHERE user_id=? AND active=1", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


def count_incoming_today(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) FROM incoming_sms
                 WHERE user_id=? AND DATE(created_at)=DATE('now')""", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


# ==================== AI MANAGER ====================
import json as _json

def get_ai_plans():
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("SELECT code, name, price, duration_days, features, trial_available FROM ai_plans WHERE active=1 ORDER BY price")
    rows = c.fetchall(); conn.close()
    return rows

def get_ai_plan(code):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("SELECT code, name, price, duration_days, features, trial_available FROM ai_plans WHERE code=?", (code,))
    row = c.fetchone(); conn.close()
    return row

def get_messengers(active_only=True):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    if active_only:
        c.execute("SELECT code, name, icon, requires_phone, requires_admin, docs_url FROM ai_messengers WHERE active=1 ORDER BY rowid")
    else:
        c.execute("SELECT code, name, icon, requires_phone, requires_admin, docs_url FROM ai_messengers ORDER BY rowid")
    rows = c.fetchall(); conn.close()
    return rows

def get_messenger_name(code):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("SELECT name, icon FROM ai_messengers WHERE code=?", (code,))
    row = c.fetchone(); conn.close()
    return row if row else (code, '❓')

def get_active_subscription(user_id):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("""SELECT id, plan_code, is_trial, messenger, start_at, end_at
                 FROM ai_subscriptions WHERE user_id=? AND active=1 AND end_at > CURRENT_TIMESTAMP
                 ORDER BY id DESC LIMIT 1""", (user_id,))
    row = c.fetchone(); conn.close()
    if not row: return None
    return {'id': row[0], 'plan_code': row[1], 'is_trial': bool(row[2]),
            'messenger': row[3] or 'rubika', 'start_at': row[4], 'end_at': row[5]}

def has_used_trial(user_id):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ai_subscriptions WHERE user_id=? AND is_trial=1", (user_id,))
    n = c.fetchone()[0]; conn.close()
    return n > 0

def create_ai_subscription(user_id, plan_code, is_trial=0, messenger='rubika'):
    plan = get_ai_plan(plan_code)
    if not plan: return None
    days = 7 if is_trial else plan[3]
    end = (_dt.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("""INSERT INTO ai_subscriptions (user_id, plan_code, is_trial, messenger, end_at)
                 VALUES (?, ?, ?, ?, ?)""", (user_id, plan_code, 1 if is_trial else 0, messenger, end))
    sid = c.lastrowid; conn.commit(); conn.close()
    return sid

def cancel_ai_subscription(sub_id):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("UPDATE ai_subscriptions SET active=0 WHERE id=?", (sub_id,))
    conn.commit(); conn.close()

def get_ai_config(user_id):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("""SELECT id, plan_code, rubika_channel_id, rubika_admin_username,
                 target_channel, source_channels, content_keywords,
                 recruit_target_count, recruit_message, active, verified, messenger
                 FROM ai_channel_config WHERE user_id=? ORDER BY id DESC LIMIT 1""", (user_id,))
    row = c.fetchone(); conn.close()
    if not row: return None
    return {'id': row[0], 'plan_code': row[1], 'channel_id': row[2] or '',
            'admin_username': row[3] or '', 'target_channel': row[4] or '',
            'source_channels': row[5] or '', 'content_keywords': row[6] or '',
            'recruit_target': row[7] or 100, 'recruit_message': row[8] or '',
            'active': bool(row[9]), 'verified': bool(row[10]),
            'messenger': row[11] or 'rubika'}

def save_ai_config(user_id, data):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("SELECT id FROM ai_channel_config WHERE user_id=?", (user_id,))
    row = c.fetchone()
    vals = (data.get('plan_code',''), data.get('messenger','rubika'),
            data.get('channel_id',''), data.get('admin_username',''),
            data.get('target_channel',''), data.get('source_channels',''),
            data.get('content_keywords',''), data.get('recruit_target', 100),
            data.get('recruit_message',''))
    if row:
        c.execute("""UPDATE ai_channel_config SET
                     plan_code=?, messenger=?, rubika_channel_id=?, rubika_admin_username=?,
                     target_channel=?, source_channels=?, content_keywords=?,
                     recruit_target_count=?, recruit_message=?,
                     updated_at=CURRENT_TIMESTAMP WHERE user_id=?""", vals + (user_id,))
    else:
        c.execute("""INSERT INTO ai_channel_config
                     (user_id, plan_code, messenger, rubika_channel_id, rubika_admin_username,
                      target_channel, source_channels, content_keywords,
                      recruit_target_count, recruit_message)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (user_id,) + vals)
    conn.commit(); conn.close()

def toggle_ai_config(user_id, active):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("UPDATE ai_channel_config SET active=? WHERE user_id=?", (1 if active else 0, user_id))
    conn.commit(); conn.close()

def add_ai_task(user_id, task_type, messenger='', payload=None):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    p = _json.dumps(payload) if payload else '{}'
    c.execute("""INSERT INTO ai_task_queue (user_id, task_type, messenger, payload)
                 VALUES (?, ?, ?, ?)""", (user_id, task_type, messenger, p))
    tid = c.lastrowid; conn.commit(); conn.close()
    return tid

def get_user_ai_tasks(user_id, limit=50):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("""SELECT id, task_type, status, result, scheduled_at, executed_at, created_at, messenger
                 FROM ai_task_queue WHERE user_id=? ORDER BY id DESC LIMIT ?""", (user_id, limit))
    rows = c.fetchall(); conn.close()
    return rows

def count_pending_tasks(user_id=None):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    if user_id:
        c.execute("SELECT COUNT(*) FROM ai_task_queue WHERE user_id=? AND status='pending'", (user_id,))
    else:
        c.execute("SELECT COUNT(*) FROM ai_task_queue WHERE status='pending'")
    n = c.fetchone()[0]; conn.close()
    return n

def get_all_ai_subscriptions(limit=200):
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    c.execute("""SELECT s.id, s.user_id, u.username, u.shop_name, s.plan_code,
                 s.is_trial, s.messenger, s.start_at, s.end_at, s.active
                 FROM ai_subscriptions s LEFT JOIN users u ON u.id = s.user_id
                 ORDER BY s.id DESC LIMIT ?""", (limit,))
    rows = c.fetchall(); conn.close()
    return rows

def get_ai_stats():
    conn = sqlite3.connect('panel.db'); c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) FROM ai_subscriptions WHERE active=1 AND end_at > CURRENT_TIMESTAMP")
    stats['active_subs'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ai_subscriptions WHERE is_trial=1")
    stats['trials'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ai_subscriptions")
    stats['total_subs'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ai_task_queue WHERE status='pending'")
    stats['pending_tasks'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ai_task_queue WHERE status='done'")
    stats['done_tasks'] = c.fetchone()[0]
    conn.close()
    return stats


# ==================== BOT TOKEN / ربات ====================

def save_bot_token(user_id, token, messenger='rubika'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id FROM ai_channel_config WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE ai_channel_config SET bot_token=?, messenger=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
                  (token, messenger, user_id))
    else:
        c.execute("INSERT INTO ai_channel_config (user_id, bot_token, messenger) VALUES (?, ?, ?)",
                  (user_id, token, messenger))
    conn.commit()
    conn.close()


def get_bot_token(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT bot_token, messenger, rubika_channel_id FROM ai_channel_config WHERE user_id=?",
              (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {'token': row[0] or '', 'messenger': row[1] or 'rubika', 'channel': row[2] or ''}


def get_pending_tasks(limit=10):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, user_id, task_type, messenger, payload, scheduled_at
                 FROM ai_task_queue WHERE status='pending'
                 AND scheduled_at <= CURRENT_TIMESTAMP
                 ORDER BY id ASC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def update_task_status(task_id, status, result=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""UPDATE ai_task_queue SET status=?, result=?, executed_at=CURRENT_TIMESTAMP
                 WHERE id=?""", (status, result, task_id))
    conn.commit()
    conn.close()


def log_bot_action(user_id, task_id, action, detail=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT INTO ai_task_log (user_id, task_id, action, detail)
                 VALUES (?, ?, ?, ?)""", (user_id, task_id, action, detail))
    conn.commit()
    conn.close()


# ==================== BOT MEMBERS / FORCE-JOIN / BROADCAST ====================

def add_bot_member(user_id, messenger, chat_id, username='', first_name='', last_name='', phone=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO bot_members
                 (user_id, messenger, chat_id, username, first_name, last_name, phone)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (user_id, messenger, str(chat_id), username, first_name, last_name, phone))
    conn.commit()
    conn.close()


def get_bot_members(user_id, messenger=None, limit=1000):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    if messenger:
        c.execute("""SELECT chat_id, username, first_name, phone FROM bot_members
                     WHERE user_id=? AND messenger=? AND is_blocked=0 LIMIT ?""",
                  (user_id, messenger, limit))
    else:
        c.execute("""SELECT chat_id, username, first_name, phone FROM bot_members
                     WHERE user_id=? AND is_blocked=0 LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def count_bot_members(user_id, messenger=None):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    if messenger:
        c.execute("SELECT COUNT(*) FROM bot_members WHERE user_id=? AND messenger=?", (user_id, messenger))
    else:
        c.execute("SELECT COUNT(*) FROM bot_members WHERE user_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


def add_force_join(user_id, messenger, channel_id, channel_username='', channel_link=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT INTO force_join_channels
                 (user_id, messenger, channel_id, channel_username, channel_link)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, messenger, channel_id, channel_username, channel_link))
    fid = c.lastrowid
    conn.commit()
    conn.close()
    return fid


def get_force_joins(user_id, messenger=None):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    if messenger:
        c.execute("""SELECT id, channel_id, channel_username, channel_link, active
                     FROM force_join_channels WHERE user_id=? AND messenger=? ORDER BY id DESC""",
                  (user_id, messenger))
    else:
        c.execute("""SELECT id, channel_id, channel_username, channel_link, active
                     FROM force_join_channels WHERE user_id=? ORDER BY id DESC""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def toggle_force_join(fid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE force_join_channels SET active = CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (fid,))
    conn.commit()
    conn.close()


def delete_force_join(fid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM force_join_channels WHERE id=?", (fid,))
    conn.commit()
    conn.close()


def log_broadcast(user_id, message, sent, failed, target_type='bot_members'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT INTO broadcast_log
                 (user_id, message, total_sent, total_failed, target_type)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, message, sent, failed, target_type))
    bid = c.lastrowid
    conn.commit()
    conn.close()
    return bid


def get_broadcast_history(user_id, limit=20):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, message, total_sent, total_failed, target_type, created_at
                 FROM broadcast_log WHERE user_id=? ORDER BY id DESC LIMIT ?""",
              (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def add_contact_with_source(user_id, name, phone, group_name='', source='bot'):
    """اضافه کردن مخاطب از ربات"""
    try:
        from database import add_contact
        return add_contact(user_id, name, phone, group_name)
    except Exception:
        return None


# ==================== BOT ADS ====================

def add_bot_ad(admin_id, message):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO bot_ads (admin_id, message) VALUES (?, ?)", (admin_id, message))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid


def get_pending_ads():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, admin_id, message FROM bot_ads
                 WHERE status='pending' ORDER BY id ASC LIMIT 5""")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_bot_members(admin_id):
    """ممبران ربات برای یک ادمین مشخص"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT chat_id, username, first_name FROM bot_members
                 WHERE user_id=? AND is_blocked=0""", (admin_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def update_ad_status(ad_id, status, sent=0, failed=0):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""UPDATE bot_ads SET status=?, sent_count=?, failed_count=?,
                 executed_at=CURRENT_TIMESTAMP WHERE id=?""",
              (status, sent, failed, ad_id))
    conn.commit()
    conn.close()


def get_ads_history(admin_id=None, limit=50):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    if admin_id:
        c.execute("""SELECT id, message, sent_count, failed_count, status, created_at
                     FROM bot_ads WHERE admin_id=? ORDER BY id DESC LIMIT ?""",
                  (admin_id, limit))
    else:
        c.execute("""SELECT id, message, sent_count, failed_count, status, created_at
                     FROM bot_ads ORDER BY id DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def count_bot_members_for_user(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bot_members WHERE user_id=? AND is_blocked=0", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


# ==================== POSTER TEMPLATES ====================

def add_poster_template(user_id, code, name, prompt, category='general'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO poster_templates (user_id, code, name, prompt, category)
                     VALUES (?, ?, ?, ?, ?)""",
                  (user_id, code, name, prompt, category))
        tid = c.lastrowid
        conn.commit()
        conn.close()
        return tid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_poster_template(user_id, code):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, code, name, prompt, category FROM poster_templates
                 WHERE user_id=? AND code=? AND active=1""",
              (user_id, code))
    row = c.fetchone()
    conn.close()
    return row


def get_poster_templates(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, code, name, prompt, category, active, uses
                 FROM poster_templates WHERE user_id=? ORDER BY id DESC""",
              (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def delete_poster_template(tid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM poster_templates WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def toggle_poster_template(tid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE poster_templates SET active = CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def increment_template_use(tid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE poster_templates SET uses = COALESCE(uses,0) + 1 WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def get_admin_bot(messenger):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT token, username, active FROM admin_bots WHERE messenger=?", (messenger,))
    row = c.fetchone(); conn.close()
    return row

def save_admin_bot(messenger, token, username=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO admin_bots (messenger, token, username, active) VALUES (?, ?, ?, 1)", (messenger, token, username))
    conn.commit(); conn.close()

def get_all_admin_bots():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT messenger, token, username, active FROM admin_bots")
    rows = c.fetchall(); conn.close()
    return rows

def delete_admin_bot(messenger):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM admin_bots WHERE messenger=?", (messenger,))
    conn.commit(); conn.close()

def get_bot_stats():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    s = {}
    c.execute("SELECT COUNT(*) FROM bot_members"); s['members'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bot_ads WHERE status='done'"); s['ads_done'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bot_ads WHERE status='pending'"); s['ads_pending'] = c.fetchone()[0]
    conn.close(); return s


def get_admin_bot(messenger='rubika'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT token, username FROM admin_bots WHERE messenger=? AND active=1", (messenger,))
    row = c.fetchone()
    conn.close()
    return row

def save_admin_bot(messenger, token, username=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO admin_bots (messenger, token, username, active) VALUES (?, ?, ?, 1)", (messenger, token, username))
    conn.commit()
    conn.close()

def get_all_admin_bots():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT messenger, token, username FROM admin_bots WHERE active=1")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_admin_bot(messenger):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM admin_bots WHERE messenger=?", (messenger,))
    conn.commit()
    conn.close()

def add_bot_member(messenger, chat_id, first_name=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bot_members (messenger, chat_id, first_name) VALUES (?, ?, ?)", (messenger, str(chat_id), first_name))
    conn.commit()
    conn.close()

def add_ad(message):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO bot_ads (message) VALUES (?)", (message,))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid

def get_pending_ads():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, message FROM bot_ads WHERE status='pending' ORDER BY id LIMIT 5")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_ad_done(aid, sent, failed):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE bot_ads SET status='done', sent_count=?, failed_count=?, executed_at=CURRENT_TIMESTAMP WHERE id=?", (sent, failed, aid))
    conn.commit()
    conn.close()

def get_bot_stats():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    s = {}
    c.execute("SELECT COUNT(*) FROM bot_members"); s['members'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bot_ads WHERE status='done'"); s['ads_done'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bot_ads WHERE status='pending'"); s['ads_pending'] = c.fetchone()[0]
    conn.close()
    return s


# ==================== ALIASES & MISSING FUNCS ====================

def add_bot_ad(admin_id, message):
    return add_ad(message)

def get_user_bot_members(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT chat_id, first_name FROM bot_members")
    rows = c.fetchall()
    conn.close()
    return rows

def count_bot_members_for_user(user_id):
    return count_bot_members()

def get_bot_token(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT token, messenger, '' FROM admin_bots WHERE active=1 LIMIT 1")
    row = c.fetchone()
    conn.close()
    if not row: return None
    return {'token': row[0] or '', 'messenger': row[1] or 'rubika', 'channel': ''}

def add_force_join(user_id, messenger, channel_id, username='', link=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS force_join_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, messenger TEXT, channel_id TEXT,
            channel_username TEXT, channel_link TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    except: pass
    c.execute("""INSERT INTO force_join_channels
                 (user_id, messenger, channel_id, channel_username, channel_link)
                 VALUES (?, ?, ?, ?, ?)""", (user_id, messenger, channel_id, username, link))
    fid = c.lastrowid
    conn.commit()
    conn.close()
    return fid

def get_force_joins(user_id, messenger=None):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        if messenger:
            c.execute("""SELECT id, channel_id, channel_username, channel_link, active
                         FROM force_join_channels WHERE user_id=? AND messenger=?
                         ORDER BY id DESC""", (user_id, messenger))
        else:
            c.execute("""SELECT id, channel_id, channel_username, channel_link, active
                         FROM force_join_channels WHERE user_id=? ORDER BY id DESC""", (user_id,))
        rows = c.fetchall()
    except:
        rows = []
    conn.close()
    return rows

def toggle_force_join(fid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE force_join_channels SET active = CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (fid,))
        conn.commit()
    except: pass
    conn.close()

def delete_force_join(fid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("DELETE FROM force_join_channels WHERE id=?", (fid,))
        conn.commit()
    except: pass
    conn.close()

def log_broadcast(user_id, message, sent, failed, target_type='members'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS broadcast_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, message TEXT,
            total_sent INTEGER DEFAULT 0, total_failed INTEGER DEFAULT 0,
            target_type TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    except: pass
    c.execute("""INSERT INTO broadcast_log (user_id, message, total_sent, total_failed, target_type)
                 VALUES (?, ?, ?, ?, ?)""", (user_id, message, sent, failed, target_type))
    conn.commit()
    conn.close()

def get_broadcast_history(user_id, limit=20):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("""SELECT id, message, total_sent, total_failed, target_type, created_at
                     FROM broadcast_log WHERE user_id=? ORDER BY id DESC LIMIT ?""", (user_id, limit))
        rows = c.fetchall()
    except:
        rows = []
    conn.close()
    return rows


# ==================== ALIASES ====================

def get_contacts(user_id):
    """alias برای توابع مخاطبین"""
    try:
        conn = sqlite3.connect('panel.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, phone, COALESCE(group_name, ''), COALESCE(group_name, '')
                     FROM contacts WHERE user_id=? ORDER BY id DESC""", (user_id,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        # اگه ستون group_name نبود، بدون اون
        try:
            conn = sqlite3.connect('panel.db')
            c = conn.cursor()
            c.execute("SELECT id, name, phone FROM contacts WHERE user_id=? ORDER BY id DESC", (user_id,))
            rows = c.fetchall()
            conn.close()
            return rows
        except:
            return []

def count_contacts(user_id):
    try:
        conn = sqlite3.connect('panel.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM contacts WHERE user_id=?", (user_id,))
        n = c.fetchone()[0]
        conn.close()
        return n
    except:
        return 0

def add_contact(user_id, name, phone, group_name='', note=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO contacts (user_id, name, phone, group_name, note)
                     VALUES (?, ?, ?, ?, ?)""", (user_id, name, phone, group_name, note))
    except:
        try:
            c.execute("INSERT INTO contacts (user_id, name, phone) VALUES (?, ?, ?)",
                      (user_id, name, phone))
        except Exception as e:
            conn.close()
            return None
    cid = c.lastrowid
    conn.commit()
    conn.close()
    return cid


# ==================== FIXED SIGNATURES ====================

def count_bot_members(user_id_or_messenger=None, messenger=None):
    """پشتیبانی از هر دو حالت"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        if messenger:
            c.execute("SELECT COUNT(*) FROM bot_members WHERE messenger=?", (messenger,))
        elif isinstance(user_id_or_messenger, str) and user_id_or_messenger in ('rubika','eitaa','bale','soroush','telegram'):
            c.execute("SELECT COUNT(*) FROM bot_members WHERE messenger=?", (user_id_or_messenger,))
        elif user_id_or_messenger:
            c.execute("SELECT COUNT(*) FROM bot_members")
        else:
            c.execute("SELECT COUNT(*) FROM bot_members")
        n = c.fetchone()[0]
    except:
        n = 0
    conn.close()
    return n

def get_ads_history(*args, **kwargs):
    """پشتیبانی از هر تعداد آرگومان"""
    limit = 30
    for a in args:
        if isinstance(a, int):
            limit = a
    if 'limit' in kwargs:
        limit = kwargs['limit']
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id, message, sent_count, failed_count, status, created_at FROM bot_ads ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
    except:
        rows = []
    conn.close()
    return rows


# ==================== CUSTOMERS / مشتری‌ها ====================

def add_customer(phone, name, password=''):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO customers (phone, name, password) VALUES (?, ?, ?)",
                  (phone, name, password))
        cid = c.lastrowid
        conn.commit()
        conn.close()
        return cid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_customer_by_phone(phone):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, phone, name, password, avatar, created_at FROM customers WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    return row


def get_customer(cid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id, phone, name, password, avatar, created_at FROM customers WHERE id=?", (cid,))
    row = c.fetchone()
    conn.close()
    return row


def update_customer_lastlogin(cid):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE customers SET last_login=CURRENT_TIMESTAMP WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def search_shop(query):
    """جستجوی مغازه‌دار"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    q = '%' + query + '%'
    c.execute("""SELECT id, username, shop_name, phone FROM users
                 WHERE id != 1 AND status='active'
                 AND (shop_name LIKE ? OR username LIKE ?)
                 ORDER BY shop_name LIMIT 30""", (q, q))
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_shops():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, username, shop_name, phone FROM users
                 WHERE id != 1 AND status='active'
                 ORDER BY shop_name LIMIT 100""")
    rows = c.fetchall()
    conn.close()
    return rows


def add_customer_order(customer_id, user_id, subject, message, phone):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""INSERT INTO customer_orders
                 (customer_id, user_id, subject, message, phone)
                 VALUES (?, ?, ?, ?, ?)""",
              (customer_id, user_id, subject, message, phone))
    oid = c.lastrowid
    conn.commit()
    conn.close()
    return oid


def get_customer_orders(customer_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT o.id, o.user_id, u.shop_name, o.subject, o.message,
                 o.status, o.reply, o.created_at
                 FROM customer_orders o
                 LEFT JOIN users u ON u.id = o.user_id
                 WHERE o.customer_id=? ORDER BY o.id DESC LIMIT 50""", (customer_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_shop_orders(user_id):
    """سفارش‌هایی که مشتری‌ها برای این مغازه فرستادن"""
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT o.id, c.name, c.phone, o.subject, o.message,
                 o.status, o.created_at
                 FROM customer_orders o
                 LEFT JOIN customers c ON c.id = o.customer_id
                 WHERE o.user_id=? ORDER BY o.id DESC LIMIT 100""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def reply_customer_order(order_id, reply):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE customer_orders SET reply=?, status='replied', replied_at=CURRENT_TIMESTAMP WHERE id=?",
              (reply, order_id))
    conn.commit()
    conn.close()


def add_favorite(customer_id, user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO customer_favorites (customer_id, user_id) VALUES (?, ?)",
                  (customer_id, user_id))
        conn.commit()
    except: pass
    conn.close()


def remove_favorite(customer_id, user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM customer_favorites WHERE customer_id=? AND user_id=?",
              (customer_id, user_id))
    conn.commit()
    conn.close()


def get_favorites(customer_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.shop_name, u.phone
                 FROM customer_favorites f
                 LEFT JOIN users u ON u.id = f.user_id
                 WHERE f.customer_id=?""", (customer_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def count_shop_orders(user_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customer_orders WHERE user_id=? AND status='pending'", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


def set_member_role(messenger, chat_id, role):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("UPDATE bot_members SET role=? WHERE messenger=? AND chat_id=?",
              (role, messenger, str(chat_id)))
    conn.commit()
    conn.close()


def get_member_role(messenger, chat_id):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT role FROM bot_members WHERE messenger=? AND chat_id=?",
              (messenger, str(chat_id)))
    row = c.fetchone()
    conn.close()
    return (row[0] or '') if row else ''


def get_all_shops_public():
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT id, username, shop_name, phone FROM users
                 WHERE id != 1 AND status='active' AND shop_name != ''
                 ORDER BY shop_name LIMIT 100""")
    rows = c.fetchall()
    conn.close()
    return rows
