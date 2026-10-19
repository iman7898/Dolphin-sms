from image_generator import generate_image
from flask import (Flask, request, render_template, redirect, url_for,
                   session, jsonify, flash)
from database import *
from database import (find_user_by_ref_code, process_referral,
                      get_or_create_referral_code)
from adapters.sms_adapter import send_sms, check_balance
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
from functools import wraps
import hashlib, hmac, os, secrets, time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app = Flask(__name__)

# ⚡ Cache + Gzip
import gzip as _gz
from io import BytesIO as _BIO

@app.after_request
def _cache_response(response):
    # Gzip
    try:
        accept = request.headers.get('Accept-Encoding', '')
        if 'gzip' in accept.lower() and response.status_code == 200:
            if not response.direct_passthrough:
                ct = response.content_type or ''
                if any(x in ct for x in ['text/', 'json', 'javascript', 'css', 'xml', 'svg']):
                    data = response.get_data()
                    if len(data) > 500:
                        buf = _BIO()
                        with _gz.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as gz:
                            gz.write(data)
                        comp = buf.getvalue()
                        if len(comp) < len(data):
                            response.set_data(comp)
                            response.headers['Content-Encoding'] = 'gzip'
                            response.headers['Content-Length'] = str(len(comp))
                            response.headers['Vary'] = 'Accept-Encoding'
    except Exception:
        pass
    # Cache استاتیک
    try:
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=86400'
    except Exception:
        pass
    return response


app = Flask(__name__)

# ⚡ Gzip Compression دستی
import gzip as _gz
from io import BytesIO as _BIO

@app.after_request
def _gzip_response(response):
    try:
        accept = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept.lower():
            return response
        if response.status_code < 200 or response.status_code >= 300:
            return response
        if response.direct_passthrough:
            return response
        ct = response.content_type or ''
        if not (ct.startswith('text/') or 'json' in ct or 'javascript' in ct or 'css' in ct or 'xml' in ct or 'svg' in ct):
            return response
        data = response.get_data()
        if len(data) < 500:
            return response
        buf = _BIO()
        with _gz.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as gz:
            gz.write(data)
        compressed = buf.getvalue()
        if len(compressed) >= len(data):
            return response
        response.set_data(compressed)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = str(len(compressed))
        response.headers['Vary'] = 'Accept-Encoding'
    except Exception:
        pass
    return response

print("✅ Gzip دستی فعال شد")
app = Flask(__name__)



app.secret_key = SECRET_KEY

@app.route('/sw-new.js')
def serve_sw_new():
    from flask import send_file
    return send_file('static/sw-new.js', mimetype='application/javascript')


# ============ SERVICE WORKER (ROOT SCOPE) ============
from flask import send_file
@app.route('/service-worker.js')
def serve_sw():
    return send_file('static/pwa/service-worker.js', mimetype='application/javascript')


# 🔐 تنظیمات امنیتی session
from datetime import timedelta as _td
app.config['PERMANENT_SESSION_LIFETIME'] = _td(days=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # اگر HTTPS شد، True کن
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# ===== توابع امنیتی =====
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB

def _hash_password(password):
    """هش امن رمز با PBKDF2"""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000)
    return f"pbkdf2${salt}${h.hex()}"

def _verify_password(stored, password):
    """چک رمز - پشتیبانی از plaintext قدیمی و هش جدید"""
    if not stored:
        return False
    if stored.startswith("pbkdf2$"):
        try:
            _, salt, h = stored.split("$", 2)
            new_h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()
            return hmac.compare_digest(h, new_h)
        except Exception:
            return False
    # plaintext قدیمی
    return hmac.compare_digest(stored, password)

def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def _save_upload(file, prefix, user_id):
    """ذخیره فایل آپلود شده"""
    if not file or not file.filename:
        return None
    if not _allowed_file(file.filename):
        return None
    # چک سایز
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    fname = f"{prefix}_{user_id}_{int(time.time())}.{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    file.save(fpath)
    return f"/static/uploads/{fname}"

def _csrf_token():
    """تولید/دریافت توکن CSRF"""
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(32)
    return session["csrf"]

def _check_csrf():
    """بررسی توکن CSRF"""
    token = request.form.get("csrf") or request.headers.get("X-CSRF")
    return token and hmac.compare_digest(token, session.get("csrf", ""))

app.jinja_env.globals["csrf_token"] = _csrf_token


@app.context_processor
def inject_global_settings():
    """تزریق تنظیمات به همه قالب‌ها (پس‌زمینه، آواتار، تم)"""
    try:
        if session.get("is_admin"):
            s = get_admin_settings()
        elif session.get("user_id"):
            s = get_user_settings(session["user_id"])
        else:
            s = {"avatar": None, "bg": None, "theme": "neon"}
    except Exception:
        s = {"avatar": None, "bg": None, "theme": "neon"}
    return {"current_settings": s}


