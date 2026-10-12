import time, sqlite3, threading, os, re
from bot_adapters.rubika import RubikaBot
from ai_service import ask_ai
from admin_commands import parse_add_command, parse_remove_command, parse_set_command

OFFSET_DIR = os.path.expanduser("~/otp_panel/offsets")
os.makedirs(OFFSET_DIR, exist_ok=True)


def db(): return sqlite3.connect("panel.db", timeout=15)


# ============ UTILS ============
def load_offset(m):
    try:
        with open(os.path.join(OFFSET_DIR, m + ".txt")) as f:
            return f.read().strip() or None
    except: return None


def save_offset(m, off):
    try:
        with open(os.path.join(OFFSET_DIR, m + ".txt"), "w") as f:
            f.write(str(off) if off else "")
    except: pass


def get_bots():
    conn = db(); c = conn.cursor()
    c.execute("SELECT messenger, token FROM admin_bots WHERE active=1 AND token != ''")
    rows = c.fetchall(); conn.close()
    return rows


def save_member(m, chat_id, first_name=''):
    conn = db(); c = conn.cursor()
    c.execute("SELECT id FROM bot_members WHERE messenger=? AND chat_id=?", (m, str(chat_id)))
    row = c.fetchone()
    if row:
        c.execute("UPDATE bot_members SET last_seen=CURRENT_TIMESTAMP WHERE id=?", (row[0],))
    else:
        try:
            c.execute("INSERT INTO bot_members (messenger, chat_id, first_name) VALUES (?, ?, ?)",
                      (m, str(chat_id), first_name))
            conn.commit()
            print("[" + m + "] NEW: " + (first_name or str(chat_id)), flush=True)
        except: pass
    conn.commit(); conn.close()


def inc_msg(m, chat_id):
    conn = db(); c = conn.cursor()
    c.execute("UPDATE bot_members SET total_messages = total_messages + 1 WHERE messenger=? AND chat_id=?",
              (m, str(chat_id)))
    conn.commit(); conn.close()


# ============ SHOP INFO ============
def get_shop():
    conn = db(); c = conn.cursor()
    c.execute("""SELECT id, shop_name, shop_type, address, phone, hours, instagram, description
                 FROM shop_info LIMIT 1""")
    row = c.fetchone(); conn.close()
    return row


def get_products():
    conn = db(); c = conn.cursor()
    c.execute("SELECT id, name, aliases, price, unit, description, category FROM shop_products WHERE available=1")
    rows = c.fetchall(); conn.close()
    return rows


def find_product(query):
    """جستجوی محصول"""
    q = query.strip().lower()
    if not q: return None
    conn = db(); c = conn.cursor()
    c.execute("SELECT id, name, aliases, price, unit, description, category FROM shop_products WHERE available=1")
    rows = c.fetchall(); conn.close()

    # اول: مچ دقیق
    for p in rows:
        if p[1].strip().lower() == q:
            return p
    # دوم: توی aliases
    for p in rows:
        aliases = [a.strip().lower() for a in (p[2] or '').split(',')]
        if q in aliases:
            return p
    # سوم: توی name (search جزئی)
    for p in rows:
        if q in p[1].lower() or p[1].lower() in q:
            return p
    # چهارم: توی aliases (search جزئی)
    for p in rows:
        for a in (p[2] or '').split(','):
            if q in a.strip().lower() or a.strip().lower() in q:
                return p
    return None


# ============ AI PROMPT ============
def build_system_prompt():
    """ساخت system prompt با اطلاعات مغازه"""
    shop = get_shop()
    products = get_products()

    prompt = "تو یه دستیار هوشمند و مودب فارسی‌زبان هستی که به مشتری‌ها جواب می‌دی. همیشه فارسی جواب بده.\n\n"

    if shop:
        prompt += "🏪 اطلاعات مغازه:\n"
        if shop[1]: prompt += "- نام مغازه: " + shop[1] + "\n"
        if shop[2]: prompt += "- نوع کسب‌وکار: " + shop[2] + "\n"
        if shop[3]: prompt += "- آدرس: " + shop[3] + "\n"
        if shop[4]: prompt += "- شماره تماس: " + shop[4] + "\n"
        if shop[5]: prompt += "- ساعات کاری: " + shop[5] + "\n"
        if shop[6]: prompt += "- اینستاگرام: " + shop[6] + "\n"
        if shop[7]: prompt += "- توضیحات: " + shop[7] + "\n"
        prompt += "\n"

    if products:
        prompt += "📦 لیست محصولات و قیمت‌ها:\n"
        for p in products[:50]:
            line = "- " + p[1]
            if p[2]: line += " (" + p[2] + ")"
            line += ": " + str(p[3]) + " تومان"
            if p[4]: line += " / " + p[4]
            if p[5]: line += " — " + p[5]
            prompt += line + "\n"
        prompt += "\n"

    prompt += ("قوانین:\n"
              "1. اگه کسی ازت قیمت محصولی رو پرسید، دقیقاً قیمت رو بگو\n"
              "2. اگه آدرس خواست، آدرس رو بگو\n"
              "3. اگه محصولی توی لیست نبود، بگو در دسترس نیست\n"
              "4. مودب و صمیمی باش\n"
              "5. جواب‌ها کوتاه و مفید باشه\n")

    return prompt


