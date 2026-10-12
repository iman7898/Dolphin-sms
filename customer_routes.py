from flask import Blueprint, render_template, request, redirect, session, flash
from database import (add_customer, get_customer_by_phone, get_customer,
                     update_customer_lastlogin, search_shop, get_all_shops,
                     add_customer_order, get_customer_orders, get_shop_orders,
                     reply_customer_order, add_favorite, remove_favorite,
                     get_favorites, get_user_settings, get_user)

customer_bp = Blueprint('customer', __name__)


def _cid(): return session.get('customer_id')
def _is_customer(): return bool(session.get('customer_id'))
def _is_admin(): return bool(session.get('is_admin'))


def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


# ========== ورود/ثبت‌نام ==========
@customer_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if _is_customer():
        return redirect('/customer/dashboard')

    error = None
    if request.method == 'POST':
        phone = (request.form.get('phone') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not phone or len(phone) != 11 or not phone.startswith('09'):
            error = 'شماره معتبر وارد کن (09xxxxxxxxx)'
        else:
            cust = get_customer_by_phone(phone)
            if cust and cust[3] and cust[3] == password:
                session['customer_id'] = cust[0]
                session['customer_name'] = cust[2]
                update_customer_lastlogin(cust[0])
                return redirect('/customer/dashboard')
            elif cust and not cust[3]:
                # بدون رمز — ثبت‌نام ناقص، بذار رمز بذاره
                session['customer_id'] = cust[0]
                session['customer_name'] = cust[2]
                update_customer_lastlogin(cust[0])
                return redirect('/customer/dashboard')
            else:
                error = 'شماره یا رمز اشتباه'

    return render_template('customer_login.html', error=error, current_settings=_cs())


@customer_bp.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if _is_customer():
        return redirect('/customer/dashboard')

    error = None
    if request.method == 'POST':
        phone = (request.form.get('phone') or '').strip()
        name = (request.form.get('name') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not phone or len(phone) != 11 or not phone.startswith('09'):
            error = 'شماره معتبر وارد کن'
        elif not name:
            error = 'نام الزامی است'
        elif len(password) < 4:
            error = 'رمز حداقل ۴ کاراکتر'
        else:
            cid = add_customer(phone, name, password)
            if cid:
                session['customer_id'] = cid
                session['customer_name'] = name
                return redirect('/customer/dashboard')
            else:
                # شماره قبلاً ثبت شده
                cust = get_customer_by_phone(phone)
                if cust and not cust[3]:
                    error = 'شماره قبلاً ثبت شده ولی رمز نداره. با همون شماره وارد شو.'
                else:
                    error = 'این شماره قبلاً ثبت شده — لطفاً وارد شو'

    return render_template('customer_register.html', error=error, current_settings=_cs())


@customer_bp.route('/customer/logout')
def customer_logout():
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    return redirect('/customer/login')


# ========== داشبورد ==========
@customer_bp.route('/customer/dashboard')
def customer_dashboard():
    if not _is_customer():
        return redirect('/customer/login')
    cid = _cid()
    cust = get_customer(cid)
    favs = get_favorites(cid)
    orders = get_customer_orders(cid)
    return render_template('customer_dashboard.html',
        customer=cust, favorites=favs, orders=orders,
        current_settings=_cs())


# ========== جستجوی مغازه ==========
@customer_bp.route('/customer/search')
def customer_search():
    if not _is_customer():
        return redirect('/customer/login')
    q = (request.args.get('q') or '').strip()
    if q:
        shops = search_shop(q)
    else:
        shops = get_all_shops()
    cid = _cid()
    favs = get_favorites(cid)
    fav_ids = [f[0] for f in favs]
    return render_template('customer_search.html',
        shops=shops, q=q, fav_ids=fav_ids,
        current_settings=_cs())


@customer_bp.route('/customer/shop/<int:uid>')
def customer_shop_view(uid):
    if not _is_customer():
        return redirect('/customer/login')
    shop = get_user(uid)
    if not shop:
        return redirect('/customer/search')
    cid = _cid()
    favs = get_favorites(cid)
    is_fav = uid in [f[0] for f in favs]
    return render_template('customer_shop.html',
        shop=shop, is_fav=is_fav,
        current_settings=_cs())


@customer_bp.route('/customer/favorite/<int:uid>', methods=['POST'])
def customer_fav(uid):
    if not _is_customer():
        return redirect('/customer/login')
    cid = _cid()
    action = request.form.get('action', 'add')
    if action == 'add':
        add_favorite(cid, uid)
    else:
        remove_favorite(cid, uid)
    return redirect(request.referrer or '/customer/search')


# ========== سفارش ==========
@customer_bp.route('/customer/order/<int:uid>', methods=['GET', 'POST'])
def customer_new_order(uid):
    if not _is_customer():
        return redirect('/customer/login')
    shop = get_user(uid)
    if not shop:
        return redirect('/customer/search')

    if request.method == 'POST':
        subject = (request.form.get('subject') or '').strip()
        message = (request.form.get('message') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        if not subject or not message:
            flash('موضوع و پیام الزامی است', 'error')
        else:
            cid = _cid()
            add_customer_order(cid, uid, subject, message, phone)
            flash('✅ سفارش ارسال شد', 'ok')
            return redirect('/customer/dashboard')

    cid = _cid()
    cust = get_customer(cid)
    return render_template('customer_order.html',
        shop=shop, customer=cust,
        current_settings=_cs())


@customer_bp.route('/customer/orders')
def customer_orders_list():
    if not _is_customer():
        return redirect('/customer/login')
    cid = _cid()
    orders = get_customer_orders(cid)
    return render_template('customer_orders.html',
        orders=orders,
        current_settings=_cs())


# ========== پنل مغازه‌دار — سفارش‌های مشتری‌ها ==========
@customer_bp.route('/panel/customer-orders')
def panel_customer_orders():
    uid = session.get('user_id')
    if not uid:
        return redirect('/panel/login')
    orders = get_shop_orders(uid)
    return render_template('panel_customer_orders.html',
        orders=orders,
        current_settings=_cs(uid))


@customer_bp.route('/panel/customer-orders/<int:oid>/reply', methods=['POST'])
def panel_order_reply(oid):
    uid = session.get('user_id')
    if not uid:
        return redirect('/panel/login')
    reply = (request.form.get('reply') or '').strip()
    if reply:
        reply_customer_order(oid, reply)
        flash('✅ پاسخ ارسال شد', 'ok')
    return redirect('/panel/customer-orders')


@customer_bp.route('/customer')
def customer_root():
    if _is_customer():
        return redirect('/customer/dashboard')
    return redirect('/customer/login')
