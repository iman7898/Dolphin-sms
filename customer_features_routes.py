import random
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, flash, jsonify
from customer_db import (get_customer_by_id, get_shop, get_products,
                         get_my_orders, add_order, get_points, count_orders,
                         add_favorite, remove_favorite, get_favorites, is_favorite)
from customer_features import (add_to_cart, get_cart_items, update_cart_qty,
                               remove_from_cart, clear_cart, count_cart,
                               add_order_status, get_order_status,
                               add_rating, get_rating, get_shop_avg_rating,
                               get_shop_ratings, add_notif, get_notifs,
                               count_unread_notifs, mark_notif_read,
                               mark_all_notifs_read, check_coupon, calc_discount,
                               use_coupon, send_customer_msg, send_shop_msg,
                               get_chat)
from database import get_user_settings

feat_bp = Blueprint('customer_features', __name__)


def _cid(): return session.get('customer_id')
def _cs():
    try: return get_user_settings(1)
    except: return None


# ============ CART ============
@feat_bp.route('/customer/cart/<int:shop_id>')
def view_cart(shop_id):
    cid = _cid()
    if not cid: return redirect('/customer/login')
    shop = get_shop(shop_id)
    if not shop: return redirect('/customer/search')
    items = get_cart_items(cid, shop_id)
    total = sum(i[4] * i[3] for i in items)
    return render_template('customer_cart.html',
        shop=shop, items=items, total=total, current_settings=_cs())


@feat_bp.route('/customer/cart/<int:shop_id>/add', methods=['POST'])
def add_cart(shop_id):
    cid = _cid()
    if not cid: return jsonify({'ok': False})
    pid = request.form.get('product_id')
    qty = int(request.form.get('qty', 1))
    price = int(request.form.get('price', 0))
    try:
        add_to_cart(cid, shop_id, int(pid), price, qty)
        flash('✅ به سبد خرید اضافه شد', 'ok')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(request.referrer or f'/customer/shop/{shop_id}')


@feat_bp.route('/customer/cart/item/<int:item_id>/update', methods=['POST'])
def update_item(item_id):
    if not _cid(): return redirect('/customer/login')
    qty = int(request.form.get('qty', 1))
    update_cart_qty(item_id, qty)
    return redirect(request.referrer or '/customer/dashboard')


@feat_bp.route('/customer/cart/item/<int:item_id>/remove', methods=['POST'])
def remove_item(item_id):
    if not _cid(): return redirect('/customer/login')
    remove_from_cart(item_id)
    flash('حذف شد', 'ok')
    return redirect(request.referrer or '/customer/dashboard')


@feat_bp.route('/customer/cart/<int:shop_id>/checkout', methods=['POST'])
def cart_checkout(shop_id):
    cid = _cid()
    if not cid: return redirect('/customer/login')
    items = get_cart_items(cid, shop_id)
    if not items:
        flash('سبد خرید خالیه', 'error')
        return redirect(f'/customer/cart/{shop_id}')

    total = sum(i[4] * i[3] for i in items)
    coupon_code = (request.form.get('coupon') or '').strip()
    coupon = check_coupon(coupon_code) if coupon_code else None
    discount = calc_discount(coupon, total)
    final = total - discount

    # ساخت پیام سفارش
    lines = []
    for it in items:
        lines.append(f"• {it[2]} × {it[3]} = {it[4] * it[3]:,} تومان")
    msg = "🛒 سفارش جدید:\n\n" + "\n".join(lines)
    msg += f"\n\n💰 جمع: {total:,} تومان"
    if discount > 0:
        msg += f"\n🎁 تخفیف: {discount:,} تومان"
        msg += f"\n✅ قابل پرداخت: {final:,} تومان"

    subject = f"سفارش {len(items)} محصول"
    oid = add_order(cid, shop_id, subject, msg, '')
    add_order_status(oid, 'pending', 'سفارش ثبت شد')

    if coupon and coupon_id_check(coupon):
        use_coupon(coupon['id'], cid, oid, discount)

    # نوتیف به مشتری
    add_notif(cid, '✅ سفارش ثبت شد',
              f'سفارش شما در حال بررسی است. مبلغ: {final:,} تومان',
              '✅', '/customer/orders')

    clear_cart(cid, shop_id)
    flash(f'✅ سفارش ثبت شد. مبلغ نهایی: {final:,} تومان', 'ok')
    return redirect('/customer/orders')


def coupon_id_check(c):
    return c and c.get('id')


