from flask import Blueprint, render_template, request, redirect, session, flash
from database import (get_loyalty, add_loyalty_points, redeem_points, notify_reward_ready,
                      get_weekly_points, get_weekly_labels,
                      get_top_users_by_points, get_my_rank, get_top_sms_senders,
                      get_upcoming_birthdays, give_birthday_gift, get_birthday_history,
                      get_loyalty_log, get_all_loyalty, set_user_birthday,
                      count_tier_users, check_birthday_bonus,
                      loyalty_multiplier, is_double_points_day,
                      get_user, get_user_settings)

loyalty_bp = Blueprint('loyalty', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


@loyalty_bp.route('/panel/loyalty')
def panel_loyalty():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    check_birthday_bonus(uid)
    l = get_loyalty(uid)
    logs = get_loyalty_log(uid, 30)
    user = get_user(uid)
    shop = user[3] if user and len(user) > 3 else ''

    # progress bar (به سمت ۱۰۰ تا)
    next_reward = 100 - (l['points'] % 100)
    progress_pct = (l['points'] % 100)

    # 📊 داده نمودار
    weekly = get_weekly_points(uid)
    chart_labels = get_weekly_labels()
    chart_values = list(weekly.values())

    return render_template('panel_loyalty.html',
        l=l, logs=logs, shop=shop,
        next_reward=next_reward,
        progress_pct=progress_pct,
        multiplier=loyalty_multiplier(),
        double_day=is_double_points_day(),
        chart_labels=chart_labels,
        chart_values=chart_values,
        current_settings=_cs(uid))


@loyalty_bp.route('/panel/loyalty/redeem', methods=['POST'])
def panel_redeem():
    uid = _uid()
    if not uid: return redirect('/panel/login')
    ok, msg = redeem_points(uid, 100, 10)
    return redirect('/panel/loyalty?redeemed=1')


@loyalty_bp.route('/panel/loyalty/birthday', methods=['POST'])
def panel_birthday():
    uid = _uid()
    if not uid: return redirect('/panel/login')
    # 🔒 اگه قبلاً ثبت شده، اجازه تغییر نده
    current = get_loyalty(uid)
    if current.get('birthday'):
        flash('⚠️ تاریخ تولد قبلاً ثبت شده و قابل تغییر نیست', 'error')
        return redirect('/panel/loyalty')
    bd = (request.form.get('birthday') or '').strip()
    if bd:
        set_user_birthday(uid, bd)
    return redirect('/panel/loyalty')


@loyalty_bp.route('/admin/loyalty')
def admin_loyalty():
    if not _is_admin(): return redirect('/admin/login')
    rows = get_all_loyalty()
    tiers = count_tier_users()
    return render_template('admin_loyalty.html',
        rows=rows, tiers=tiers,
        current_settings=_cs())


@loyalty_bp.route('/admin/loyalty/<int:uid>/add', methods=['POST'])
def admin_add_points(uid):
    if not _is_admin(): return redirect('/admin/login')
    try: n = int(request.form.get('points', 0))
    except: n = 0
    note = (request.form.get('note') or 'تنظیم ادمین').strip()
    if request.form.get('neg'):
        n = -abs(n)
    if n != 0:
        add_loyalty_points(uid, n, note)
    return redirect('/admin/loyalty')


@loyalty_bp.route('/panel/leaderboard')
def panel_leaderboard():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    period = request.args.get('period', 'week')
    if period not in ('week', 'month', 'all'):
        period = 'week'

    top = get_top_users_by_points(10, period)
    sms_top = get_top_sms_senders(10, 30)
    my_rank, my_pts, total_users = get_my_rank(uid, period)

    return render_template('panel_leaderboard.html',
        top=top, sms_top=sms_top,
        period=period,
        my_rank=my_rank, my_pts=my_pts, total_users=total_users,
        current_settings=_cs(uid))


@loyalty_bp.route('/admin/birthdays')
def admin_birthdays():
    if not _is_admin(): return redirect('/admin/login')
    bds = get_upcoming_birthdays(7)
    history = get_birthday_history(30)
    today_bds = [b for b in bds if b['is_today']]
    return render_template('admin_birthdays.html',
        birthdays=bds, today=today_bds, history=history,
        current_settings=_cs())


@loyalty_bp.route('/admin/birthdays/<int:uid>/gift', methods=['POST'])
def admin_birthday_gift(uid):
    if not _is_admin(): return redirect('/admin/login')
    try:
        cash = int(request.form.get('cash', 100000))
        pts = int(request.form.get('points', 100))
    except:
        cash, pts = 100000, 100
    give_birthday_gift(uid, cash, pts)
    return redirect('/admin/birthdays')
