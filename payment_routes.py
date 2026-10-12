import json
import urllib.request
from flask import Blueprint, render_template, request, redirect, session
from database import (get_wallet, charge_wallet, get_user,
                      create_payment, set_payment_authority,
                      get_payment_by_authority, get_payment,
                      mark_payment_verified, mark_payment_failed,
                      get_setting, set_setting, get_user_payments,
                      get_user_settings, get_all_users)

payment_bp = Blueprint('payment', __name__)

ZP_REQUEST = "https://payment.zarinpal.com/pg/v4/payment/request.json"
ZP_VERIFY  = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
ZP_START   = "https://payment.zarinpal.com/pg/StartPay/"


def _post(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _uid():
    return session.get('user_id')


def _is_admin():
    return bool(session.get('is_admin'))


def _base_url():
    # اگه توی تنظیمات ست شده بود، ازون استفاده کن
    custom = get_setting('public_base_url', '').strip()
    if custom:
        return custom.rstrip('/')
    return request.host_url.rstrip('/')


def _test_mode():
    return get_setting('payment_test_mode', '1') == '1'


def _merchant():
    return get_setting('zarinpal_merchant_id', '').strip()


# ========== صفحه شارژ ==========
@payment_bp.route('/panel/wallet/charge', methods=['GET'])
def charge_page():
    uid = _uid()
    if not uid:
        return redirect('/panel/login')
    try: cs = get_user_settings(uid)
    except: cs = None
    return render_template('wallet_charge.html',
        balance=get_wallet(uid),
        current_settings=cs,
        test_mode=_test_mode(),
        has_merchant=bool(_merchant()))


# ========== شروع پرداخت ==========
@payment_bp.route('/panel/wallet/charge', methods=['POST'])
def charge_start():
    uid = _uid()
    if not uid:
        return redirect('/panel/login')

    try:
        amount = int(request.form.get('amount', 0))
    except:
        amount = 0

    if amount < 1000:
        return render_template('payment_result.html',
            ok=False, title='مبلغ نامعتبر',
            msg='حداقل مبلغ شارژ ۱٬۰۰۰ ریال است.',
            current_settings=None)

    # ===== حالت تست =====
    if _test_mode() or not _merchant():
        # بدون درگاه، مستقیم شارژ کن
        charge_wallet(uid, amount, 'شارژ تست (بدون درگاه)')
        pid = create_payment(uid, amount, 'TEST-' + str(uid))
        mark_payment_verified(pid, 'TEST-REF')
        return render_template('payment_result.html',
            ok=True, title='شارژ موفق (تست)',
            msg=f'مبلغ {amount:,} ریال به کیف پول شما اضافه شد.',
            current_settings=None, amount=amount, ref_id='TEST')

    # ===== درگاه واقعی =====
    pid = create_payment(uid, amount, '')
    callback = _base_url() + '/payment/callback'

    try:
        resp = _post(ZP_REQUEST, {
            "merchant_id": _merchant(),
            "amount": amount,
            "callback_url": callback,
            "description": f"شارژ کیف پول - کاربر {uid}"
        })
    except Exception as e:
        mark_payment_failed(pid)
        return render_template('payment_result.html',
            ok=False, title='خطا در اتصال',
            msg=f'ارتباط با درگاه برقرار نشد: {e}',
            current_settings=None)

    if resp.get('data') and resp['data'].get('authority'):
        auth = resp['data']['authority']
        set_payment_authority(pid, auth)
        return redirect(ZP_START + auth)
    else:
        mark_payment_failed(pid)
        err = resp.get('errors', {})
        return render_template('payment_result.html',
            ok=False, title='خطای درگاه',
            msg=f"کد خطا: {err.get('code','?')} — {err.get('message','نامشخص')}",
            current_settings=None)


# ========== کال‌بک زرین‌پال ==========
@payment_bp.route('/payment/callback', methods=['GET'])
def callback():
    status = request.args.get('Status', '')
    authority = request.args.get('Authority', '')

    if not authority:
        return render_template('payment_result.html',
            ok=False, title='اطلاعات ناقص',
            msg='Authority از درگاه دریافت نشد.', current_settings=None)

    pay = get_payment_by_authority(authority)
    if not pay:
        return render_template('payment_result.html',
            ok=False, title='پرداخت پیدا نشد',
            msg='رکورد پرداخت در سیستم نیست.', current_settings=None)

    pid, uid, amount = pay[0], pay[1], pay[2]

    if status != 'OK':
        mark_payment_failed(pid)
        return render_template('payment_result.html',
            ok=False, title='پرداخت لغو شد',
            msg='شما پرداخت را لغو کردید یا ناموفق بود.', current_settings=None)

    # verify
    try:
        resp = _post(ZP_VERIFY, {
            "merchant_id": _merchant(),
            "amount": amount,
            "authority": authority
        })
    except Exception as e:
        return render_template('payment_result.html',
            ok=False, title='خطای verify',
            msg=f'خطا در تأیید پرداخت: {e}', current_settings=None)

    data = resp.get('data') or {}
    code = data.get('code', -1)
    ref_id = data.get('ref_id', '')

    if code in (100, 101):
        mark_payment_verified(pid, ref_id)
        charge_wallet(uid, amount, f'شارژ آنلاین (کد رهگیری: {ref_id})')
        try:
            from database import notify_wallet_charge
            notify_wallet_charge(uid, amount, 'درگاه آنلاین')
        except Exception:
            pass
        return render_template('payment_result.html',
            ok=True, title='پرداخت موفق ✅',
            msg=f'مبلغ {amount:,} ریال به کیف پول شما اضافه شد.',
            current_settings=None, amount=amount, ref_id=ref_id)
    else:
        mark_payment_failed(pid)
        err = resp.get('errors') or {}
        return render_template('payment_result.html',
            ok=False, title='پرداخت تأیید نشد',
            msg=f"کد: {code} — {err.get('message','')}",
            current_settings=None)


# ========== تنظیمات ادمین ==========
@payment_bp.route('/admin/payment', methods=['GET', 'POST'])
def admin_payment():
    if not _is_admin():
        return redirect('/admin/login')

    saved = False
    if request.method == 'POST':
        set_setting('zarinpal_merchant_id', request.form.get('merchant', '').strip())
        set_setting('payment_test_mode', '1' if request.form.get('test_mode') else '0')
        set_setting('public_base_url', request.form.get('base_url', '').strip())
        saved = True

    return render_template('admin_payment.html',
        merchant=_merchant(),
        test_mode=_test_mode(),
        base_url=get_setting('public_base_url', ''),
        detected_base=request.host_url.rstrip('/'),
        saved=saved)


@payment_bp.route('/admin/payments')
def admin_payments_list():
    if not _is_admin():
        return redirect('/admin/login')
    import sqlite3
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.user_id, u.username, p.amount, p.status, p.ref_id, p.created_at
        FROM payments p LEFT JOIN users u ON u.id = p.user_id
        ORDER BY p.id DESC LIMIT 200
    """)
    rows = c.fetchall()
    conn.close()
    return render_template('admin_payments.html', payments=rows)
