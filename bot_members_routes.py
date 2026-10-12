from flask import Blueprint, render_template, request, redirect, session, flash
from database import get_user_settings
import sqlite3

members_bp = Blueprint('bot_members_view', __name__)

def _is_admin(): return bool(session.get('is_admin'))
def _cs():
    try: return get_user_settings(1)
    except: return None
def db(): return sqlite3.connect('panel.db')

@members_bp.route('/admin/bot-members')
def admin_bot_members():
    if not _is_admin(): return redirect('/admin/login')
    filter_m = request.args.get('messenger', '')
    q = request.args.get('q', '').strip()
    conn = db()
    c = conn.cursor()
    sql = "SELECT id, messenger, chat_id, first_name, joined_at FROM bot_members WHERE 1=1"
    params = []
    if filter_m:
        sql += " AND messenger=?"
        params.append(filter_m)
    if q:
        sql += " AND (chat_id LIKE ? OR first_name LIKE ?)"
        params.append('%' + q + '%')
        params.append('%' + q + '%')
    sql += " ORDER BY id DESC LIMIT 500"
    c.execute(sql, params)
    members = c.fetchall()
    c.execute("SELECT messenger, COUNT(*) FROM bot_members GROUP BY messenger")
    stats = c.fetchall()
    total = sum(s[1] for s in stats)
    c.execute("SELECT COUNT(*) FROM bot_members WHERE DATE(joined_at)=DATE('now')")
    today = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bot_members WHERE joined_at >= datetime('now', '-7 days')")
    week = c.fetchone()[0]
    conn.close()
    return render_template('admin_bot_members.html',
        members=members, stats=stats, total=total, today=today, week=week,
        filter_m=filter_m, q=q, current_settings=_cs())

@members_bp.route('/admin/bot-members/<int:mid>/delete', methods=['POST'])
def admin_member_delete(mid):
    if not _is_admin(): return redirect('/admin/login')
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM bot_members WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    return redirect('/admin/bot-members')

@members_bp.route('/admin/bot-members/clear', methods=['POST'])
def admin_members_clear():
    if not _is_admin(): return redirect('/admin/login')
    m = request.form.get('messenger', '')
    conn = db()
    c = conn.cursor()
    if m:
        c.execute("DELETE FROM bot_members WHERE messenger=?", (m,))
    else:
        c.execute("DELETE FROM bot_members")
    conn.commit()
    conn.close()
    return redirect('/admin/bot-members')
