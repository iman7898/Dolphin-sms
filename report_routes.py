from flask import Blueprint, render_template, request, redirect, session
from database import (
    get_user_sms_history, count_user_sms, count_user_sms_by_status,
    get_user_sms_daily, get_user_premium_history, get_user_payments_history,
    get_transactions, get_wallet,
    get_total_revenue, get_total_revenue_by_period, get_daily_revenue,
    get_revenue_by_user, get_daily_sms_all, get_admin_overview,
    get_top_paying_users, get_user_settings, get_user
)

report_bp = Blueprint('report', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


# ========== گزارش مغازه‌دار ==========
@report_bp.route('/panel/reports')
def panel_reports():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    period = request.args.get('period', 'all')
    if period not in ('today', 'week', 'month', 'all'):
        period = 'all'
    phone = (request.args.get('phone') or '').strip()

    sms_list = get_user_sms_history(uid, 200, phone, period)
    sms_count = count_user_sms(uid, period)
    sms_ok = count_user_sms_by_status(uid, 'success', period)
    sms_fail = sms_count - sms_ok

    transactions = get_transactions(uid, 100)
    premiums = get_user_premium_history(uid, 50)
    payments = get_user_payments_history(uid, 50)

    daily = get_user_sms_daily(uid, 7)
    chart_labels = list(daily.keys())
    chart_values = list(daily.values())

    user = get_user(uid)
    shop = user[3] if user and len(user) > 3 else ''

    return render_template('panel_reports.html',
        sms_list=sms_list,
        sms_count=sms_count,
        sms_ok=sms_ok,
        sms_fail=sms_fail,
        transactions=transactions,
        premiums=premiums,
        payments=payments,
        balance=get_wallet(uid),
        period=period,
        phone=phone,
        shop=shop,
        chart_labels=chart_labels,
        chart_values=chart_values,
        current_settings=_cs(uid))


# ========== گزارش ادمین ==========
@report_bp.route('/admin/reports')
def admin_reports():
    if not _is_admin(): return redirect('/admin/login')

    overview = get_admin_overview()
    total_rev = get_total_revenue()
    rev_today = get_total_revenue_by_period('today')
    rev_week = get_total_revenue_by_period('week')
    rev_month = get_total_revenue_by_period('month')

    daily_rev = get_daily_revenue(30)
    rev_labels = list(daily_rev.keys())
    rev_values = list(daily_rev.values())

    daily_sms = get_daily_sms_all(30)
    sms_labels = list(daily_sms.keys())
    sms_values = list(daily_sms.values())

    by_user = get_revenue_by_user(50)
    top_payers = get_top_paying_users(10)

    return render_template('admin_reports.html',
        overview=overview,
        total_rev=total_rev,
        rev_today=rev_today,
        rev_week=rev_week,
        rev_month=rev_month,
        rev_labels=rev_labels, rev_values=rev_values,
        sms_labels=sms_labels, sms_values=sms_values,
        by_user=by_user,
        top_payers=top_payers,
        current_settings=_cs())


# ============ گزارش پیام‌ها (لیست کامل) ============
@report_bp.route('/panel/messages')
def panel_messages():
    if 'user_id' not in session:
        return redirect('/panel/login')
    uid = session['user_id']
    from database import get_user_sms_history
    import sqlite3 as _s
    conn = _s.connect('panel.db', timeout=15)
    c = conn.cursor()
    c.execute("""SELECT id, phone, message, status, created_at
                 FROM sent_sms WHERE user_id=?
                 ORDER BY id DESC LIMIT 300""", (uid,))
    messages = c.fetchall()
    # آمار
    c.execute("SELECT status, COUNT(*) FROM sent_sms WHERE user_id=? GROUP BY status", (uid,))
    stats_rows = c.fetchall()
    conn.close()
    stats = {'success': 0, 'error': 0, 'pending': 0, 'total': len(messages)}
    for st, cnt in stats_rows:
        st = (st or '').lower()
        if st in ('success', 'ok', 'sent'):
            stats['success'] += cnt
        elif st in ('error', 'failed'):
            stats['error'] += cnt
        else:
            stats['pending'] += cnt
    from database import get_user_settings
    try: cs = get_user_settings(uid)
    except: cs = None
    return render_template('panel_messages.html',
                           messages=messages, stats=stats,
                           current_settings=cs)


@report_bp.route('/panel/messages/clear', methods=['POST'])
def panel_messages_clear():
    if 'user_id' not in session:
        return redirect('/panel/login')
    uid = session['user_id']
    import sqlite3 as _s
    conn = _s.connect('panel.db', timeout=15)
    c = conn.cursor()
    c.execute("DELETE FROM sent_sms WHERE user_id=? AND status IN ('error','failed')", (uid,))
    conn.commit(); conn.close()
    return redirect('/panel/messages')
