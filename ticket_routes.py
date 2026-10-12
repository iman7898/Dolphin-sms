from flask import Blueprint, render_template, request, redirect, session
from database import (create_ticket, get_user_tickets, get_all_tickets, get_ticket,
                      get_ticket_replies, add_ticket_reply, update_ticket_status,
                      count_open_tickets, count_user_unread_tickets, get_user_settings,
                      notify_ticket_reply, notify_ticket_new, get_user)

ticket_bp = Blueprint('ticket', __name__)


def _uid():
    return session.get('user_id')


def _is_admin():
    return bool(session.get('is_admin'))


def _cs(uid=None):
    try:
        return get_user_settings(uid or 1)
    except Exception:
        return None


# ========== پنل مغازه‌دار ==========
@ticket_bp.route('/panel/tickets')
def panel_tickets():
    uid = _uid()
    if not uid:
        return redirect('/panel/login')
    tks = get_user_tickets(uid, 100)
    return render_template('panel_tickets.html',
        tickets=tks,
        current_settings=_cs(uid),
        unread=count_user_unread_tickets(uid))


@ticket_bp.route('/panel/tickets/new', methods=['GET', 'POST'])
def panel_tickets_new():
    uid = _uid()
    if not uid:
        return redirect('/panel/login')

    if request.method == 'POST':
        subject = (request.form.get('subject') or '').strip()
        message = (request.form.get('message') or '').strip()
        priority = request.form.get('priority') or 'normal'
        if subject and message:
            tid = create_ticket(uid, subject, message, priority)
            # 🔔 نوتیف به ادمین
            try:
                u = get_user(uid)
                uname = u[1] if u else f'کاربر {uid}'
                notify_ticket_new(tid, subject, uname)
            except Exception:
                pass
            return redirect(f'/panel/tickets/{tid}')

    return render_template('panel_ticket_new.html',
        current_settings=_cs(uid))


@ticket_bp.route('/panel/tickets/<int:tid>', methods=['GET', 'POST'])
def panel_ticket_view(tid):
    uid = _uid()
    if not uid:
        return redirect('/panel/login')

    t = get_ticket(tid)
    if not t or t[1] != uid:
        return redirect('/panel/tickets')

    if request.method == 'POST':
        msg = (request.form.get('message') or '').strip()
        if msg:
            add_ticket_reply(tid, 'user', msg)
            # اگه قبلاً answered بود، دوباره بشه open
            if t[6] == 'answered':
                update_ticket_status(tid, 'open')
            return redirect(f'/panel/tickets/{tid}')

    replies = get_ticket_replies(tid)
    return render_template('panel_ticket_view.html',
        ticket=t, replies=replies,
        current_settings=_cs(uid))


@ticket_bp.route('/panel/tickets/<int:tid>/close', methods=['POST'])
def panel_ticket_close(tid):
    uid = _uid()
    if not uid:
        return redirect('/panel/login')
    t = get_ticket(tid)
    if t and t[1] == uid:
        update_ticket_status(tid, 'closed')
    return redirect(f'/panel/tickets/{tid}')


# ========== پنل ادمین ==========
@ticket_bp.route('/admin/tickets')
def admin_tickets():
    if not _is_admin():
        return redirect('/admin/login')
    status_filter = request.args.get('status')
    tks = get_all_tickets(300, status_filter)
    return render_template('admin_tickets.html',
        tickets=tks,
        filter=status_filter or '',
        open_count=count_open_tickets(),
        current_settings=_cs())


@ticket_bp.route('/admin/tickets/<int:tid>', methods=['GET', 'POST'])
def admin_ticket_view(tid):
    if not _is_admin():
        return redirect('/admin/login')

    t = get_ticket(tid)
    if not t:
        return redirect('/admin/tickets')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'reply':
            msg = (request.form.get('message') or '').strip()
            if msg:
                add_ticket_reply(tid, 'admin', msg)
                # 🔔 نوتیف به کاربر
                try:
                    notify_ticket_reply(t[1], tid, t[4])
                except Exception:
                    pass
        elif action == 'close':
            update_ticket_status(tid, 'closed')
        elif action == 'open':
            update_ticket_status(tid, 'open')
        return redirect(f'/admin/tickets/{tid}')

    replies = get_ticket_replies(tid)
    return render_template('admin_ticket_view.html',
        ticket=t, replies=replies,
        current_settings=_cs())
