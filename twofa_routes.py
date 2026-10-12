from flask import Blueprint, render_template, request, redirect, session, flash
from database import (get_2fa, set_2fa_enabled, generate_2fa_code,
                      verify_2fa_code, get_user, get_user_settings,
                      log_login)

twofa_bp = Blueprint('twofa', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


def _send_2fa_sms(phone, code):
    """ارسال پیامک کد — با try/except چون ممکنه خط نداشته باشه"""
    try:
        from adapters.mci_adapter import send_sms
        msg = f'کد ورود شما: {code}\nاعتبار: ۵ دقیقه'
        result = send_sms(phone, msg)
        return result
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# ===== تنظیمات 2FA (پروفایل) =====
@twofa_bp.route('/panel/2fa', methods=['GET', 'POST'])
def panel_2fa():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    f = get_2fa(uid)
    msg = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'enable':
            phone = (request.form.get('phone') or '').strip()
            if not phone or not (phone.startswith('09') and len(phone) == 11):
                msg = ('error', 'شماره موبایل معتبر نیست (09xxxxxxxxx)')
            else:
                set_2fa_enabled(uid, True, phone)
                msg = ('ok', '✅ ورود دو مرحله‌ای فعال شد')
                f = get_2fa(uid)
        elif action == 'disable':
            set_2fa_enabled(uid, False, '')
            msg = ('ok', '✅ ورود دو مرحله‌ای غیرفعال شد')
            f = get_2fa(uid)
        elif action == 'test':
            phone = (request.form.get('phone') or f['phone'] or '').strip()
            code = generate_2fa_code(uid)
            r = _send_2fa_sms(phone, code)
            if r and r.get('status') == 'success':
                msg = ('ok', '📱 کد تست ارسال شد')
            else:
                msg = ('error', f"⚠️ پیامک ارسال نشد — کد تست: {code}")

    return render_template('panel_2fa.html',
        f=f, msg=msg, current_settings=_cs(uid))


# ===== تأیید کد موقع ورود =====
@twofa_bp.route('/panel/2fa/verify', methods=['GET', 'POST'])
def panel_2fa_verify():
    uid = session.get('pending_2fa_uid')
    if not uid:
        return redirect('/panel/login')

    error = None
    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        ok, m = verify_2fa_code(uid, code)
        if ok:
            # تایید موفق — session اصلی رو ست کن
            session['user_id'] = uid
            session['user_name'] = session.get('pending_2fa_name', '')
            session.pop('pending_2fa_uid', None)
            session.pop('pending_2fa_name', None)
            return redirect('/panel/dashboard')
        else:
            error = m

    # اطلاعات کاربر
    u = get_user(uid)
    phone = ''
    test_code = None
    try:
        f = get_2fa(uid)
        phone = f['phone'] or ''
        # اگه کد تازه هست (یعنی پیامک نرفته یا کاربر درخواست کرده)، نمایش بده
        # این خط رو برای حالت تست نگه دار
        test_code = f.get('code') or None
    except Exception:
        pass
    masked = phone[:4] + '****' + phone[-2:] if len(phone) >= 6 else phone

    return render_template('panel_2fa_verify.html',
        error=error, masked=masked, test_code=test_code, current_settings=None)


# ===== درخواست کد جدید =====
@twofa_bp.route('/panel/2fa/resend', methods=['POST'])
def panel_2fa_resend():
    uid = session.get('pending_2fa_uid')
    if not uid:
        return redirect('/panel/login')
    f = get_2fa(uid)
    code = generate_2fa_code(uid)
    r = _send_2fa_sms(f['phone'], code)
    # اگه پیامک نرفت، کد رو نشون بده (تست)
    if not (r and r.get('status') == 'success'):
        flash(f'⚠️ پیامک ارسال نشد — کد: {code}', 'error')
    else:
        flash('📱 کد جدید ارسال شد', 'ok')
    return redirect('/panel/2fa/verify')


# ===== غیرفعال‌سازی توسط ادمین =====
@twofa_bp.route('/admin/2fa/<int:user_id>/disable', methods=['POST'])
def admin_disable_2fa(user_id):
    if not _is_admin(): return redirect('/admin/login')
    set_2fa_enabled(user_id, False, '')
    return redirect(f'/admin/user/{user_id}')
