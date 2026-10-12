from flask import Blueprint, render_template, request, redirect, session, flash
from database import (add_bot_ad, get_ads_history, get_user_bot_members,
                      count_bot_members_for_user, update_ad_status,
                      get_user_settings, get_ai_config)

botads_bp = Blueprint('botads', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


# ========== ادمین سایت ==========
@botads_bp.route('/admin/bot-ads', methods=['GET', 'POST'])
def admin_bot_ads():
    if not _is_admin(): return redirect('/admin/login')

    if request.method == 'POST':
        msg = (request.form.get('message') or '').strip()
        target_user = request.form.get('target_user') or '1'
        if msg:
            try:
                target_user_id = int(target_user)
            except:
                target_user_id = 1
            add_bot_ad(target_user_id, msg)
            flash('✅ تبلیغ به صف اضافه شد', 'ok')
        return redirect('/admin/bot-ads')

    history = get_ads_history(None, 50)
    total_members = count_bot_members_for_user(1)

    # لیست همه کاربرانی که ربات دارن
    import sqlite3
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("""SELECT user_id, bot_token, messenger FROM ai_channel_config
                 WHERE bot_token != '' AND bot_token IS NOT NULL""")
    bot_users = c.fetchall()
    conn.close()

    return render_template('admin_bot_ads.html',
        history=history,
        total_members=total_members,
        bot_users=bot_users,
        current_settings=_cs())


# ========== مغازه‌دار ==========
@botads_bp.route('/panel/bot-ads', methods=['GET', 'POST'])
def panel_bot_ads():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    if request.method == 'POST':
        msg = (request.form.get('message') or '').strip()
        if msg:
            add_bot_ad(uid, msg)
            flash('✅ تبلیغ به صف اضافه شد', 'ok')
        return redirect('/panel/bot-ads')

    history = get_ads_history(uid, 50)
    total = count_bot_members_for_user(uid)
    return render_template('panel_bot_ads.html',
        history=history, total_members=total,
        current_settings=_cs(uid))
