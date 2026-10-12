from flask import Blueprint, render_template, request, redirect, session, jsonify
from database import (add_auto_reply, get_user_auto_replies, get_auto_reply,
                      update_auto_reply, delete_auto_reply, toggle_auto_reply,
                      find_matching_rule, increment_auto_reply_hit,
                      log_incoming_sms, get_user_incoming_sms,
                      count_auto_replies, count_incoming_today,
                      get_user_settings, get_user_by_username)

autoreply_bp = Blueprint('autoreply', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


# ========== پنل مغازه‌دار ==========
@autoreply_bp.route('/panel/auto-reply', methods=['GET', 'POST'])
def panel_auto_reply():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    edit_id = request.args.get('edit')
    editing = None
    if edit_id:
        try:
            r = get_auto_reply(int(edit_id))
            if r and r[1] == uid:
                editing = r
        except:
            pass

    if request.method == 'POST':
        action = request.form.get('action')
        keyword = (request.form.get('keyword') or '').strip()
        response = (request.form.get('response') or '').strip()
        mtype = request.form.get('match_type') or 'contains'

        if action == 'add' and keyword and response:
            add_auto_reply(uid, keyword, response, mtype)
        elif action == 'edit':
            rid = request.form.get('id')
            if rid and keyword and response:
                try:
                    r = get_auto_reply(int(rid))
                    if r and r[1] == uid:
                        update_auto_reply(int(rid), keyword, response, mtype)
                except:
                    pass
        return redirect('/panel/auto-reply')

    rules = get_user_auto_replies(uid)
    incoming = get_user_incoming_sms(uid, 50)
    return render_template('panel_auto_reply.html',
        rules=rules, editing=editing,
        active_count=count_auto_replies(uid),
        incoming_today=count_incoming_today(uid),
        incoming=incoming,
        current_settings=_cs(uid))


@autoreply_bp.route('/panel/auto-reply/<int:rid>/delete', methods=['POST'])
def panel_auto_reply_delete(rid):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    r = get_auto_reply(rid)
    if r and r[1] == uid:
        delete_auto_reply(rid)
    return redirect('/panel/auto-reply')


@autoreply_bp.route('/panel/auto-reply/<int:rid>/toggle', methods=['POST'])
def panel_auto_reply_toggle(rid):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    r = get_auto_reply(rid)
    if r and r[1] == uid:
        toggle_auto_reply(rid)
    return redirect('/panel/auto-reply')


# ========== وب‌هوک کاوه‌نگار (پیام‌های ورودی) ==========
@autoreply_bp.route('/webhook/kavenegar/<username>', methods=['GET', 'POST'])
def kavenegar_webhook(username):
    """
    کاوه‌نگار این URL رو صدا می‌زنه وقتی پیامکی به خط ما بیاد.
    پارامترها: from, message, ... (بسته به تنظیمات)
    """
    user = get_user_by_username(username)
    if not user:
        return jsonify({'ok': False, 'error': 'user not found'}), 404

    uid = user[0]
    sender = request.values.get('from') or request.values.get('sender') or ''
    msg = request.values.get('message') or request.values.get('text') or ''

    if not msg:
        return jsonify({'ok': True, 'note': 'empty'})

    # پیدا کردن قاعده
    match = find_matching_rule(uid, msg)
    reply_sent = ''
    matched_rule_id = None

    if match:
        matched_rule_id, response_text = match
        try:
            from adapters.kavenegar_adapter import send_sms
            r = send_sms(sender, response_text)
            if r.get('status') == 'success':
                reply_sent = response_text
            increment_auto_reply_hit(matched_rule_id)
        except Exception:
            pass

    log_incoming_sms(uid, sender, msg, matched_rule_id, reply_sent)
    return jsonify({'ok': True, 'matched': bool(match)})
