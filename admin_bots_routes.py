from flask import Blueprint, render_template, request, redirect, session, flash
from database import (get_all_admin_bots, save_admin_bot, delete_admin_bot,
                      get_bot_stats, get_ads_history, add_ad, count_bot_members, get_user_settings)

admin_bots_bp = Blueprint('admin_bots', __name__)

def _is_admin(): return bool(session.get('is_admin'))
def _cs():
    try: return get_user_settings(1)
    except: return None

@admin_bots_bp.route('/admin/bots', methods=['GET', 'POST'])
def admin_bots():
    if not _is_admin(): return redirect('/admin/login')
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            m = (request.form.get('messenger') or '').strip()
            t = (request.form.get('token') or '').strip()
            u = (request.form.get('username') or '').strip()
            if m and t:
                save_admin_bot(m, t, u)
        return redirect('/admin/bots')
    bots = get_all_admin_bots()
    stats = get_bot_stats()
    members = count_bot_members()
    return render_template('admin_bots.html', bots=bots, stats=stats, members=members, current_settings=_cs())

@admin_bots_bp.route('/admin/bots/<m>/delete', methods=['POST'])
def admin_bot_delete(m):
    if not _is_admin(): return redirect('/admin/login')
    delete_admin_bot(m)
    return redirect('/admin/bots')

@admin_bots_bp.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not _is_admin(): return redirect('/admin/login')
    if request.method == 'POST':
        msg = (request.form.get('message') or '').strip()
        if msg:
            add_ad(msg)
            flash('تبلیغ در صف قرار گرفت', 'ok')
        return redirect('/admin/ads')
    history = get_ads_history(30)
    members = count_bot_members()
    return render_template('admin_ads.html', history=history, members=members, current_settings=_cs())
