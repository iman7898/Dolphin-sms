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