# ============ RATE ============
@feat_bp.route('/customer/rate/<int:shop_id>', methods=['GET', 'POST'])
def rate_shop(shop_id):
    cid = _cid()
    if not cid: return redirect('/customer/login')
    shop = get_shop(shop_id)
    if not shop: return redirect('/customer/search')
    my = get_rating(cid, shop_id)
    if request.method == 'POST':
        stars = int(request.form.get('stars', 5))
        comment = (request.form.get('comment') or '').strip()
        add_rating(cid, shop_id, stars, comment)
        flash('✅ نظر شما ثبت شد', 'ok')
        return redirect(f'/customer/shop/{shop_id}')
    return render_template('customer_rate.html',
        shop=shop, my_rating=my, current_settings=_cs())


@feat_bp.route('/customer/ratings/<int:shop_id>')
def shop_ratings(shop_id):
    cid = _cid()
    if not cid: return redirect('/customer/login')
    shop = get_shop(shop_id)
    if not shop: return redirect('/customer/search')
    avg, cnt = get_shop_avg_rating(shop_id)
    ratings = get_shop_ratings(shop_id, 50)
    return render_template('customer_ratings.html',
        shop=shop, avg=avg, cnt=cnt, ratings=ratings, current_settings=_cs())


# ============ NOTIFICATIONS ============
@feat_bp.route('/customer/notifications')
def customer_notifs():
    cid = _cid()
    if not cid: return redirect('/customer/login')
    notifs = get_notifs(cid, 100)
    return render_template('customer_notifs.html',
        notifs=notifs, current_settings=_cs())


@feat_bp.route('/customer/notifications/<int:nid>/read', methods=['POST'])
def mark_read(nid):
    if not _cid(): return jsonify({'ok': False})
    mark_notif_read(nid)
    return jsonify({'ok': True})


@feat_bp.route('/customer/notifications/read-all', methods=['POST'])
def mark_all_read():
    cid = _cid()
    if not cid: return jsonify({'ok': False})
    mark_all_notifs_read(cid)
    return jsonify({'ok': True})


@feat_bp.route('/customer/notifications/count')
def notifs_count():
    cid = _cid()
    if not cid: return jsonify({'count': 0})
    return jsonify({'count': count_unread_notifs(cid)})


# ============ COUPON ============
@feat_bp.route('/customer/coupon/check', methods=['POST'])
def coupon_check():
    if not _cid(): return jsonify({'ok': False})
    code = (request.form.get('code') or '').strip()
    total = int(request.form.get('total', 0))
    c = check_coupon(code)
    if not c:
        return jsonify({'ok': False, 'msg': 'کد نامعتبر یا منقضی'})
    if total < c['min_order']:
        return jsonify({'ok': False, 'msg': f'حداقل خرید {c["min_order"]:,} تومان'})
    discount = calc_discount(c, total)
    return jsonify({'ok': True, 'discount': discount,
                    'type': c['type'], 'value': c['value']})


# ============ CHAT ============
@feat_bp.route('/customer/chat/<int:shop_id>', methods=['GET', 'POST'])
def customer_chat(shop_id):
    cid = _cid()
    if not cid: return redirect('/customer/login')
    shop = get_shop(shop_id)
    if not shop: return redirect('/customer/search')
    if request.method == 'POST':
        msg = (request.form.get('message') or '').strip()
        if msg:
            send_customer_msg(cid, shop_id, msg)
        return redirect(f'/customer/chat/{shop_id}')
    msgs = get_chat(cid, shop_id, 200)
    return render_template('customer_chat.html',
        shop=shop, messages=msgs, current_settings=_cs())


# ============ ORDER TRACK ============
@feat_bp.route('/customer/order/<int:order_id>/track')
def track_order(order_id):
    cid = _cid()
    if not cid: return redirect('/customer/login')
    # چک کن سفارش مال خودش باشه
    my = get_my_orders(cid)
    order = None
    for o in my:
        if o[0] == order_id:
            order = o
            break
    if not order: return redirect('/customer/orders')
    statuses = get_order_status(order_id)
    return render_template('customer_track.html',
        order=order, statuses=statuses, current_settings=_cs())


# ============ CART COUNT (API) ============
@feat_bp.route('/customer/cart/count')
def cart_count():
    cid = _cid()
    if not cid: return jsonify({'count': 0})
    return jsonify({'count': count_cart(cid)})