@app.after_request
def _security_headers(response):
    # غیرفعال کردن Cache برای HTML ها
    if response.content_type and 'text/html' in response.content_type:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    """هدرهای امنیتی"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response




def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "unknown"


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # اگه مغازه‌دار لاگینه، کیکش کن
        if session.get("user_id"):
            session.clear()
            return redirect(url_for("admin_login"))
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # اگه ادمین لاگینه، کیکش کن
        if session.get("is_admin"):
            session.clear()
            return redirect(url_for("panel_login"))
        if not session.get("user_id"):
            return redirect(url_for("panel_login"))
        # چک کن کاربر هنوز وجود داره
        user = get_user(session["user_id"])
        if not user:
            session.clear()
            return redirect(url_for("panel_login"))
        if not is_user_active(session["user_id"]):
            session.clear()
            return redirect(url_for("panel_login") + "?expired=1")
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return redirect(url_for("admin_login"))


# ============ پنل ادمین ============
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        ip = get_client_ip()
        ua = request.headers.get("User-Agent", "unknown")
        # Rate limiting
        attempts = count_recent_attempts(ip, 15)
        if attempts >= 8:
            error = "تلاش بیش از حد. ۱۵ دقیقه صبر کن."
            log_login(u or "unknown", ip, ua, user_id=None, status="rate_limited")
            return render_template("admin_login.html", error=error)

        if u == ADMIN_USERNAME and _verify_password(ADMIN_PASSWORD, p):
            clear_login_attempts(ip)
            session.clear()
            log_login(u, ip, ua, user_id=None, status="success")
            session["is_admin"] = True
            session["admin_user"] = u
            session["login_time"] = time.time()
            session["user_agent"] = ua
            return redirect(url_for("admin_dashboard"))
        else:
            add_login_attempt(ip, u or "unknown")
            log_login(u or "unknown", ip, ua, user_id=None, status="failed")
            error = "نام کاربری یا رمز اشتباه است"
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    raw_users = get_all_users()
    users = []
    for u in raw_users:
        user_id = u[0]
        users.append({
            "id": u[0],
            "username": u[1],
            "shop_name": u[3],
            "phone": u[4],
            "start_date": u[5],
            "end_date": u[6],
            "status": u[7],
            "sms_limit": u[8] if len(u) > 8 else 1000,
            "days_left": days_remaining(user_id),
            "sms_left": sms_remaining(user_id),
            "sms_used": sms_used(user_id),
        })
    return render_template("admin_dashboard.html",
        users=users,
        total_sms=count_sms(),
        balance=check_balance(),
        stats=get_login_stats(),
        unread_chat=count_unread_for_admin(),
        current_theme=session.get("admin_theme", "neon"))


@app.route("/admin/users/add", methods=["POST"])
@admin_required
def admin_add_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    shop_name = request.form.get("shop_name", "").strip()
    phone = request.form.get("phone", "").strip()
    days = int(request.form.get("days", 30) or 30)
    sms_limit = int(request.form.get("sms_limit", 1000) or 1000)

    if not username or not password:
        flash("نام کاربری و رمز الزامی است", "error")
    else:
        ok, result = add_user(username, password, shop_name, phone, days, sms_limit)
        if ok:
            flash(f"کاربر {username} ساخته شد", "success")
        else:
            flash(f"خطا: {result}", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    user = get_user(user_id)
    if not user:
        return "کاربر پیدا نشد", 404
    premium_status = get_premium_status(user_id)
    return render_template("admin_user_detail.html",
        user=user,
        user_sms=get_all_sms(100, user_id=user_id),
        user_logins=get_user_logins(user_id, limit=50),
        sms_count=count_sms(user_id=user_id),
        sms_left=sms_remaining(user_id),
        days_left=days_remaining(user_id),
        time_left=time_remaining_detailed(user_id),
        premium=premium_status)


@app.route("/admin/user/<int:user_id>/suspend", methods=["POST"])
@admin_required
def admin_user_suspend(user_id):
    suspend_user(user_id)
    flash("کاربر متوقف شد", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


@app.route("/admin/user/<int:user_id>/activate", methods=["POST"])
@admin_required
def admin_user_activate(user_id):
    activate_user(user_id)
    flash("کاربر فعال شد", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


@app.route("/admin/user/<int:user_id>/extend", methods=["POST"])
@admin_required
def admin_user_extend(user_id):
    days = int(request.form.get("days", 30) or 30)
    extend_user_days(user_id, days)
    flash(f"{days} روز اضافه شد", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


@app.route("/admin/user/<int:user_id>/update_limit", methods=["POST"])
@admin_required
def admin_user_update_limit(user_id):
    new_limit = int(request.form.get("sms_limit", 1000) or 1000)
    update_sms_limit(user_id, new_limit)
    flash(f"محدودیت پیامک به {new_limit} تغییر کرد", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


@app.route("/admin/user/<int:user_id>/update_end_date", methods=["POST"])
@admin_required
def admin_user_update_end_date(user_id):
    from datetime import datetime
    new_date = request.form.get("end_date", "").strip()
    if new_date:
        try:
            # فرمت ورودی: YYYY-MM-DDTHH:MM:SS
            if "T" in new_date:
                dt = datetime.strptime(new_date, "%Y-%m-%dT%H:%M:%S")
            else:
                dt = datetime.strptime(new_date, "%Y-%m-%d %H:%M:%S")
            db_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            update_end_date(user_id, db_date)
            flash("تاریخ پایان بروزرسانی شد", "success")
        except Exception as e:
            flash(f"خطا در تاریخ: {e}", "error")
    return redirect(url_for("admin_user_detail", user_id=user_id))



@app.route("/admin/logs")
@admin_required
def admin_logs():
    return render_template("admin_logs.html",
        logs=get_all_logins(200),
        stats=get_login_stats())


@app.route("/admin/logs/clear", methods=["POST"])
@admin_required
def admin_logs_clear():
    clear_login_logs()
    return redirect(url_for("admin_logs"))


# ============ پنل مغازه‌دار ============
@app.route("/panel/login", methods=["GET", "POST"])
def panel_login():
    error = None
    expired = request.args.get("expired")
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        ip = get_client_ip()
        ua = request.headers.get("User-Agent", "unknown")
        # Rate limiting
        attempts = count_recent_attempts(ip, 15)
        if attempts >= 8:
            error = "تلاش بیش از حد. ۱۵ دقیقه صبر کن."
            log_login(u or "unknown", ip, ua, user_id=None, status="rate_limited")
            return render_template("panel_login.html", error=error, expired=expired)

        try:
            from database import get_user_by_username_or_phone as _getu
            user = _getu(u)
        except Exception:
            user = get_user_by_username(u)
        if user and _verify_password(user[2], p):
            user_id = user[0]
            if not is_user_active(user_id):
                log_login(u, ip, ua, user_id=user_id, status="expired")
                error = "اشتراک یا اعتبار پیامک شما به پایان رسیده"
            else:
                clear_login_attempts(ip)
                session.clear()
                log_id = log_login(u, ip, ua, user_id=user_id, status="success")
                # 🔒 چک 2FA
                try:
                    from database import get_2fa as _g2fa
                    f2 = _g2fa(user_id)
                except Exception:
                    f2 = {'enabled': 0}
                if f2.get('enabled'):
                    # پیامک کد
                    try:
                        from database import generate_2fa_code as _g2code
                        code = _g2code(user_id)
                        # 🔥 ارسال پیامک — اگه خط نداری، کد رو توی log چاپ کن
                        try:
                            from twofa_routes import _send_2fa_sms
                            r = _send_2fa_sms(f2.get('phone',''), code)
                            if not (r and r.get('status') == 'success'):
                                print(f'⚠️ پیامک نرفت — کد 2FA برای کاربر {user_id}: {code}', flush=True)
                        except Exception as e:
                            print(f'⚠️ خطا پیامک: {e} — کد: {code}', flush=True)
                    except Exception as e:
                        print(f'⚠️ خطا 2FA: {e}', flush=True)
                    session['pending_2fa_uid'] = user_id
                    session['pending_2fa_name'] = u
                    session['pending_2fa_log'] = log_id
                    return redirect('/panel/2fa/verify')

                session.permanent = True
                session["user_id"] = user_id
                session["user_name"] = u
                session["log_id"] = log_id
                session["login_time"] = time.time()
                session["user_agent"] = ua
                return redirect(url_for("panel_dashboard"))
        else:
            add_login_attempt(ip, u or "unknown")
            log_login(u or "unknown", ip, ua, user_id=None, status="failed")
            error = "نام کاربری یا رمز اشتباه است"
    return render_template("panel_login.html", error=error, expired=expired)


@app.route("/panel/logout")
def panel_logout():
    if session.get("log_id"):
        log_logout(session["log_id"])
    session.clear()
    return redirect(url_for("panel_login"))


@app.route("/panel/dashboard")
@user_required
def panel_dashboard():
    user_id = session["user_id"]
    user = get_user(user_id)
    return render_template("panel_dashboard.html",
        user=user,
        sms_list=get_all_sms(50, user_id=user_id),
                           wallet_balance=get_wallet(session["user_id"]),
                           sms_price=5000,
        total=count_sms(user_id=user_id),
        days_left=days_remaining(user_id),
        sms_left=sms_remaining(user_id),
        sms_limit=user[8],
        balance=check_balance(),
        time_left=time_remaining_detailed(user_id),
        unread_chat=count_unread_for_user(user_id))


@app.route("/panel/send", methods=["GET", "POST"])
@user_required
def panel_send():
    result = None
    user_id = session["user_id"]
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()
        if not phone or not message:
            result = {"status": "error", "message": "شماره و متن الزامی است"}
        elif not (phone.startswith("09") and len(phone) == 11):
            result = {"status": "error", "message": "شماره معتبر نیست"}
        elif sms_remaining(user_id) <= 0:
            result = {"status": "error", "message": "اعتبار پیامک شما تمام شده"}
        else:
            # 💰 هزینه هر پیامک (ریال) — قابل تغییر
            SMS_PRICE = 5000
            if get_wallet(user_id) < SMS_PRICE:
                result = {"status": "error", "message": "موجودی کیف پول کافی نیست"}
            else:
                result = send_sms(phone, message)
                log_sms(phone, message, result.get("status", "unknown"), user_id=user_id)
                # فقط اگه پیامک با موفقیت ارسال شد، از کیف پول کم کن
                if result.get("status") == "success":
                    deduct_wallet(user_id, SMS_PRICE, f"ارسال پیامک به {phone}")
                    # 🎁 امتیاز وفاداری (۲x در پنجشنبه/جمعه)
                    try:
                        mult = loyalty_multiplier()
                        add_loyalty_points(user_id, 1 * mult, f'ارسال پیامک ({mult}x)')
                    except Exception:
                        pass
    return render_template("panel_send.html", result=result,
                           sms_left=sms_remaining(user_id),
                           schedules=get_user_schedules(user_id))


# ============ برنامه‌ریزی پیام‌ها ============
@app.route("/panel/schedule/add", methods=["POST"])
@user_required
def panel_add_schedule():
    user_id = session["user_id"]
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    daily_limit = int(request.form.get("daily_limit", 100) or 100)

    if not message or not start_date or not end_date:
        return jsonify({"status": "error", "message": "همه فیلدها الزامی است"}), 400

    add_schedule(user_id, title, message, start_date, end_date, daily_limit)
    return redirect(url_for("panel_send"))


@app.route("/panel/schedule/delete/<int:schedule_id>", methods=["POST"])
@user_required
def panel_delete_schedule(schedule_id):
    delete_schedule(schedule_id, session["user_id"])
    return redirect(url_for("panel_send"))


@app.route("/panel/schedule/toggle/<int:schedule_id>", methods=["POST"])
@user_required
def panel_toggle_schedule(schedule_id):
    toggle_schedule(schedule_id, session["user_id"])
    return redirect(url_for("panel_send"))


# ============ چت ============
@app.route("/panel/chat")
@user_required
def panel_chat():
    user_id = session["user_id"]
    mark_messages_read(user_id, "shopkeeper")
    return render_template("chat.html",
        messages=get_chat_messages(user_id),
        user_id=user_id,
        is_admin=False,
        unread_chat=count_unread_for_user(user_id))


@app.route("/panel/chat/send", methods=["POST"])
@user_required
def panel_chat_send():
    msg = request.form.get("message", "").strip()
    if msg:
        add_chat_message(session["user_id"], "shopkeeper", msg)
    return redirect(url_for("panel_chat"))


@app.route("/admin/chat")
@admin_required
def admin_chat_list():
    return render_template("admin_chat_list.html",
        chats=get_all_chat_users(),
        unread_chat=count_unread_for_admin())


@app.route("/admin/chat/<int:user_id>")
@admin_required
def admin_chat(user_id):
    user = get_user(user_id)
    if not user:
        return "کاربر پیدا نشد", 404
    mark_messages_read(user_id, "admin")
    return render_template("chat.html",
        messages=get_chat_messages(user_id),
        user_id=user_id,
        user=user,
        is_admin=True,
        unread_chat=count_unread_for_admin(),
        unread_dm=0)


@app.route("/admin/chat/<int:user_id>/send", methods=["POST"])
@admin_required
def admin_chat_send(user_id):
    msg = request.form.get("message", "").strip()
    if msg:
        add_chat_message(user_id, "admin", msg)
    return redirect(url_for("admin_chat", user_id=user_id))


# ============ هوش مصنوعی ============
@app.route("/panel/ai")
@user_required
def panel_ai():
    user_id = session["user_id"]
    usage = get_ai_usage(user_id)
    return render_template("ai.html",
        usage=usage,
        user_id=user_id,
        unread_chat=count_unread_for_user(user_id))


def _ask_ai(question, history=None):
    """AI حرفه‌ای با حافظه مکالمه و چند مدل"""
    import requests as req
    from concurrent.futures import ThreadPoolExecutor, as_completed

    history = history or []

    def try_models():
        """امتحان چند مدل موازی"""
        models = ["openai", "gemini", "mistral"]
        results = {}

        def call(model):
            try:
                msgs = [
                    {"role": "system", "content": """تو یه دستیار هوشمند فارسی‌زبان حرفه‌ای هستی. 