def handle_message(text, name=''):
    """پاسخ به پیام کاربر"""
    t = text.strip()
    if not t:
        return None

    # اول: جستجوی مستقیم محصول
    # اگه پیام حاوی "چند" یا "قیمت" باشه
    if any(k in t for k in ["قیمت", "چند", "چنده", "هزار", "تومان", "قیمتش"]):
        # کلمات کلیدی رو حذف کن
        cleaned = t
        for word in ["قیمت", "چنده", "چند", "هست", "چیه", "؟", "?", "تومان", "هزار", "قیمتش",
                     "بگو", "میشه", "داری", "دارید", "هست؟", "است"]:
            cleaned = cleaned.replace(word, " ")
        cleaned = cleaned.strip()

        # جستجو
        if cleaned:
            for word in cleaned.split():
                if len(word) >= 2:
                    product = find_product(word)
                    if product:
                        shop = get_shop()
                        msg = "🔸 " + product[1] + "\n"
                        msg += "💰 قیمت: " + str(product[3]) + " تومان"
                        if product[4]:
                            msg += " / هر " + product[4]
                        msg += "\n"
                        if product[5]:
                            msg += "📝 " + product[5] + "\n"
                        if shop and shop[1]:
                            msg += "\n🏪 " + shop[1]
                        return msg

    # دوم: آدرس
    if any(k in t for k in ["آدرس", "ادرس", "کجاست", "کجایید", "کجا هستید"]):
        shop = get_shop()
        if shop and shop[3]:
            return "📍 آدرس ما:\n\n" + shop[3] + ("\n\n🏪 " + shop[1] if shop[1] else "")
        return "📍 متأسفانه آدرس ثبت نشده"

    # سوم: شماره تماس
    if any(k in t for k in ["شماره", "تلفن", "تماس"]):
        shop = get_shop()
        if shop and shop[4]:
            return "📞 شماره تماس:\n\n" + shop[4]
        return "📞 شماره تماس ثبت نشده"

    # چهارم: ساعات کاری
    if any(k in t for k in ["ساعت", "ساعات", "کِی باز", "کی باز"]):
        shop = get_shop()
        if shop and shop[5]:
            return "🕐 ساعات کاری:\n\n" + shop[5]
        return "🕐 ساعات کاری ثبت نشده"

    # پنجم: AI
    system = build_system_prompt()
    return ask_ai(t, system)


# ============ HANDLER ============
def is_admin(m, cid):
    """چک کن ادمین هست یا نه - از تنظیمات"""
    conn = db(); c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key='admin_chat_id'")
    row = c.fetchone(); conn.close()
    if row and row[0] == str(cid):
        return True
    return False


def set_admin(m, cid):
    """تنظیم ادمین"""
    conn = db(); c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('admin_chat_id', ?)", (str(cid),))
        conn.commit()
    except: pass
    conn.close()


def add_product(name, price, aliases="", unit="کیلو", desc="", category=""):
    conn = db(); c = conn.cursor()
    try:
        c.execute("""INSERT INTO shop_products 
                     (shop_id, name, aliases, price, unit, description, category)
                     VALUES (1, ?, ?, ?, ?, ?, ?)""",
                  (name, aliases, int(price), unit, desc, category))
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return pid
    except Exception as e:
        conn.close()
        return None