# ============ SABAD KOL (همه سبدها) ============
@feat_bp.route('/customer/cart/list')
def cart_list():
    cid = session.get('customer_id')
    if not cid:
        return redirect('/customer/login')
    import sqlite3 as _s
    conn = _s.connect('panel.db', timeout=15)
    c = conn.cursor()
    c.execute("""SELECT ca.shop_id,
                        (SELECT username FROM users WHERE id=ca.shop_id) AS shop_name,
                        COUNT(ci.id) AS items,
                        SUM(ci.price * ci.quantity) AS total
                 FROM cart ca
                 JOIN cart_items ci ON ci.cart_id = ca.id
                 WHERE ca.customer_id=?
                 GROUP BY ca.shop_id
                 ORDER BY ca.shop_id DESC""", (cid,))
    carts = c.fetchall()
    conn.close()
    from database import get_user_settings
    try: cs = get_user_settings(1)
    except: cs = None
    return render_template('customer_cart_list.html', carts=carts, current_settings=cs)


# ============ WHEEL OF FORTUNE ============
import random
from datetime import datetime
import sqlite3

@feat_bp.route('/customer/wheel')
def customer_wheel():
    if not session.get('customer_id'): return redirect('/customer/login')
    cid = session['customer_id']
    try:
        conn = sqlite3.connect('panel.db')
        cur = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(*) FROM wheel_spins WHERE customer_id=? AND DATE(created_at)=?", (cid, today))
        has_spun = cur.fetchone()[0] > 0
        conn.close()
    except Exception as e:
        print("WHEEL GET ERROR:", e, flush=True)
        has_spun = False # اگه خطا داد، بذار بچرخونه
        
    return render_template('customer_wheel.html', has_spun=has_spun)

@feat_bp.route('/customer/wheel/spin', methods=['POST'])
def customer_wheel_spin():
    if not session.get('customer_id'): return {'error': 'وارد نشدید'}, 401
    cid = session['customer_id']
    
    try:
        conn = sqlite3.connect('panel.db')
        cur = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cur.execute("SELECT COUNT(*) FROM wheel_spins WHERE customer_id=? AND DATE(created_at)=?", (cid, today))
        if cur.fetchone()[0] > 0:
            conn.close()
            return {'error': 'شما امروز شانستون رو امتحان کردید!'}
            
        prizes = [
            {'label': 'شانس نیاوردی', 'code': '', 'val': 0},
            {'label': '۵٪ تخفیف', 'code': 'WIN5', 'val': 5},
            {'label': '۱۰٪ تخفیف', 'code': 'WIN10', 'val': 10},
            {'label': 'ارسال رایگان', 'code': 'FREESHIP', 'val': 100},
            {'label': '۲۰٪ تخفیف', 'code': 'WIN20', 'val': 20},
            {'label': '۱۰ امتیاز', 'code': 'POINTS10', 'val': 0}
        ]
        
        # شانس‌ها وزن‌دهی شدند (شانس نیاوردی بیشتر از همه)
        weights = [45, 20, 15, 10, 5, 5]
        prize = random.choices(prizes, weights=weights, k=1)[0]
        
        # ذخیره در جدول گردونه
        cur.execute("INSERT INTO wheel_spins (customer_id, prize) VALUES (?, ?)", (cid, prize['label']))
        
        # اگه کوپن بود
        random_code = ""
        if prize['code']:
            import uuid
            random_code = f"{prize['code']}-{uuid.uuid4().hex[:4].upper()}"
            try:
                cur.execute("""INSERT INTO coupons (code, discount_type, value, min_order, max_uses, active) 
                               VALUES (?, 'percent', ?, 0, 1, 1)""", (random_code, prize['val']))
            except Exception as coupon_err:
                print("COUPON SAVE ERR:", coupon_err, flush=True)
                
        conn.commit()
        conn.close()
        
        return {'prize': prize['label'], 'code': random_code}
        
    except Exception as e:
        print("WHEEL SPIN ERROR:", str(e), flush=True)
        return {'error': f'خطای دیتابیس: {str(e)}'}

# ============ OTP LOGIN ============
import random
from datetime import datetime, timedelta

@feat_bp.route('/customer/otp', methods=['GET'])
def customer_otp_page():
    return render_template('customer_otp.html')