قوانین:
- همیشه فارسی جواب بده
- جواب‌های دقیق، مفید و کاربردی بده
- اگه کد خواستن، کد کامل با توضیح بده
- اگه اطلاعات کافی نداری، صادقانه بگو
- لحن دوستانه و حرفه‌ای داشته باش"""}
                ]
                # اضافه کردن تاریخچه (آخرین ۶ پیام)
                for h in history[-6:]:
                    msgs.append(h)
                msgs.append({"role": "user", "content": question})

                r = req.post(
                    "https://text.pollinations.ai/",
                    json={"messages": msgs, "model": model, "private": True},
                    timeout=20
                )
                if r.status_code == 200 and r.text.strip() and len(r.text.strip()) > 5:
                    return r.text.strip()
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(call, m): m for m in models}
            for f in as_completed(futures, timeout=25):
                try:
                    result = f.result()
                    if result:
                        return result
                except Exception:
                    continue
        return None

    result = try_models()

    # fallback: get ساده
    if not result:
        try:
            r = req.get(
                f"https://text.pollinations.ai/{req.utils.quote(question)}?model=flux-realism",
                timeout=15
            )
            if r.status_code == 200 and r.text.strip():
                result = r.text.strip()
        except Exception:
            pass

    return result or "⚠ متأسفم، الان نمی‌تونم جواب بدم. دوباره تلاش کن."


@app.route("/panel/ai/ask", methods=["POST"])
@user_required
def panel_ai_ask():
    user_id = session["user_id"]
    usage = get_ai_usage(user_id)
    limit = 999 if usage["is_premium"] else 10
    if usage["daily_count"] >= limit:
        return jsonify({"status": "error", "message": "سقف سوال روزانه تموم شده. نسخه پرمیوم بخر."})

    question = (request.get_json(silent=True) or {}).get("q", "").strip()
    if not question:
        return jsonify({"status": "error", "message": "سوال خالیه"})

    answer = _ask_ai(question)
    increment_ai_usage(user_id)
    new_usage = get_ai_usage(user_id)
    return jsonify({
        "status": "success",
        "answer": answer,
        "used": new_usage["daily_count"],
        "limit": limit
    })


@app.route("/admin/ai/premium/<int:user_id>", methods=["POST"])
@admin_required
def admin_ai_premium(user_id):
    set_ai_premium(user_id, 30)
    flash(f"پرمیوم ۳۰ روزه برای کاربر {user_id} فعال شد", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


# ============ هوش مصنوعی ادمین ============
@app.route("/admin/ai")
@admin_required
def admin_ai():
    return render_template("ai_admin.html",
        unread_chat=count_unread_for_admin())


@app.route("/admin/ai/ask", methods=["POST"])
@admin_required
def admin_ai_ask():
    question = (request.get_json(silent=True) or {}).get("q", "").strip()
    if not question:
        return jsonify({"status": "error", "message": "سوال خالیه"})
    # ادمین: بدون محدودیت
    answer = _ask_ai(question)
    return jsonify({"status": "success", "answer": answer, "used": 0, "limit": 999})


# ============ پروفایل ============
@app.route("/panel/profile", methods=["GET", "POST"])
@user_required
def panel_profile():
    user_id = session["user_id"]
    user = get_user(user_id)
    message = None
    msg_type = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "username":
            new_username = request.form.get("new_username", "").strip()
            if new_username and new_username != user[1]:
                ok, msg = update_user_username(user_id, new_username)
                if ok:
                    session["user_name"] = new_username
                    user = get_user(user_id)
                    message, msg_type = "نام کاربری بروزرسانی شد", "success"
                else:
                    message, msg_type = msg, "error"

        elif action == "password":
            old_pass = request.form.get("old_password", "")
            new_pass = request.form.get("new_password", "").strip()
            confirm = request.form.get("confirm_password", "").strip()
            if old_pass != user[2]:
                message, msg_type = "رمز فعلی اشتباهه", "error"
            elif not new_pass or len(new_pass) < 4:
                message, msg_type = "رمز جدید باید حداقل ۴ کاراکتر باشه", "error"
            elif new_pass != confirm:
                message, msg_type = "رمز جدید و تکرارش یکی نیستن", "error"
            else:
                update_user_password(user_id, new_pass)
                message, msg_type = "رمز عبور بروزرسانی شد", "success"

        elif action == "info":
            shop = request.form.get("shop_name", "").strip()
            phone = request.form.get("phone", "").strip()
            update_user_shop_name(user_id, shop)
            update_user_phone(user_id, phone)
            user = get_user(user_id)
            message, msg_type = "اطلاعات بروزرسانی شد", "success"

        elif action == "theme":
            theme = request.form.get("theme", "neon")
            premium_themes = ["aurora", "galaxy", "sunset", "forest", "fire", "ice", "cyber", "rose", "midnight", "candy", "emerald", "blood"]
            # چک کن کاربر پرمیوم داره
            prem_status = get_premium_status(user_id)
            if theme in premium_themes and not prem_status["active"]:
                message, msg_type = "این تم مخصوص اعضای پرمیومه", "error"
            else:
                update_user_theme(user_id, theme)
                session["theme"] = theme
                message, msg_type = f"تم به {theme} تغییر کرد", "success"

        elif action == "avatar":
            path = _save_upload(request.files.get("avatar"), "avatar", user_id)
            if path:
                update_user_avatar(user_id, path)
                message, msg_type = "عکس پروفایل تغییر کرد", "success"
            else:
                message, msg_type = "فرمت نامعتبر یا حجم بیش از ۳MB", "error"

        elif action == "bg":
            path = _save_upload(request.files.get("bg"), "bg", user_id)
            if path:
                update_user_bg(user_id, path)
                message, msg_type = "پس‌زمینه تغییر کرد", "success"
            else:
                message, msg_type = "فرمت نامعتبر یا حجم بیش از ۳MB", "error"

    current_theme = get_user_theme(user_id)
    settings = get_user_settings(user_id)
    premium_status = get_premium_status(user_id)
    settings["premium"] = premium_status["active"]
    settings["premium_until"] = premium_status["until"]
    return render_template("profile.html",
        user=user,
        current_theme=current_theme,
        settings=settings,
        message=message,
        msg_type=msg_type,
        is_admin=False,
        unread_chat=count_unread_for_user(user_id))


@app.route("/admin/profile", methods=["GET", "POST"])
@admin_required
def admin_profile():
    message = None
    msg_type = None
    current_theme = session.get("admin_theme", "neon")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "password":
            old_pass = request.form.get("old_password", "")
            new_pass = request.form.get("new_password", "").strip()
            confirm = request.form.get("confirm_password", "").strip()
            if old_pass != ADMIN_PASSWORD:
                message, msg_type = "رمز فعلی اشتباهه", "error"
            elif not new_pass or len(new_pass) < 4:
                message, msg_type = "رمز جدید باید حداقل ۴ کاراکتر باشه", "error"
            elif new_pass != confirm:
                message, msg_type = "رمز جدید و تکرارش یکی نیستن", "error"
            else:
                import re
                with open('config.py', 'r') as f:
                    cfg = f.read()
                cfg = re.sub(r'ADMIN_PASSWORD = ".*?"', f'ADMIN_PASSWORD = "{new_pass}"', cfg)
                with open('config.py', 'w') as f:
                    f.write(cfg)
                message, msg_type = "رمز ادمین بروزرسانی شد. سرور رو ری‌استارت کن", "success"

        elif action == "theme":
            theme = request.form.get("theme", "neon")
            session["admin_theme"] = theme
            current_theme = theme
            message, msg_type = f"تم به {theme} تغییر کرد", "success"

        elif action == "avatar":
            path = _save_upload(request.files.get("avatar"), "admin_avatar", 0)
            if path:
                update_admin_avatar(path)
                message, msg_type = "عکس پروفایل تغییر کرد", "success"
            else:
                message, msg_type = "فرمت نامعتبر یا حجم بیش از ۳MB", "error"

        elif action == "bg":
            path = _save_upload(request.files.get("bg"), "admin_bg", 0)
            if path:
                update_admin_bg(path)
                message, msg_type = "پس‌زمینه تغییر کرد", "success"
            else:
                message, msg_type = "فرمت نامعتبر یا حجم بیش از ۳MB", "error"

    settings = get_admin_settings()
    # ادمین: پرمیوم رایگان همیشه
    settings["premium"] = True
    settings["premium_until"] = "∞"
    return render_template("profile.html",
        user=None,
        admin_user=ADMIN_USERNAME,
        current_theme=current_theme,
        settings=settings,
        message=message,
        msg_type=msg_type,
        is_admin=True,
        unread_chat=count_unread_for_admin())


# ============ چت کاربران ============
@app.route("/panel/users")
@user_required
def panel_users():
    user_id = session["user_id"]
    query = request.args.get("q", "").strip()
    results = []
    if query:
        results = search_users_advanced(query, user_id)
    return render_template("users_chat.html",
        friends=get_friends(user_id),
        incoming=get_incoming_requests(user_id),
        outgoing=get_outgoing_requests(user_id),
        results=results,
        query=query,
        user_id=user_id,
        unread_chat=count_unread_for_user(user_id),
        unread_dm=count_dm_unread(user_id),
        pending_count=count_pending_requests(user_id),
        is_admin=False)


@app.route("/panel/request/send/<int:other_id>", methods=["POST"])
@user_required
def panel_request_send(other_id):
    user_id = session["user_id"]
    ok, msg = send_chat_request(user_id, other_id)
    flash(msg, "success" if ok else "error")
    return redirect(url_for("panel_users"))


@app.route("/panel/request/accept/<int:req_id>", methods=["POST"])
@user_required
def panel_request_accept(req_id):
    accept_request(req_id, session["user_id"])
    flash("درخواست پذیرفته شد ✅", "success")
    return redirect(url_for("panel_users"))


@app.route("/panel/request/reject/<int:req_id>", methods=["POST"])
@user_required
def panel_request_reject(req_id):
    reject_request(req_id, session["user_id"])
    flash("درخواست رد شد", "success")
    return redirect(url_for("panel_users"))


@app.route("/panel/request/delete/<int:req_id>", methods=["POST"])
@user_required
def panel_request_delete(req_id):
    delete_request(req_id, session["user_id"])
    return redirect(url_for("panel_users"))


@app.route("/panel/dm/<int:other_id>", methods=["GET", "POST"])
@user_required
def panel_dm(other_id):
    user_id = session["user_id"]
    if user_id == other_id:
        return redirect(url_for("panel_users"))
    other = get_user(other_id)
    if not other:
        return "کاربر پیدا نشد", 404
    # چک دوست بودن
    if not are_friends(user_id, other_id):
        flash("برای چت باید اول درخواست بدی و پذیرفته بشه", "error")
        return redirect(url_for("panel_users"))

    if request.method == "POST":
        msg = request.form.get("message", "").strip()
        if msg:
            send_dm(user_id, other_id, msg)
        return redirect(url_for("panel_dm", other_id=other_id))

    mark_dm_read(user_id, other_id)
    msgs = get_conversation(user_id, other_id)

    return render_template("dm_chat.html",
        messages=msgs,
        other=other,
        user_id=user_id,
        is_admin=False,
        unread_chat=count_unread_for_user(user_id),
        unread_dm=count_dm_unread(user_id))


# ============ API چت (auto-refresh) ============
@app.route("/api/chat/messages")
def api_chat_messages():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401

    user_id = request.args.get("user_id", type=int)
    after = request.args.get("after", 0, type=int)

    if session.get("is_admin"):
        # ادمین با هر کاربری
        if not user_id:
            return jsonify({"messages": []})
    else:
        # مغازه‌دار فقط با خودش
        user_id = session["user_id"]

    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    c.execute("""SELECT id, sender, message, created_at,
                        reply_to_name, reply_to_text,
                        msg_type, file_path, voice_duration
                 FROM chat_messages
                 WHERE user_id=? AND id > ?
                 ORDER BY id ASC LIMIT 100""", (user_id, after))
    rows = c.fetchall()

    # آواتار ادمین و کاربر
    conn2 = __import__("sqlite3").connect("panel.db")
    c2 = conn2.cursor()
    c2.execute("SELECT avatar_path FROM user_settings WHERE user_id=-1")
    row_adm = c2.fetchone()
    admin_avatar = row_adm[0] if row_adm and row_adm[0] else None
    c2.execute("SELECT avatar_path FROM user_settings WHERE user_id=?", (user_id,))
    row_usr = c2.fetchone()
    user_avatar = row_usr[0] if row_usr and row_usr[0] else None
    conn2.close()

    messages = []
    for r in rows:
        msg_id = r[0]
        c.execute("SELECT emoji, user_id FROM reactions WHERE message_id=?", (msg_id,))
        reacts = c.fetchall()
        reactions = {}
        for emo, uid in reacts:
            if emo not in reactions:
                reactions[emo] = 0
            reactions[emo] += 1
        sender_avatar = admin_avatar if r[1] == "admin" else user_avatar
        messages.append({
            "id": msg_id, "sender": r[1], "text": r[2], "time": r[3][11:16],
            "reply_to": {"name": r[4], "text": r[5]} if r[4] else None,
            "msg_type": r[6] or "text",
            "file_path": r[7],
            "voice_duration": r[8],
            "reactions": reactions,
            "avatar": sender_avatar
        })
    conn.close()

    if session.get("is_admin"):
        mark_messages_read(user_id, "admin")
    else:
        mark_messages_read(user_id, "shopkeeper")

    return jsonify({"messages": messages})


@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401

    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"status": "error", "message": "empty"}), 400

    if session.get("is_admin"):
        user_id = data.get("user_id")
        sender = "admin"
    else:
        user_id = session["user_id"]
        sender = "shopkeeper"

    if not user_id:
        return jsonify({"status": "error"}), 400

    reply_to_id = data.get("reply_to")
    reply_name = None
    reply_text = None
    if reply_to_id:
        try:
            conn = __import__("sqlite3").connect("panel.db")
            c = conn.cursor()
            c.execute("SELECT sender, message FROM chat_messages WHERE id=?", (reply_to_id,))
            row = c.fetchone()
            if row:
                sender_label = "Creator" if row[0] == "admin" else "مغازه‌دار"
                reply_name = sender_label
                reply_text = row[1][:80]
            conn.close()
        except Exception:
            pass

    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    c.execute("""INSERT INTO chat_messages (user_id, sender, message, reply_to_id, reply_to_name, reply_to_text)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (user_id, sender, msg, reply_to_id, reply_name, reply_text))
    new_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "id": new_id})