def remove_product(name):
    conn = db(); c = conn.cursor()
    c.execute("DELETE FROM shop_products WHERE name LIKE ? OR aliases LIKE ?",
              ('%' + name + '%', '%' + name + '%'))
    affected = c.rowcount
    conn.commit(); conn.close()
    return affected


def update_shop_info(field, value):
    allowed = ['shop_name', 'shop_type', 'address', 'phone', 'hours', 'instagram', 'description']
    if field not in allowed:
        return False
    conn = db(); c = conn.cursor()
    c.execute(f"UPDATE shop_info SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=1", (value,))
    conn.commit(); conn.close()
    return True


def handle(bot, m, cid, text, name):
    t = (text or "").strip()
    if not t: return
    print("[" + m + "] << '" + t[:60] + "'", flush=True)

    # /start
    if t in ("/start", "شروع", "start"):
        shop = get_shop()
        welcome = "سلام" + (" " + name if name else "") + " عزیز! 🌹\n\n"
        if shop and shop[1]:
            welcome += "🏪 خوش اومدی به " + shop[1] + "\n\n"
        welcome += "💬 هر سوالی داری بپرس\n"
        welcome += "مثلاً:\n"
        welcome += "• قیمت [محصول] چنده؟\n"
        welcome += "• آدرس کجاست؟\n"
        welcome += "• ساعت کاری چیه؟"
        bot.send_message(cid, welcome)
        return

    # /help
    if t in ("/help", "راهنما", "/راهنما"):
        bot.send_message(cid,
            "📚 راهنما\n\n"
            "💬 کافیه سوالت رو بنویسی:\n\n"
            "🔸 قیمت [محصول]\n"
            "🔸 آدرس کجاست؟\n"
            "🔸 ساعت کاری چیه؟\n"
            "🔸 شماره تماس؟\n\n"
            "🤖 یا هر سوال دیگه‌ای بپرس")
        return

    # /products - لیست محصولات
    if t in ("/products", "/محصولات", "محصولات", "لیست قیمت", "/لیست"):
        products = get_products()
        if not products:
            bot.send_message(cid, "📭 لیست محصولات خالیه")
            return
        msg = "📦 لیست محصولات:\n\n"
        for p in products[:30]:
            msg += "🔸 " + p[1] + ": " + str(p[3]) + " تومان"
            if p[4]: msg += " / " + p[4]
            msg += "\n"
        bot.send_message(cid, msg)
        return

    # ============ دستورات ادمین ============
    
    # /admin - خودت رو ادمین کن (فقط اولین بار)
    if t == "/admin":
        set_admin(m, cid)
        bot.send_message(cid, "✅ حالا ادمین هستی!\n\nاز الان می‌تونی:\n• /add - اضافه کردن محصول\n• /remove - حذف محصول\n• /set - تنظیم اطلاعات")
        return
    
    # چک کن ادمین هست
    admin = is_admin(m, cid)
    
    if admin:
        # /add
        add_data = parse_add_command(t)
        if add_data:
            pid = add_product(
                add_data["name"],
                add_data["price"],
                add_data["aliases"],
                add_data["unit"],
                add_data["description"]
            )
            if pid:
                bot.send_message(cid,
                    "✅ محصول اضافه شد!\n\n"
                    "📦 نام: " + add_data["name"] + "\n"
                    "💰 قیمت: " + add_data["price"] + " تومان\n"
                    "📝 واحد: " + add_data["unit"])
            else:
                bot.send_message(cid, "⚠️ خطا در اضافه کردن")
            return
        
        # /remove
        rm_name = parse_remove_command(t)
        if rm_name:
            n = remove_product(rm_name)
            if n > 0:
                bot.send_message(cid, "✅ " + str(n) + " محصول حذف شد")
            else:
                bot.send_message(cid, "⚠️ محصول پیدا نشد")
            return
        
        # /set
        set_data = parse_set_command(t)
        if set_data:
            if update_shop_info(set_data["field"], set_data["value"]):
                bot.send_message(cid, "✅ ذخیره شد!\n" + set_data["field"] + " = " + set_data["value"])
            else:
                bot.send_message(cid, "⚠️ فیلد نامعتبر\n\nفیلدهای مجاز:\nshop_name\nshop_type\naddress\nphone\nhours\ninstagram\ndescription")
            return
        
        # /list - لیست همه محصولات
        if t in ("/list", "/محصولات"):
            products = get_products()
            if not products:
                bot.send_message(cid, "📭 محصولی نداری")
                return
            msg = "📦 لیست محصولات (" + str(len(products)) + "):\n\n"
            for p in products:
                msg += "🔸 " + p[1] + ": " + str(p[3]) + " تومان\n"
            bot.send_message(cid, msg)
            return
        
        # /help_admin
        if t == "/help_admin":
            bot.send_message(cid,
                "🛠 دستورات ادمین:\n\n"
                "➕ اضافه محصول:\n"
                "/add نام | قیمت | نام‌های دیگر | واحد | توضیح\n"
                "مثال:\n"
                "/add کرفس | 56000 | celery | کیلو | کرفس تازه\n\n"
                "➖ حذف محصول:\n"
                "/remove کرفس\n\n"
                "⚙️ تنظیم اطلاعات:\n"
                "/set shop_name میوه فروشی نازی\n"
                "/set address تهران...\n"
                "/set phone 09123456789\n"
                "/set hours هر روز ۸ تا ۲۲\n"
                "/set instagram @myshop\n\n"
                "📋 لیست محصولات:\n"
                "/list")
            return

    # چت AI
    inc_msg(m, cid)
    bot.send_message(cid, "🤔 ...")
    try:
        answer = handle_message(t, name)
        if answer:
            if len(answer) > 4000:
                for i in range(0, len(answer), 4000):
                    bot.send_message(cid, answer[i:i+4000])
                    time.sleep(0.5)
            else:
                bot.send_message(cid, answer)
        else:
            bot.send_message(cid, "⚠️ الان نمی‌تونم جواب بدم.")
    except Exception as e:
        print("[" + m + "] err: " + str(e)[:80], flush=True)
        bot.send_message(cid, "⚠️ خطا")


