from flask import Blueprint, render_template, request, redirect, session
from database import (get_or_create_referral_code, get_user_referrals,
                      count_referrals, get_top_referrers, find_user_by_ref_code,
                      get_user_settings)

referral_bp = Blueprint('referral', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


@referral_bp.route('/panel/referrals')
def panel_referrals():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    code = get_or_create_referral_code(uid)
    base = request.host_url.rstrip('/')
    link = f'{base}/register/ref/{code}' if code else ''
    refs = get_user_referrals(uid)
    count = count_referrals(uid)

    # پاداش پیش‌فرض از ثابت‌های database
    from database import (REFERRER_BONUS_POINTS, REFERRER_BONUS_CASH,
                          REFERRED_BONUS_POINTS, REFERRED_BONUS_CASH)

    return render_template('panel_referrals.html',
        code=code or '—',
        link=link,
        refs=refs,
        count=count,
        bonus_pts=REFERRER_BONUS_POINTS,
        bonus_cash=REFERRER_BONUS_CASH,
        ref_pts=REFERRED_BONUS_POINTS,
        ref_cash=REFERRED_BONUS_CASH,
        current_settings=_cs(uid))


@referral_bp.route('/admin/referrals')
def admin_referrals():
    if not _is_admin(): return redirect('/admin/login')
    top = get_top_referrers(20)
    return render_template('admin_referrals.html',
        top=top,
        current_settings=_cs())