@feat_bp.route('/customer/otp/send', methods=['POST'])
def customer_otp_send():
    phone = request.json.get('phone', '').strip()
    if not phone or len(phone) != 11 or not phone.startswith('09'):
        return {'error': 'شماره موبایل نامعتبر است'}
    
    code = str(random.randint(1000, 9999))
    expires = (datetime.now() + timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("DELETE FROM otp_codes WHERE phone=?", (phone,))
    c.execute("INSERT INTO otp_codes (phone, code, expires_at) VALUES (?, ?, ?)", (phone, code, expires))
    conn.commit()
    conn.close()
    
    # ارسال پیامک با سرویس موجود
    try:
        from adapters.sms_adapter import send_sms
        msg = f"🐬 کد ورود شما به فروشگاه: {code}\nاین کد ۲ دقیقه اعتبار دارد."
        send_sms(phone, msg)
        print(f"DEBUG OTP SENT: {phone} -> {code}", flush=True)
        # کد رو برای تست برمی‌گردونیم (بعداً برش می‌داریم)
        return {'ok': True, 'msg': 'کد ارسال شد', 'test_code': code}
    except Exception as e:
        print(f"DEBUG OTP ERROR: {e}", flush=True)
        return {'error': 'خطا در ارسال پیامک، لطفا دوباره تلاش کنید'}

@feat_bp.route('/customer/otp/verify', methods=['POST'])
def customer_otp_verify():
    phone = request.json.get('phone', '').strip()
    code = request.json.get('code', '').strip()
    
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT code, expires_at FROM otp_codes WHERE phone=?", (phone,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return {'error': 'کدی یافت نشد، دوباره درخواست دهید'}
        
    db_code, expires_at = row
    if db_code != code:
        # اگه کد تست بود (برای دیباگ)
        if code == '0000':
            pass  # قبولش کن
        else:
            conn.close()
            return {'error': 'کد وارد شده اشتباه است'}
        
    if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
        conn.close()
        return {'error': 'کد منقضی شده است'}
        
    # اگه تایید شد، چک کن کاربر هست یا نه
    c.execute("SELECT id, name FROM customers WHERE phone=?", (phone,))
    cust = c.fetchone()
    
    if cust:
        session['customer_id'] = cust[0]
        session['customer_name'] = cust[1]
        session['customer_phone'] = phone
        c.execute("DELETE FROM otp_codes WHERE phone=?", (phone,))
        conn.commit()
        conn.close()
        return {'ok': True, 'redirect': '/customer/home'}
    else:
        # کاربر جدیده، بذار توی سشن تا اسمش رو بگیریم
        session['temp_otp_phone'] = phone
        c.execute("DELETE FROM otp_codes WHERE phone=?", (phone,))
        conn.commit()
        conn.close()
        return {'ok': True, 'redirect': '/customer/otp/register'}

import json
from pywebpush import webpush, WebPushException

VAPID_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg6fxq+9Kmda9wr6tw
whiUQIVytHCw/e5D4SWPATzqmVuhRANCAAR0j6qUMC4rnkZUUvnC/zaaLzRIAnFi
pY4GHjm15iDJ6YZnC4kNDhXqCTU8hKpsTIZ69lpZ7a7uM7XPSXxWHpR7
-----END PRIVATE KEY-----
"""
VAPID_PUBLIC_KEY = "BHSPqpQwLiueRlRS-cL_NpovNEgCcWKljgYeObXmIMnphmcLiQ0OFeoJNTyEqmxMhnr2Wlntru4ztc9JfFYelHs"
VAPID_CLAIMS = {"sub": "mailto:admin@dolphin.com"}

@feat_bp.route('/api/push/key')
def push_public_key():
    return {'key': VAPID_PUBLIC_KEY}

@feat_bp.route('/api/push/subscribe', methods=['POST'])
def push_subscribe():
    if not session.get('user_id') and not session.get('customer_id'):
        return {'error': 'not logged in'}, 401
    uid = session.get('user_id') or session.get('customer_id')
    sub_str = json.dumps(request.json)
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT id FROM push_subscriptions WHERE user_id=? AND subscription=?", (uid, sub_str))
    if not c.fetchone():
        c.execute("INSERT INTO push_subscriptions (user_id, subscription) VALUES (?, ?)", (uid, sub_str))
        conn.commit()
    conn.close()
    return {'ok': True}

def send_push_to_user(user_id, title, body, url='/'):
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("SELECT subscription FROM push_subscriptions WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    for (sub_str,) in rows:
        try:
            webpush(
                subscription_info=json.loads(sub_str),
                data=json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except Exception as e:
            print(f"Push error: {e}", flush=True)

@feat_bp.route('/api/push/test')
def push_test():
    cid = session.get('customer_id')
    if not cid: return {'error': 'اول لاگین کن'}
    
    try:
        conn = sqlite3.connect('panel.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM push_subscriptions WHERE user_id=?", (cid,))
        count = c.fetchone()[0]
        conn.close()
        
        if count == 0:
            return {'error': 'شما هنوز دکمه فعالسازی رو نزدید یا مرورگر اجازه نداده!'}
            
        send_push_to_user(cid, '🐬 تست موفق!', 'این یه نوتیفیکیشن واقعی از طرف Dolphin SMS هست.')
        return {'ok': True, 'msg': 'نوتیفیکیشن ارسال شد! به گوشیت نگاه کن.'}
    except Exception as e:
        return {'error': f'خطای سرور: {str(e)}'}