# ============ API پیشرفته چت ============
@app.route("/api/chat/edit", methods=["POST"])
def api_chat_edit():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401
    data = request.get_json() or {}
    msg_id = data.get("id")
    new_text = data.get("text", "").strip()
    if not msg_id or not new_text:
        return jsonify({"status": "error"}), 400
    is_admin = bool(session.get("is_admin"))
    user_id = None if is_admin else session["user_id"]
    ok = edit_chat_message(msg_id, new_text, user_id, is_admin)
    return jsonify({"status": "success" if ok else "error"})


@app.route("/api/chat/delete", methods=["POST"])
def api_chat_delete():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401
    data = request.get_json() or {}
    msg_id = data.get("id")
    if not msg_id:
        return jsonify({"status": "error"}), 400
    is_admin = bool(session.get("is_admin"))
    user_id = None if is_admin else session["user_id"]
    ok = delete_chat_message(msg_id, user_id, is_admin)
    return jsonify({"status": "success" if ok else "error"})


@app.route("/api/chat/search")
def api_chat_search():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401
    q = request.args.get("q", "").strip()
    user_id = request.args.get("user_id", type=int)
    if not session.get("is_admin"):
        user_id = session["user_id"]
    if not q or not user_id:
        return jsonify({"results": []})
    rows = search_chat_messages(user_id, q)
    return jsonify({"results": [
        {"id": r[0], "sender": r[2], "text": r[3], "time": r[5][11:16]}
        for r in rows
    ]})


