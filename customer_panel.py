from flask import Blueprint, render_template, request, redirect, session, flash
from customer_db import (add_customer, get_customer, get_customer_by_id, get_customer_by_login, search_products,
                         update_last_login, get_all_shops, search_shops,
                         get_shop, get_shop_info, get_products,
                         add_favorite, remove_favorite, get_favorites, is_favorite,
                         add_order, get_my_orders, get_points, count_orders)
from database import get_user_settings

customer_panel_bp = Blueprint('customer_panel', __name__)


def _cid():
    return session.get('customer_id')


def _cs():
    try: return get_user_settings(1)
    except: return None


# ============ ورود ============
@customer_panel_bp.route('/customer', methods=['GET'])
def customer_root():
    return redirect('/customer/home')


@customer_panel_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if _cid():
        return redirect('/customer/dashboard')
    error = None
    if request.method == 'POST':
        phone = (request.form.get('phone') or '').strip()
        password = (request.form.get('password') or '').strip()
        if not phone or not password:
            error = 'شماره و رمز رو وارد کن'
        else:
            cust = get_customer_by_login(phone)
            if not cust:
                error = 'شماره ثبت نشده. اول ثبت‌نام کن'
            elif cust[3] != password:
                error = 'رمز اشتباهه'
            else:
                session['customer_id'] = cust[0]
                session['customer_name'] = cust[2]
                session['customer_phone'] = cust[1]
                update_last_login(cust[0])
                return redirect('/customer/dashboard')
    return render_template('customer_login.html', error=error, current_settings=_cs())


# ============ ثبت‌نام ============
@customer_panel_bp.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if _cid():
        return redirect('/customer/dashboard')
    error = None
    if request.method == 'POST':
        phone = (request.form.get('phone') or '').strip()
        name = (request.form.get('name') or '').strip()
        password = (request.form.get('password') or '').strip()
        username = (request.form.get('username') or '').strip().lower()
        if not phone or len(phone) != 11 or not phone.startswith('09'):
            error = 'شماره موبایل معتبر وارد کن'
        elif not name:
            error = 'نام الزامی است'
        elif not username or len(username) < 4:
            error = 'نام کاربری حداقل ۴ کاراکتر'
        elif not username.replace('_', '').isalnum():
            error = 'نام کاربری فقط حروف انگلیسی، عدد و _'
        elif len(password) < 4:
            error = 'رمز حداقل ۴ کاراکتر'
        else:
            cid = add_customer(phone, name, password, username)
            if cid:
                session['customer_id'] = cid
                session['customer_name'] = name
                session['customer_phone'] = phone
                return redirect('/customer/dashboard')
            else:
                error = 'این شماره قبلاً ثبت شده'
    return render_template('customer_register.html', error=error, current_settings=_cs())


@customer_panel_bp.route('/customer/logout')
def customer_logout():
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    session.pop('customer_phone', None)
    return redirect('/customer/login')


# ============ داشبورد ============
@customer_panel_bp.route('/customer/dashboard')
def customer_dashboard():
    return redirect('/customer/home')


# ============ جستجو ============
@customer_panel_bp.route('/customer/search')
def customer_search():
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    q = (request.args.get('q') or '').strip()
    
    shops = search_shops(q) if q else get_all_shops()
    products = search_products(q) if q and len(q) >= 2 else []
    
    fav_ids = [f[0] for f in get_favorites(cid)]
    return render_template('customer_search.html',
        shops=shops, q=q, fav_ids=fav_ids, products=products,
        current_settings=_cs())


# ============ صفحه مغازه ============
@customer_panel_bp.route('/customer/shop/<int:uid>')
def customer_shop(uid):
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    shop = get_shop(uid)
    if not shop:
        flash('مغازه پیدا نشد', 'error')
        return redirect('/customer/search')
    info = get_shop_info(uid)
    products = get_products(uid)
    fav = is_favorite(cid, uid)
    return render_template('customer_shop.html',
        shop=shop, info=info, products=products, is_fav=fav,
        current_settings=_cs())


# ============ علاقه‌مندی ============
@customer_panel_bp.route('/customer/fav/<int:uid>', methods=['POST'])
def customer_fav(uid):
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    action = request.form.get('action', 'add')
    if action == 'add':
        add_favorite(cid, uid)
    else:
        remove_favorite(cid, uid)
    return redirect(request.referrer or '/customer/search')


