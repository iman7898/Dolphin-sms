from flask import Blueprint, render_template, request, session, redirect
from adapters.kavenegar_adapter import send_otp, send_sms, check_balance
from database import get_user_settings

test_bp = Blueprint('test_sms', __name__)


def _is_admin():
    return bool(session.get('is_admin'))


def _cs():
    try: return get_user_settings(1)
    except: return None


@test_bp.route('/admin/test-sms', methods=['GET', 'POST'])
def admin_test_sms():
    if not _is_admin():
        return redirect('/admin/login')

    result = None
    method = 'otp'
    if request.method == 'POST':
        phone = (request.form.get('phone') or '').strip()
        code = (request.form.get('code') or '123456').strip()
        method = request.form.get('method', 'otp')

        if not phone or not (phone.startswith('09') and len(phone) == 11):
            result = {'status': 'error', 'message': 'شماره معتبر نیست (09xxxxxxxxx)'}
        else:
            if method == 'otp':
                result = send_otp(phone, code)
            else:
                msg = (request.form.get('message') or 'تست پنل پیامکی ✅').strip()
                result = send_sms(phone, msg)

    balance = check_balance()
    return render_template('admin_test_sms.html',
        result=result,
        method=method,
        balance=balance,
        current_settings=_cs())