@app.route("/api/chat/clear", methods=["POST"])
def api_chat_clear():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not session.get("is_admin"):
        user_id = session["user_id"]
    if not user_id:
        return jsonify({"status": "error"}), 400
    clear_chat(user_id, bool(session.get("is_admin")))
    return jsonify({"status": "success"})


# ============ API نوتیفیکیشن ============
@app.route("/api/notifications")
def api_notifications():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"items": []}), 401
    if session.get("is_admin"):
        return jsonify({"items": []})  # ادمین نوتیف نداره
    user_id = session["user_id"]
    rows = get_notifications(user_id)
    return jsonify({"items": [
        {"id": r[0], "title": r[2], "body": r[3], "read": bool(r[4]), "time": r[5]}
        for r in rows
    ]})


# ============ API آپلود فایل چت ============
CHAT_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "chat")
os.makedirs(CHAT_UPLOAD_DIR, exist_ok=True)

ALLOWED_CHAT_IMG = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_CHAT_AUDIO = {"webm", "ogg", "mp3", "wav", "m4a", "aac"}

@app.route("/api/chat/upload", methods=["POST"])
def api_chat_upload():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401

    if session.get("is_admin"):
        user_id = request.form.get("user_id", type=int)
        sender = "admin"
    else:
        user_id = session["user_id"]
        sender = "shopkeeper"

    if not user_id:
        return jsonify({"status": "error"}), 400

    file = request.files.get("file")
    msg_type = request.form.get("type", "image")

    if not file or not file.filename:
        return jsonify({"status": "error", "message": "فایلی نفرستادی"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if msg_type == "image" and ext not in ALLOWED_CHAT_IMG:
        return jsonify({"status": "error", "message": "فرمت عکس پشتیبانی نمی‌شه"}), 400
    if msg_type == "voice" and ext not in ALLOWED_CHAT_AUDIO:
        return jsonify({"status": "error", "message": "فرمت صدا پشتیبانی نمی‌شه"}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 10 * 1024 * 1024:  # 10MB
        return jsonify({"status": "error", "message": "حجم فایل بیش از ۱۰ مگابایته"}), 400

    fname = f"chat_{msg_type}_{user_id}_{int(time.time())}.{ext}"
    fpath = os.path.join(CHAT_UPLOAD_DIR, fname)
    file.save(fpath)
    rel_path = f"/static/uploads/chat/{fname}"

    # ذخیره در دیتابیس
    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    duration = request.form.get("duration", type=int) or 0
    c.execute("""INSERT INTO chat_messages
                 (user_id, sender, message, msg_type, file_path, voice_duration)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (user_id, sender, "", msg_type, rel_path, duration))
    new_id = c.lastrowid
    conn.commit()
    conn.close()

    # گرفتن آواتار فرستنده
    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    av_id = -1 if sender == "admin" else user_id
    c.execute("SELECT avatar_path FROM user_settings WHERE user_id=?", (av_id,))
    row = c.fetchone()
    avatar = row[0] if row and row[0] else None
    conn.close()

    return jsonify({
        "status": "success", "id": new_id,
        "path": rel_path, "type": msg_type, "duration": duration,
        "avatar": avatar
    })


@app.route("/api/chat/react", methods=["POST"])
def api_chat_react():
    if not (session.get("is_admin") or session.get("user_id")):
        return jsonify({"status": "error"}), 401
    data = request.get_json() or {}
    msg_id = data.get("id")
    emoji = data.get("emoji", "").strip()
    if not msg_id or not emoji:
        return jsonify({"status": "error"}), 400

    user_id = -1 if session.get("is_admin") else session["user_id"]

    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    # اگه کاربر قبلاً واکنش داده بود، حذفش کن
    c.execute("SELECT emoji FROM reactions WHERE message_id=? AND user_id=?", (msg_id, user_id))
    existing = c.fetchone()
    if existing and existing[0] == emoji:
        c.execute("DELETE FROM reactions WHERE message_id=? AND user_id=?", (msg_id, user_id))
        action = "removed"
    elif existing:
        c.execute("UPDATE reactions SET emoji=? WHERE message_id=? AND user_id=?", (emoji, msg_id, user_id))
        action = "updated"
    else:
        c.execute("INSERT INTO reactions (message_id, user_id, emoji) VALUES (?, ?, ?)", (msg_id, user_id, emoji))
        action = "added"
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "action": action})


# ============ API پرمیوم ادمین ============
@app.route("/admin/user/<int:user_id>/premium/add", methods=["POST"])
@admin_required
def admin_premium_add(user_id):
    days = int(request.form.get("days", 30) or 30)
    until = extend_premium(user_id, days)
    flash(f"پرمیوم {days} روزه فعال شد (تا {until})", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


@app.route("/admin/user/<int:user_id>/premium/revoke", methods=["POST"])
@admin_required
def admin_premium_revoke(user_id):
    revoke_premium(user_id)
    flash("پرمیوم لغو شد", "success")
    return redirect(url_for("admin_user_detail", user_id=user_id))


# ============ API همه پیام‌ها ============
@app.route("/api/all-messages")
@user_required
def api_all_messages():
    user_id = session["user_id"]
    filter_type = request.args.get("filter", "all")
    conversations = get_all_conversations(user_id)

    if filter_type == "admin":
        conversations = [c for c in conversations if c["type"] == "admin"]
    elif filter_type == "personal":
        conversations = [c for c in conversations if c["type"] == "personal"]

    return jsonify({"conversations": conversations})


@app.route("/api/message-counts")
@user_required
def api_message_counts():
    user_id = session["user_id"]
    return jsonify(get_conversation_counts(user_id))


# ============ API Trigger ============
@app.route("/api/trigger", methods=["POST"])
def trigger():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()
    location = data.get("location", "unknown")
    user_id = data.get("user_id")
    if not phone:
        return jsonify({"status": "error", "message": "phone لازم است"}), 400
    if user_id and not is_user_active(user_id):
        return jsonify({"status": "error", "message": "کاربر غیرفعال"}), 403
    message = "منتظر دیدار دوباره شما هستیم"
    result = send_sms(phone, message)
    log_sms(phone, message, result.get("status", "unknown"), user_id=user_id)
    log_event(phone, location, user_id=user_id)
    return jsonify(result)



# ============ مخاطبین ============
@app.route("/panel/contacts")
@user_required
def panel_contacts():
    uid = session["user_id"]
    s = request.args.get("q", "").strip()
    g = request.args.get("group", "").strip()
    return render_template("contacts.html",
        contacts=get_user_contacts(uid, s, g),
        groups=get_contact_groups(uid),
        total=count_contacts(uid),
        search=s, current_group=g,
        unread_chat=count_unread_for_user(uid))

@app.route("/panel/contacts/add", methods=["POST"])
@user_required
def panel_contacts_add():
    uid = session["user_id"]
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    grp = request.form.get("group", "معمولی").strip() or "معمولی"
    notes = request.form.get("notes", "").strip()
    if not name or not phone:
        flash("نام و شماره الزامی است", "error")
    elif not (phone.startswith("09") and len(phone) == 11):
        flash("شماره معتبر نیست", "error")
    else:
        add_contact(uid, name, phone, grp, notes)
        flash("مخاطب اضافه شد", "success")
    return redirect(url_for("panel_contacts"))

@app.route("/panel/contacts/edit/<int:cid>", methods=["POST"])
@user_required
def panel_contacts_edit(cid):
    update_contact(cid, session["user_id"],
        request.form.get("name", "").strip(),
        request.form.get("phone", "").strip(),
        request.form.get("group", "معمولی").strip() or "معمولی",
        request.form.get("notes", "").strip())
    flash("بروزرسانی شد", "success")
    return redirect(url_for("panel_contacts"))

@app.route("/panel/contacts/delete/<int:cid>", methods=["POST"])
@user_required
def panel_contacts_delete(cid):
    delete_contact(cid, session["user_id"])
    flash("حذف شد", "success")
    return redirect(url_for("panel_contacts"))

@app.route("/panel/contacts/import", methods=["POST"])
@user_required
def panel_contacts_import():
    uid = session["user_id"]
    txt = request.form.get("contacts_text", "").strip()
    default_group = request.form.get("default_group", "معمولی").strip() or "معمولی"
    
    if not txt:
        flash("متنی وارد نشده", "error")
        return redirect(url_for("panel_contacts"))
    
    items = []
    errors = []
    line_num = 0
    
    for line in txt.split("\n"):
        line_num += 1
        line = line.strip()
        if not line:
            continue
        
        # پشتیبانی از جداکننده‌های مختلف: , ; | tab
        parts = []
        for sep in [",", ";", "|", "	"]:
            if sep in line:
                parts = [p.strip() for p in line.split(sep)]
                break
        
        if not parts:
            # فقط شماره
            if line.startswith("09") and len(line) == 11:
                items.append({"name": "مشتری " + line[-4:], "phone": line, "group": default_group})
            else:
                errors.append(f"خط {line_num}: نامعتبر")
            continue
        
        # اگر فقط یه بخش
        if len(parts) == 1:
            if parts[0].startswith("09") and len(parts[0]) == 11:
                items.append({"name": "مشتری " + parts[0][-4:], "phone": parts[0], "group": default_group})
            else:
                errors.append(f"خط {line_num}: نامعتبر")
        
        # دو بخش یا بیشتر
        elif len(parts) >= 2:
            name = parts[0]
            phone = parts[1]
            group = parts[2] if len(parts) > 2 else default_group
            
            # نرمال‌سازی شماره
            phone = phone.replace(" ", "").replace("-", "")
            
            # چک شماره
            if phone.startswith("+98"):
                phone = "0" + phone[3:]
            elif phone.startswith("98") and len(phone) == 12:
                phone = "0" + phone[2:]
            elif phone.startswith("9") and len(phone) == 10:
                phone = "0" + phone
            
            if not (phone.startswith("09") and len(phone) == 11):
                errors.append(f"خط {line_num}: شماره نامعتبر ({phone})")
                continue
            
            if not name:
                name = "مشتری " + phone[-4:]
            
            items.append({"name": name, "phone": phone, "group": group})
    
    if not items:
        msg = "هیچ مخاطب معتبری پیدا نشد"
        if errors:
            msg += " — " + "; ".join(errors[:3])
        flash(msg, "error")
        return redirect(url_for("panel_contacts"))
    
    added = import_contacts(uid, items)
    
    success_msg = f"✅ {added} مخاطب اضافه شد"
    if errors:
        success_msg += f" ({len(errors)} خطا)"
    flash(success_msg, "success")
    return redirect(url_for("panel_contacts"))


@app.route("/admin/contacts/<int:target_uid>/import", methods=["POST"])
@admin_required
def admin_contacts_import(target_uid):
    txt = request.form.get("contacts_text", "").strip()
    default_group = request.form.get("default_group", "معمولی").strip() or "معمولی"
    
    if not txt:
        flash("متنی وارد نشده", "error")
        return redirect(url_for("admin_user_contacts", user_id=target_uid))
    
    items = []
    errors = []
    line_num = 0
    
    for line in txt.split("\n"):
        line_num += 1
        line = line.strip()
        if not line:
            continue
        
        parts = []
        for sep in [",", ";", "|", "	"]:
            if sep in line:
                parts = [p.strip() for p in line.split(sep)]
                break
        
        if not parts:
            if line.startswith("09") and len(line) == 11:
                items.append({"name": "مشتری " + line[-4:], "phone": line, "group": default_group})
            continue
        
        if len(parts) >= 2:
            name = parts[0] or "مشتری " + parts[1][-4:]
            phone = parts[1].replace(" ", "").replace("-", "")
            group = parts[2] if len(parts) > 2 else default_group
            
            if phone.startswith("+98"):
                phone = "0" + phone[3:]
            elif phone.startswith("9") and len(phone) == 10:
                phone = "0" + phone
            
            if phone.startswith("09") and len(phone) == 11:
                items.append({"name": name, "phone": phone, "group": group})
    
    if items:
        added = import_contacts(target_uid, items)
        flash(f"✅ {added} مخاطب اضافه شد", "success")
    else:
        flash("هیچ مخاطب معتبری پیدا نشد", "error")
    
    return redirect(url_for("admin_user_contacts", user_id=target_uid))

@app.route("/admin/contacts")
@admin_required
def admin_contacts():
    raw = get_all_users()
    users = [{"id": u[0], "username": u[1], "shop_name": u[3],
              "contacts_count": count_contacts(u[0])} for u in raw]
    return render_template("admin_contacts.html", users=users,
        total_users=len(users), unread_chat=count_unread_for_admin())

@app.route("/admin/contacts/<int:uid>")
@admin_required
def admin_user_contacts(uid):
    user = get_user(uid)
    if not user: return "not found", 404
    s = request.args.get("q", "").strip()
    g = request.args.get("group", "").strip()
    return render_template("contacts.html",
        contacts=get_user_contacts(uid, s, g),
        groups=get_contact_groups(uid), total=count_contacts(uid),
        search=s, current_group=g,
        admin_view=True, user=user, user_id=uid,
        unread_chat=count_unread_for_admin())


# ============ قالب‌ها ============
@app.route("/panel/templates")
@user_required
def panel_templates():
    uid = session["user_id"]
    cat = request.args.get("cat", "").strip()
    return render_template("templates.html",
        templates=get_user_templates(uid, cat),
        categories=get_template_categories(uid),
        total=count_templates(uid), current_cat=cat,
        unread_chat=count_unread_for_user(uid))

@app.route("/panel/templates/add", methods=["POST"])
@user_required
def panel_templates_add():
    uid = session["user_id"]
    t = request.form.get("title", "").strip()
    b = request.form.get("body", "").strip()
    c = request.form.get("category", "عمومی").strip() or "عمومی"
    if not t or not b:
        flash("عنوان و متن الزامی است", "error")
    else:
        add_template(uid, t, b, c)
        flash("قالب ذخیره شد", "success")
    return redirect(url_for("panel_templates"))

@app.route("/panel/templates/edit/<int:tid>", methods=["POST"])
@user_required
def panel_templates_edit(tid):
    update_template(tid, session["user_id"],
        request.form.get("title", "").strip(),
        request.form.get("body", "").strip(),
        request.form.get("category", "عمومی").strip() or "عمومی")
    flash("بروزرسانی شد", "success")
    return redirect(url_for("panel_templates"))

@app.route("/panel/templates/delete/<int:tid>", methods=["POST"])
@user_required
def panel_templates_delete(tid):
    delete_template(tid, session["user_id"])
    flash("حذف شد", "success")
    return redirect(url_for("panel_templates"))

@app.route("/api/templates/list")
@user_required
def api_templates_list():
    rows = get_user_templates(session["user_id"])
    return jsonify({"templates": [
        {"id": r[0], "title": r[2], "body": r[3], "category": r[4], "use_count": r[5]}
        for r in rows]})

@app.route("/api/templates/use/<int:tid>", methods=["POST"])
@user_required
def api_templates_use(tid):
    increment_template_use(tid, session["user_id"])
    return jsonify({"status": "success"})

@app.route("/admin/templates")
@admin_required
def admin_templates_list():
    raw = get_all_users()
    users = [{"id": u[0], "username": u[1], "shop_name": u[3],
              "templates_count": count_templates(u[0])} for u in raw]
    return render_template("admin_templates_list.html", users=users,
        total_users=len(users), unread_chat=count_unread_for_admin())

@app.route("/admin/templates/<int:uid>")
@admin_required
def admin_user_templates(uid):
    user = get_user(uid)
    if not user: return "not found", 404
    cat = request.args.get("cat", "").strip()
    return render_template("templates.html",
        templates=get_user_templates(uid, cat),
        categories=get_template_categories(uid),
        total=count_templates(uid), current_cat=cat,
        admin_view=True, user=user, user_id=uid,
        unread_chat=count_unread_for_admin())


# ============ بکاپ ============
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup(backup_type="manual"):
    from datetime import datetime
    import shutil
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"panel_{backup_type}_{ts}.db"
        fpath = os.path.join(BACKUP_DIR, fname)
        shutil.copy2("panel.db", fpath)
        size = os.path.getsize(fpath)
        log_backup(fname, size, backup_type, "success")
        return True, fname, size
    except Exception as e:
        log_backup("", 0, backup_type, f"error: {str(e)[:50]}")
        return False, str(e), 0

@app.route("/admin/backups")
@admin_required
def admin_backups():
    all_b = get_backup_history(100)
    auto_b = [b for b in all_b if b[4] == 'auto']
    manual_b = [b for b in all_b if b[4] != 'auto']
    return render_template("admin_backups.html",
        backups=all_b, auto_backups=auto_b, manual_backups=manual_b,
        auto_count=len(auto_b), manual_count=len(manual_b),
        total=count_backups(), unread_chat=count_unread_for_admin())

@app.route("/admin/backups/create", methods=["POST"])
@admin_required
def admin_backups_create():
    ok, fname, size = create_backup("manual")
    if ok:
        flash(f"بکاپ ساخته شد ({size//1024} KB)", "success")
    else:
        flash(f"خطا: {fname}", "error")
    return redirect(url_for("admin_backups"))

@app.route("/admin/backups/download/<int:bid>")
@admin_required
def admin_backups_download(bid):
    from flask import send_file
    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM backups WHERE id=?", (bid,))
    row = c.fetchone()
    conn.close()
    if not row: return "not found", 404
    fp = os.path.join(BACKUP_DIR, row[0])
    if not os.path.exists(fp): return "not found", 404
    return send_file(fp, as_attachment=True, download_name=row[0])

@app.route("/admin/backups/delete/<int:bid>", methods=["POST"])
@admin_required
def admin_backups_delete(bid):
    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM backups WHERE id=?", (bid,))
    row = c.fetchone()
    conn.close()
    if row:
        fp = os.path.join(BACKUP_DIR, row[0])
        if os.path.exists(fp): os.remove(fp)
    delete_backup_record(bid)
    flash("حذف شد", "success")
    return redirect(url_for("admin_backups"))

@app.route("/admin/backups/restore/<int:bid>", methods=["POST"])
@admin_required
def admin_backups_restore(bid):
    import shutil
    conn = __import__("sqlite3").connect("panel.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM backups WHERE id=?", (bid,))
    row = c.fetchone()
    conn.close()
    if not row:
        flash("بکاپ پیدا نشد", "error")
        return redirect(url_for("admin_backups"))
    fp = os.path.join(BACKUP_DIR, row[0])
    if not os.path.exists(fp):
        flash("فایل پیدا نشد", "error")
        return redirect(url_for("admin_backups"))
    try:
        create_backup("before_restore")
        shutil.copy2(fp, "panel.db")
        flash("بازیابی شد. سرور رو ری‌استارت کن.", "success")
    except Exception as e:
        flash(f"خطا: {str(e)[:80]}", "error")
    return redirect(url_for("admin_backups"))


# ============ آمار ============
@app.route("/admin/stats")
@admin_required
def admin_stats():
    return render_template("admin_stats.html", unread_chat=count_unread_for_admin())

@app.route("/api/stats/data")
@admin_required
def api_stats_data():
    return jsonify({
        "daily": get_sms_stats_by_day(7),
        "hourly": get_sms_stats_by_hour(),
        "top_users": get_top_users(5),
        "statuses": get_status_stats(),
        "revenue": get_monthly_revenue()})



# ============ نوتیفیکیشن ============
@app.route("/notifications")
@user_required
def notif_page_user():
    uid = session["user_id"]
    mark_all_read(uid)
    return render_template("notifications.html",
        notifications=get_user_notifications(uid),
        is_admin=False, unread_chat=0)

@app.route("/admin/notifications")
@admin_required
def notif_page_admin():
    mark_all_read(-1)
    return render_template("notifications.html",
        notifications=get_user_notifications(-1),
        is_admin=True, unread_chat=count_unread_for_admin())

@app.route("/api/notif/count")
def notif_api_count():
    if session.get("is_admin"):
        uid = -1
    elif session.get("user_id"):
        uid = session["user_id"]
    else:
        return jsonify({"count": 0})
    return jsonify({"count": count_unread_notifications(uid)})

@app.route("/api/notif/delete/<int:nid>", methods=["POST"])
def notif_api_delete(nid):
    if session.get("is_admin"):
        delete_notification(nid, -1)
    elif session.get("user_id"):
        delete_notification(nid, session["user_id"])
    return jsonify({"status": "success"})

@app.route("/api/notif/clear", methods=["POST"])
def notif_api_clear():
    if session.get("is_admin"):
        clear_user_notifications(-1)
    elif session.get("user_id"):
        clear_user_notifications(session["user_id"])
    return jsonify({"status": "success"})

@app.route("/admin/notif/send", methods=["POST"])
@admin_required
def notif_api_send():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    icon = request.form.get("icon", "🔔").strip() or "🔔"
    link = request.form.get("link", "").strip()
    target = request.form.get("target", "all")
    if not title or not body:
        flash("عنوان و متن الزامی است", "error")
    else:
        if target == "all":
            n = notify_all_users(title, body, icon, link)
            flash(f"ارسال شد به {n} کاربر", "success")
        else:
            try:
                create_notification(int(target), title, body, icon, link)
                flash("ارسال شد", "success")
            except Exception:
                flash("کاربر نامعتبر", "error")
    return redirect(url_for("notif_page_admin"))



# ============ QR کد ============
import io
import qrcode
from flask import Response

@app.route("/panel/qr")
@user_required
def qr_my_page():
    uid = session["user_id"]
    user = get_user(uid)
    if not user:
        return redirect(url_for("panel_login"))
    return render_template("qr_page.html",
        user=user, is_admin=False,
        scans=get_qr_scans(uid, 20),
        scan_count=count_qr_scans(uid),
        unread_chat=count_unread_for_user(uid))

@app.route("/admin/qr/<int:uid>")
@admin_required
def qr_admin_view(uid):
    user = get_user(uid)
    if not user:
        return "not found", 404
    return render_template("qr_page.html",
        user=user, is_admin=True,
        scans=get_qr_scans(uid, 20),
        scan_count=count_qr_scans(uid),
        unread_chat=count_unread_for_admin())

@app.route("/qr/<username>.png")
def qr_image(username):
    user = get_user_by_username(username)
    if not user:
        return "", 404
    base_url = request.url_root.rstrip("/")
    register_url = base_url + "/register/" + username
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(register_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

@app.route("/register/<username>", methods=["GET", "POST"])
def public_register(username):
    # اطلاعات مغازه‌دار
    user = get_user_by_username(username)
    if not user:
        return render_template("public_register.html",
            shop=None, msg="این مغازه وجود ندارد", success=False)

    msg = None
    success = False

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        if not phone or not (phone.startswith("09") and len(phone) == 11):
            msg = "شماره موبایل معتبر نیست"
        elif not name:
            msg = "نام الزامی است"
        else:
            try:
                # اضافه به مخاطبین مغازه‌دار
                add_contact(
                    user_id=user[0],
                    name=name,
                    phone=phone,
                    group_name="ثبت‌نام QR",
                    note=f"از طریق لینک عمومی"
                )
                msg = "✅ ثبت‌نام موفق! از این پس پیامک‌های این مغازه به شما ارسال می‌شود."
                success = True
            except Exception as e:
                msg = f"خطا: {e}"

    return render_template("public_register.html",
        shop=user, msg=msg, success=success)


# ========== 🎯 روت جدید: ثبت‌نام با کد دعوت ==========
@app.route("/register/ref/<code>", methods=["GET", "POST"])
def public_register_ref(code):
    referrer_id = find_user_by_ref_code(code)
    if not referrer_id:
        return render_template("public_register.html",
            shop=None, msg="کد دعوت نامعتبر است", success=False)

    # اگه کاربر لاگین کرده و خودش صاحب کده → بفرست به داشبورد
    if session.get("user_id") == referrer_id:
        flash("خودت نمی‌تونی خودت رو دعوت کنی!", "warning")
        return redirect("/panel/referrals")

    referrer = get_user(referrer_id)
    if not referrer:
        return render_template("public_register.html",
            shop=None, msg="دعوت‌کننده پیدا نشد", success=False)

    msg = None
    success = False

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        shop_name = (request.form.get("shop_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        # اعتبارسنجی
        if not username or not password:
            msg = "نام کاربری و رمز الزامی است"
        elif len(password) < 6:
            msg = "رمز باید حداقل ۶ کاراکتر باشد"
        elif get_user_by_username(username):
            msg = "این نام کاربری قبلاً گرفته شده"
        else:
            try:
                # ساخت کاربر جدید
                new_uid = add_user(
                    username=username,
                    password=password,
                    shop_name=shop_name or username,
                    phone=phone,
                    days=30,
                    sms_limit=100
                )
                if new_uid:
                    # 🎁 پردازش ارجاع
                    ok = process_referral(referrer_id, new_uid, code)
                    if ok:
                        msg = f"🎉 ثبت‌نام موفق! ۲۵,۰۰۰ ریال + ۲۵ امتیاز هدیه گرفتید."
                    else:
                        msg = "✅ ثبت‌نام موفق شد."
                    success = True
                else:
                    msg = "خطا در ساخت حساب"
            except Exception as e:
                msg = f"خطا: {e}"

    # رندر تمپلیت مخصوص
    return render_template("public_register_ref.html",
        referrer=referrer, code=code, msg=msg, success=success)



# ===== اتصال کیف پول =====
try:
    from wallet_routes import wallet_bp
    app.register_blueprint(wallet_bp)
    print('✅ wallet_bp registered')
except Exception as _e:
    print('❌ wallet_bp error:', _e)


# ===== اتصال درگاه پرداخت =====
try:
    from payment_routes import payment_bp
    app.register_blueprint(payment_bp)
    print('✅ payment_bp registered')
except Exception as _e:
    print('❌ payment_bp error:', _e)


# ===== اتصال تیکت پشتیبانی =====
try:
    from ticket_routes import ticket_bp
    app.register_blueprint(ticket_bp)
    print('✅ ticket_bp registered')
except Exception as _e:
    print('❌ ticket_bp error:', _e)


# ===== اتصال وفاداری =====
try:
    from loyalty_routes import loyalty_bp
    app.register_blueprint(loyalty_bp)
    print('✅ loyalty_bp registered')
except Exception as _e:
    print('❌ loyalty_bp error:', _e)


# ===== اتصال ارجاع =====
try:
    from referral_routes import referral_bp
    app.register_blueprint(referral_bp)
    print('✅ referral_bp registered')
except Exception as _e:
    print('❌ referral_bp error:', _e)


# ===== اتصال گزارش‌ها =====
try:
    from report_routes import report_bp
    from product_routes import product_bp
    from sales_routes import sales_bp
    from channel_send_routes import channel_send_bp
    from schedule_routes import schedule_bp
    
    app.register_blueprint(report_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(channel_send_bp)
    app.register_blueprint(schedule_bp)
    
    print('✅ report_bp registered')
except Exception as _e:
    print('❌ report_bp error:', _e)

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    if not session.get("is_admin"):
        return redirect("/admin/login")

    confirm = (request.form.get("confirm_name") or "").strip()
    u = get_user(user_id)
    if not u:
        return redirect("/admin/dashboard")

    if confirm != u[1]:
        return redirect(f"/admin/user/{user_id}")

    import sqlite3
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()

    # حذف تیکت‌ها و پاسخ‌هاشون
    try:
        c.execute("SELECT id FROM tickets WHERE user_id=?", (user_id,))
        for (tid,) in c.fetchall():
            c.execute("DELETE FROM ticket_replies WHERE ticket_id=?", (tid,))
        c.execute("DELETE FROM tickets WHERE user_id=?", (user_id,))
    except: pass

    # حذف ارجاع‌ها
    try:
        c.execute("DELETE FROM referrals WHERE referrer_id=? OR referred_id=?", (user_id, user_id))
        c.execute("DELETE FROM referral_codes WHERE user_id=?", (user_id,))
    except: pass

    # بقیه جدول‌ها با user_id
    for tbl in ['wallets','transactions','payments','notifications','loyalty',
                'loyalty_log','sent_sms','contacts','sms_templates','schedules',
                'chat_messages','direct_messages','chat_requests','user_settings',
                'reactions','ai_usage','qr_scans','login_logs','login_attempts','events']:
        try:
            c.execute(f"DELETE FROM {tbl} WHERE user_id=?", (user_id,))
        except: pass

    # حذف خود کاربر (نه ادمین id=1)
    c.execute("DELETE FROM users WHERE id=? AND id != 1", (user_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")



# ===== اتصال 2FA =====
try:
    from twofa_routes import twofa_bp
    app.register_blueprint(twofa_bp)
    print('✅ twofa_bp registered')
except Exception as _e:
    print('❌ twofa_bp error:', _e)


# ===== اتصال تست پیامک =====
try:
    from test_routes import test_bp
    app.register_blueprint(test_bp)
    print('✅ test_bp registered')
except Exception as _e:
    print('❌ test_bp error:', _e)


# ===== اتصال پاسخ خودکار =====
try:
    from autoreply_routes import autoreply_bp
    app.register_blueprint(autoreply_bp)
    print('✅ autoreply_bp registered')
except Exception as _e:
    print('❌ autoreply_bp error:', _e)


# ===== اتصال AI Manager =====
try:
    from aimanager_routes import aimanager_bp
    app.register_blueprint(aimanager_bp)
    print('✅ aimanager_bp registered')
except Exception as _e:
    print('❌ aimanager_bp error:', _e)


# ===== اتصال Broadcast =====
try:
    from broadcast_routes import broadcast_bp
    app.register_blueprint(broadcast_bp)
    print('✅ broadcast_bp registered')
except Exception as _e:
    print('❌ broadcast_bp error:', _e)


# ===== Bot Ads =====
try:
    from botads_routes import botads_bp
    app.register_blueprint(botads_bp)
    print('✅ botads_bp registered')
except Exception as _e:
    print('❌ botads_bp error:', _e)


# ===== Posters =====
try:
    from poster_routes import poster_bp
    app.register_blueprint(poster_bp)
    print('✅ poster_bp registered')
except Exception as _e:
    print('❌ poster_bp error:', _e)


# ===== Admin Bots =====
try:
    from admin_bots_routes import admin_bots_bp
    app.register_blueprint(admin_bots_bp)
    print('admin_bots_bp OK')
except Exception as e:
    print('admin_bots_bp error:', e)









try:
    from bot_members_routes import members_bp
    app.register_blueprint(members_bp)
    print('members_bp OK')
except Exception as e:
    print('members_bp err:', e)


try:
    from url_admin_routes import url_admin_bp
    app.register_blueprint(url_admin_bp)
    print('url_admin_bp OK')
except Exception as e:
    print('url_admin_bp err:', e)


try:
    from customer_panel import customer_panel_bp
    app.register_blueprint(customer_panel_bp)
    print("customer_panel OK")
except Exception as e:
    print("customer_panel err:", e)


try:
    from customer_features_routes import feat_bp
    app.register_blueprint(feat_bp)
    print("customer_features OK")
except Exception as e:
    print("customer_features err:", e)

# 🔄 Keep-alive (فقط روی Render)
try:
    import os as _os
    if _os.environ.get('RENDER') or _os.environ.get('RENDER_EXTERNAL_URL'):
        from keep_alive import start as _ka_start
        _ka_start()
except Exception as _e:
    pass


# ============ ADMIN ADD USER (SHOP) ============
@app.route("/admin/add-user", methods=["POST"])
@admin_required
def admin_add_user_new():
    from database import add_user  # تابعی که مغازه جدید رو توی دیتابیس ذخیره می‌کنه
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    shop_name = request.form.get("shop_name", "").strip()
    phone = request.form.get("phone", "").strip()
    
    if username and password and shop_name:
        try:
            # فراخوانی تابع دیتابیس (اگه تابع add_user وجود نداشته باشه، اینجا خطا میده)
            add_user(username, password, shop_name, phone)
            flash("✅ مغازه جدید با موفقیت اضافه شد", "success")
        except Exception as e:
            flash(f"❌ خطا در ذخیره‌سازی: {str(e)}", "error")
    else:
        flash("❌ لطفا فیلدهای الزامی را پر کنید", "error")
        
    return redirect("/admin/dashboard")



# ============ ADMIN: MANAGE SHOPS ============
@app.route("/admin/shops", methods=["GET", "POST"])
@admin_required
def admin_shops():
    from database import add_user_full, delete_user, get_all_shop_owners
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            shop_name = request.form.get("shop_name", "").strip()
            phone = request.form.get("phone", "").strip()
            days = request.form.get("days", "30")
            
            if username and password and shop_name:
                try:
                    days = int(days)
                    success, err = add_user_full(username, password, shop_name, phone, days)
                    if success:
                        flash("✅ مغازه‌دار با موفقیت اضافه شد", "success")
                    else:
                        flash(f"❌ خطا: {err}", "error")
                except:
                    flash("❌ تعداد روز نامعتبر است", "error")
            else:
                flash("❌ فیلدهای الزامی را پر کنید", "error")
                
        elif action == "delete":
            uid = request.form.get("uid")
            if uid:
                delete_user(uid)
                flash("✅ مغازه‌دار حذف شد", "success")
                
        return redirect("/admin/shops")

    shops = get_all_shop_owners()
    return render_template("admin_shops.html", shops=shops, current_settings={})

if __name__ == "__main__":
    init_db()
    init_contacts_table()
    init_templates_table()
    init_backup_table()
    app.run(host="0.0.0.0", port=8080, debug=False)