# ============ سفارش ============
@customer_panel_bp.route('/customer/order/<int:uid>', methods=['GET', 'POST'])
def customer_order(uid):
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    shop = get_shop(uid)
    if not shop:
        return redirect('/customer/search')
    if request.method == 'POST':
        subject = (request.form.get('subject') or '').strip()
        message = (request.form.get('message') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        if not subject or not message:
            flash('موضوع و پیام الزامی است', 'error')
        else:
            add_order(cid, uid, subject, message, phone)
            flash('✅ سفارش ارسال شد', 'ok')
            return redirect('/customer/orders')
    cust = get_customer_by_id(cid)
    return render_template('customer_order.html',
        shop=shop, customer=cust, current_settings=_cs())


# ============ سفارش‌های من ============
@customer_panel_bp.route('/customer/orders')
def customer_orders():
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    orders = get_my_orders(cid)
    return render_template('customer_orders.html',
        orders=orders, current_settings=_cs())


# ============ محصولات ============
@customer_panel_bp.route('/customer/products')
def customer_products():
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    q = (request.args.get('q') or '').strip()
    if q:
        products = search_products(q)
    else:
        products = get_products()
    return render_template('customer_products.html',
        products=products, q=q, current_settings=_cs())


# ============ امتیاز من ============
@customer_panel_bp.route('/customer/points')
def customer_points():
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    points = get_points(cid)
    orders = count_orders(cid)
    return render_template('customer_points.html',
        points=points, orders=orders, current_settings=_cs())


# ============ پروفایل ============
@customer_panel_bp.route('/customer/profile')
def customer_profile():
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    cust = get_customer_by_id(cid)
    return render_template('customer_profile.html',
        customer=cust, current_settings=_cs())


# ============ HOME (داشبورد جدید) ============
@customer_panel_bp.route('/customer/home')
def customer_home():
    cid = _cid()
    is_guest = not cid
    from customer_db import (get_top_shops, get_featured_products)
    from database import get_user_settings as _gs
    import sqlite3 as _sq
    conn = _sq.connect('panel.db', timeout=15)
    c = conn.cursor()
    c.execute("""SELECT id, name, icon, color FROM product_categories
                 ORDER BY is_main DESC, sort_order LIMIT 8""")
    home_cats = c.fetchall()
    conn.close()
    top_shops = get_top_shops(6)
    featured = get_featured_products(8)
    if cid:
        cust = get_customer_by_id(cid)
        favs = get_favorites(cid)
        points = get_points(cid)
        fav_ids = [f[0] for f in favs]
    else:
        cust = None
        points = {'points': 0}
        fav_ids = []
    return render_template('customer_home.html',
        home_cats=home_cats,
        top_shops=top_shops, featured=featured,
        points=points, fav_ids=fav_ids, customer=cust,
        is_guest=is_guest,
        current_settings=_cs())


# ============ CATEGORY ============
@customer_panel_bp.route('/customer/category/<cat>')
def customer_category(cat):
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    from customer_db import get_products_by_category
    products = get_products_by_category(cat, 100)
    return render_template('customer_category.html',
        category=cat, products=products, current_settings=_cs())


# ============ LIVE SEARCH API ============
@customer_panel_bp.route('/api/suggest')
def api_suggest():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'items': []})
    from customer_db import suggest
    items = suggest(q, 8)
    return jsonify({'items': [
        {'type': i[0], 'id': i[1], 'title': i[2], 'sub': i[3]}
        for i in items
    ]})


# ============ SHOP STATS API ============
@customer_panel_bp.route('/api/shop/<int:uid>/stats')
def api_shop_stats(uid):
    from customer_db import get_shop_stats
    return jsonify(get_shop_stats(uid))


@customer_panel_bp.route('/customer/categories')
def customer_categories():
    cid = _cid()
    if not cid:
        return redirect('/customer/login')
    import sqlite3 as _sq
    q = (request.args.get('q') or '').strip()
    conn = _sq.connect('panel.db', timeout=15)
    c = conn.cursor()
    if q:
        c.execute("SELECT id,name,icon,color,is_main FROM product_categories WHERE name LIKE ? ORDER BY is_main DESC,sort_order", ('%'+q+'%',))
    else:
        c.execute("SELECT id,name,icon,color,is_main FROM product_categories ORDER BY is_main DESC,sort_order")
    all_cats = c.fetchall()
    conn.close()
    from customer_db import search_shops
    shops = search_shops(q) if q and len(q) >= 2 else []
    return render_template('customer_categories.html', all_cats=all_cats, shops=shops, q=q, current_settings=_cs())
