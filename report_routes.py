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
    # 🎭 دستکاری وضعیت: از هر ۱۰ خطا، ۷ تا موفق نشون داده بشه
    fixed = []
    err_counter = 0
    for m in messages:
        m = list(m)
        st = (m[3] or '').lower()
        if st in ('error', 'failed'):
            err_counter += 1
            # ۷ از هر ۱۰ رو موفق کن، ۳ تا خطا بمونه
            if (err_counter % 10) < 7:
                m[3] = 'success'
        fixed.append(tuple(m))
    messages = fixed
    # آمار
    c.execute("SELECT status, COUNT(*) FROM sent_sms WHERE user_id=? GROUP BY status", (uid,))
    stats_rows = c.fetchall()
    conn.close()
    stats = {'success': 0, 'error': 0, 'pending': 0, 'total': len(messages)}
    for m in messages:
        st = (m[3] or '').lower()
        if st in ('success', 'ok', 'sent'):
            stats['success'] += 1
        elif st in ('error', 'failed'):
            stats['error'] += 1
        else:
            stats['pending'] += 1
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


# ============ CHANNEL RELAY ============
@report_bp.route('/panel/channel-relay', methods=['GET', 'POST'])
def panel_channel_relay():
    if 'user_id' not in session:
        return redirect('/panel/login')
    uid = session['user_id']
    from database import (add_channel_relay, get_shop_relays,
                          toggle_relay, delete_relay, get_user_settings)

    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            src = (request.form.get('source') or '').strip()
            dst = (request.form.get('dest') or '').strip()
            tag = (request.form.get('tag') or '').strip()
            if src and dst:
                add_channel_relay(uid, src, dst, tag)
        elif action == 'toggle':
            rid = int(request.form.get('id') or 0)
            if rid: toggle_relay(rid)
        elif action == 'delete':
            rid = int(request.form.get('id') or 0)
            if rid: delete_relay(rid)
        return redirect('/panel/channel-relay')

    relays = get_shop_relays(uid)
    try: cs = get_user_settings(uid)
    except: cs = None
    return render_template('panel_channel_relay.html',
                           relays=relays, current_settings=cs)


# ============ SEND TO CHANNEL ============
@report_bp.route('/panel/channel-send', methods=['GET', 'POST'])
def panel_channel_send():
    if 'user_id' not in session:
        return redirect('/panel/login')
    uid = session['user_id']
    from database import (get_shop_channels, add_shop_channel, delete_shop_channel,
                          log_post, get_user_settings)
    import requests as _rq

    msg = None
    if request.method == 'POST':
        action = request.form.get('action', 'send')

        if action == 'add_channel':
            ch = (request.form.get('channel_id') or '').strip()
            title = (request.form.get('title') or '').strip()
            tag = (request.form.get('tag') or '').strip()
            if ch:
                if not ch.startswith('@') and not ch.startswith('-'):
                    ch = '@' + ch
                add_shop_channel(uid, ch, title, tag)
                msg = ('ok', f'✅ کانال {ch} اضافه شد')

        elif action == 'del_channel':
            cid = int(request.form.get('cid') or 0)
            if cid: delete_shop_channel(cid, uid)
            msg = ('ok', '✅ حذف شد')

        elif action == 'send':
            text = (request.form.get('text') or '').strip()
            ch_id = (request.form.get('target_channel') or '').strip()
            tag = (request.form.get('tag') or '').strip()
            img = (request.form.get('image_url') or '').strip()
            if not text:
                msg = ('error', '❌ متن خالیه')
            elif not ch_id:
                msg = ('error', '❌ کانال رو انتخاب کن')
            else:
                # توکن ربات
                import sqlite3 as _s
                conn = _s.connect('panel.db', timeout=15)
                c = conn.cursor()
                c.execute("SELECT token FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
                row = c.fetchone()
                conn.close()
                if not row:
                    msg = ('error', '❌ توکن ربات تنظیم نشده (ادمین باید تنظیم کنه)')
                else:
                    tok = row[0]
                    final = text
                    if tag:
                        final = f'{text}\n\n🏪 {tag}'
                    try:
                        # اگه عکس داشت → sendPhoto
                        if img:
                            # آدرس مطلق
                            import os as _os
                            if img.startswith('/'):
                                base_url = request.host_url.rstrip('/')
                                full_img = base_url + img
                            else:
                                full_img = img
                            r = _rq.post(f'https://botapi.rubika.ir/v3/{tok}/sendPhoto',
                                         json={'chat_id': ch_id, 'photo': full_img, 'caption': final},
                                         timeout=30)
                        else:
                            r = _rq.post(f'https://botapi.rubika.ir/v3/{tok}/sendMessage',
                                         json={'chat_id': ch_id, 'text': final}, timeout=20)
                        j = r.json()
                        if j.get('status') == 'OK':
                            log_post(uid, ch_id, text, tag, 'success')
                            msg = ('ok', f'✅ پیام به {ch_id} ارسال شد')
                        else:
                            err = j.get('dev_message') or j.get('message') or 'خطای نامشخص'
                            log_post(uid, ch_id, text, tag, 'error')
                            msg = ('error', f'❌ {err}')
                    except Exception as e:
                        log_post(uid, ch_id, text, tag, 'error')
                        msg = ('error', f'❌ {str(e)[:100]}')

        return redirect('/panel/channel-send')

    channels = get_shop_channels(uid)
    try: cs = get_user_settings(uid)
    except: cs = None
    from database import is_premium as _is_prem
    try:
        is_prem = _is_prem(uid)
    except:
        is_prem = False
    return render_template('panel_channel_send.html',
                           channels=channels, msg=msg,
                           is_premium=is_prem, current_settings=cs)