# ============ POLLING ============
def extract_updates(r):
    if not isinstance(r, dict): return []
    if r.get("status") == "OK":
        d = r.get("data", {})
        if isinstance(d, dict): return d.get("updates", [])
    return []


def next_off(r, cur):
    if not isinstance(r, dict): return cur
    if r.get("status") == "OK":
        d = r.get("data", {})
        if isinstance(d, dict) and d.get("next_offset_id"):
            return d["next_offset_id"]
    return cur


def extract_msg(u):
    if not isinstance(u, dict): return None, None, None
    ut = u.get("type", "")
    if ut == "StartedBot":
        return u.get("chat_id"), "__save__", ""
    if "new_message" in u:
        nm = u["new_message"]
        return u.get("chat_id"), nm.get("text", ""), nm.get("sender_name", "") or ""
    return None, None, None


def poll(bot, m):
    off = load_offset(m)
    print("[" + m + "] Poll (off=" + str(off) + ")", flush=True)
    if not off:
        try:
            r = bot.get_updates(None)
            no = next_off(r, off)
            if no: off = no; save_offset(m, off)
        except: pass

    while True:
        try:
            r = bot.get_updates(off)
            updates = extract_updates(r)
            no = next_off(r, off)
            if no and no != off:
                off = no; save_offset(m, off)

            for u in updates:
                cid, txt, fname = extract_msg(u)
                if not cid: continue
                if txt == "__save__":
                    save_member(m, cid, fname or "")
                    continue
                save_member(m, cid, fname or "")
                if not txt: continue
                try:
                    handle(bot, m, cid, txt, fname)
                except Exception as e:
                    print("[" + m + "] err: " + str(e)[:80], flush=True)
            time.sleep(1)
        except Exception as e:
            print("[" + m + "] poll err: " + str(e)[:80], flush=True)
            time.sleep(3)


def run(m, tok):
    bot = RubikaBot(tok)
    me = bot.get_me()
    if not bot.is_ok(me):
        print("[" + m + "] FAIL", flush=True)
        return
    uname = me.get("data", {}).get("bot", {}).get("username", "?")
    print("[" + m + "] OK: @" + uname, flush=True)
    threading.Thread(target=poll, args=(bot, m), daemon=True).start()


print("=" * 50, flush=True)
print("🏪 Shop Bot v1.0", flush=True)
print("=" * 50, flush=True)

bots = get_bots()
if not bots:
    print("⚠️ توکن نیست - /admin/bots", flush=True)
else:
    for m, tok in bots:
        threading.Thread(target=run, args=(m, tok), daemon=True).start()

print("Running...", flush=True)
while True: time.sleep(60)
