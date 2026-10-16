"""⏰ زمان‌بندی پست خودکار (فقط ادمین)"""
from flask import Blueprint, render_template, request, redirect, session, flash
import sqlite3

schedule_bp = Blueprint('schedule', __name__)

def _is_admin(): return bool(session.get('is_admin'))
def _cs():
    try:
        from database import get_user_settings
        return get_user_settings(1)
    except: return None


@schedule_bp.route('/admin/schedule', methods=['GET', 'POST'])
def admin_schedule():
    if not _is_admin(): return redirect('/admin/login')
    from database import (add_schedule, get_schedules, toggle_schedule,
                          delete_schedule, get_schedule_logs, get_all_users)
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            ch = (request.form.get('channel_id') or '').strip()
            headline = (request.form.get('headline') or '').strip()
            t = (request.form.get('post_time') or '').strip()
            title = (request.form.get('title') or '').strip()
            tag = (request.form.get('tag') or '').strip()
            days = (request.form.get('days') or 'daily').strip()
            shop_id = int(request.form.get('shop_id') or 1)
            if ch and headline and t:
                add_schedule(shop_id, ch, headline, t, title, tag, days)
                flash('✅ پست زمان‌بندی شد', 'ok')
            else:
                flash('❌ کانال، سرفصل و ساعت الزامی', 'error')
        elif action == 'toggle':
            sid = int(request.form.get('id') or 0)
            if sid: toggle_schedule(sid)
        elif action == 'delete':
            sid = int(request.form.get('id') or 0)
            if sid: delete_schedule(sid)
        return redirect('/admin/schedule')

    schedules = get_schedules()
    logs = get_schedule_logs(30)
    try:
        users = get_all_users()
    except:
        users = []
    return render_template('admin_schedule.html',
                           schedules=schedules, logs=logs,
                           users=users, current_settings=_cs())
