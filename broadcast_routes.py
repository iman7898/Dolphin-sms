from flask import Blueprint, render_template, request, redirect, session, flash, jsonify
from database import (get_bot_members, count_bot_members, get_bot_token,
                      add_force_join, get_force_joins, toggle_force_join,
                      delete_force_join, log_broadcast, get_broadcast_history,
                      get_user_settings, get_contacts, add_bot_member)
from bot_adapters.rubika import RubikaBot
from bot_adapters.telegram import TelegramBot
from bot_adapters.bale import BaleBot
import time

broadcast_bp = Blueprint('broadcast', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


def _get_bot(messenger, token):
    if not token: return None
    if messenger == 'rubika': return RubikaBot(token)
    if messenger == 'telegram': return TelegramBot(token)
    if messenger == 'bale': return BaleBot(token)
    return None


# ========== Broadcast ==========
@broadcast_bp.route('/panel/broadcast')
def panel_broadcast():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    creds = get_bot_token(uid) or {}
    msgr = creds.get('messenger', 'rubika')
    total = count_bot_members(uid, msgr)
    history = get_broadcast_history(uid, 20)

    return render_template('panel_broadcast.html',
        total=total, messenger=msgr, history=history,
        current_settings=_cs(uid))


@broadcast_bp.route('/panel/broadcast/send', methods=['POST'])
def panel_broadcast_send():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    message = (request.form.get('message') or '').strip()
    if not message:
        flash('متن پیام خالی است', 'error')
        return redirect('/panel/broadcast')

    creds = get_bot_token(uid) or {}
    msgr = creds.get('messenger', 'rubika')
    token = creds.get('token', '')

    if not token:
        flash('توکن ربات تنظیم نشده', 'error')
        return redirect('/panel/broadcast')

    bot = _get_bot(msgr, token)
    if not bot:
        flash('آداپتر پیدا نشد', 'error')
        return redirect('/panel/broadcast')

    members = get_bot_members(uid, msgr, 1000)
    sent = 0
    failed = 0
    for m in members:
        chat_id = m[0]
        try:
            r = bot.send_message(chat_id, message)
            if r.get('ok') is not False and r.get('status') != 'error':
                sent += 1
            else:
                failed += 1
        except:
            failed += 1
        time.sleep(0.05)  # جلوگیری از بلاک

    log_broadcast(uid, message, sent, failed)
    flash(f'✅ ارسال شد: {sent} | ناموفق: {failed}', 'ok')
    return redirect('/panel/broadcast')


# ========== Force-Join ==========
@broadcast_bp.route('/panel/force-join', methods=['GET', 'POST'])
def panel_force_join():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    if request.method == 'POST':
        channel_id = (request.form.get('channel_id') or '').strip()
        channel_username = (request.form.get('channel_username') or '').strip()
        channel_link = (request.form.get('channel_link') or '').strip()
        if channel_id and channel_link:
            creds = get_bot_token(uid) or {}
            msgr = creds.get('messenger', 'rubika')
            add_force_join(uid, msgr, channel_id, channel_username, channel_link)
            flash('✅ کانال اضافه شد', 'ok')
        return redirect('/panel/force-join')

    creds = get_bot_token(uid) or {}
    msgr = creds.get('messenger', 'rubika')
    channels = get_force_joins(uid, msgr)
    return render_template('panel_force_join.html',
        channels=channels, messenger=msgr,
        current_settings=_cs(uid))


@broadcast_bp.route('/panel/force-join/<int:fid>/toggle', methods=['POST'])
def panel_fj_toggle(fid):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    toggle_force_join(fid)
    return redirect('/panel/force-join')


@broadcast_bp.route('/panel/force-join/<int:fid>/delete', methods=['POST'])
def panel_fj_delete(fid):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    delete_force_join(fid)
    return redirect('/panel/force-join')


# ========== اتصال به مخاطبین ==========
@broadcast_bp.route('/panel/invite-by-sms', methods=['GET', 'POST'])
def panel_invite_by_sms():
    """ارسال پیامک دعوت به مخاطبین با لینک کانال"""
    uid = _uid()
    if not uid: return redirect('/panel/login')

    from adapters.mci_adapter import send_sms
    from database import get_contacts, log_sms

    result = None
    if request.method == 'POST':
        channel_link = (request.form.get('channel_link') or '').strip()
        template = (request.form.get('template') or '').strip()
        group = (request.form.get('group') or '').strip()

        if not channel_link or not template:
            flash('لینک و متن پیامک الزامی است', 'error')
            return redirect('/panel/invite-by-sms')

        try:
            contacts = get_contacts(uid)
            if group:
                contacts = [c for c in contacts if len(c) > 4 and c[4] == group]
        except:
            contacts = []

        sent = 0
        failed = 0
        for c in contacts:
            phone = c[2] if len(c) > 2 else ''
            name = c[1] if len(c) > 1 else ''
            if not phone: continue

            msg = template.replace('{name}', name).replace('{link}', channel_link)
            try:
                r = send_sms(phone, msg)
                if r.get('status') == 'success':
                    sent += 1
                    try: log_sms(phone, msg, 'success', user_id=uid)
                    except: pass
                else:
                    failed += 1
            except:
                failed += 1

        result = {'sent': sent, 'failed': failed, 'total': len(contacts)}
        flash(f'✅ ارسال شد: {sent} | ناموفق: {failed}', 'ok')

    try:
        contacts = get_contacts(uid)
        groups = list(set([c[4] for c in contacts if len(c) > 4 and c[4]]))
    except:
        contacts = []
        groups = []

    return render_template('panel_invite_by_sms.html',
        result=result, groups=groups, contacts_count=len(contacts),
        current_settings=_cs(uid))


# ========== وب‌هوک ربات (پردازش پیام‌های ورودی به ربات) ==========
@broadcast_bp.route('/bot/webhook/<int:user_id>/<messenger>', methods=['POST'])
def bot_webhook(user_id, messenger):
    """
    این روت رو به وب‌هوک ربات وصل کن.
    هر پیامی که کاربر به ربات بفرسته اینجا میاد.
    """
    data = request.get_json() or request.form.to_dict()
    # ذخیره به عنوان ممبر اگه جدید بود
    chat_id = data.get('chat_id') or data.get('from', {}).get('id') or ''
    username = data.get('username') or data.get('from', {}).get('username') or ''
    first_name = data.get('first_name') or data.get('from', {}).get('first_name') or ''

    if chat_id:
        add_bot_member(user_id, messenger, chat_id, username, first_name)

    return jsonify({'ok': True})
