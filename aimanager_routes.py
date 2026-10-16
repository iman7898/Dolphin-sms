from flask import Blueprint, render_template, request, redirect, session, flash, jsonify
from database import (save_bot_token, get_ai_plans, get_ai_plan, get_active_subscription,
                      has_used_trial, create_ai_subscription, cancel_ai_subscription,
                      get_ai_config, save_ai_config, toggle_ai_config,
                      add_ai_task, get_user_ai_tasks, count_pending_tasks,
                      get_all_ai_subscriptions, get_ai_stats, get_user_settings,
                      get_user, charge_wallet, get_wallet,
                      get_messengers, get_messenger_name)

aimanager_bp = Blueprint('aimanager', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


@aimanager_bp.route('/panel/ai-manager')
def panel_ai_manager():
    uid = _uid()
    if not uid: return redirect('/panel/login')
    sub = get_active_subscription(uid)
    used_trial = has_used_trial(uid)
    plans = get_ai_plans()
    config = get_ai_config(uid)
    tasks = get_user_ai_tasks(uid, 30)
    pending = count_pending_tasks(uid)
    balance = get_wallet(uid)
    return render_template('panel_ai_manager.html',
        sub=sub, used_trial=used_trial, plans=plans,
        config=config, tasks=tasks, pending=pending, balance=balance,
        current_settings=_cs(uid))


@aimanager_bp.route('/panel/ai-manager/plans')
def panel_ai_plans():
    uid = _uid()
    if not uid: return redirect('/panel/login')
    plans = get_ai_plans()
    sub = get_active_subscription(uid)
    used_trial = has_used_trial(uid)
    balance = get_wallet(uid)
    return render_template('panel_ai_plans.html',
        plans=plans, sub=sub, used_trial=used_trial, balance=balance,
        current_settings=_cs(uid))


@aimanager_bp.route('/panel/ai-manager/subscribe/<code>', methods=['POST'])
def panel_ai_subscribe(code):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    trial = request.form.get('trial') == '1'
    messenger = (request.form.get('messenger') or 'rubika').strip()
    plan = get_ai_plan(code)
    if not plan:
        flash('پلن پیدا نشد', 'error')
        return redirect('/panel/ai-manager/plans')
    if trial:
        if not plan[5]:
            flash('این پلن تست رایگان ندارد', 'error')
            return redirect('/panel/ai-manager/plans')
        if has_used_trial(uid):
            flash('قبلاً از تست رایگان استفاده کرده‌اید', 'error')
            return redirect('/panel/ai-manager/plans')
    if not trial:
        price = plan[2]
        if get_wallet(uid) < price:
            flash(f'موجودی کافی نیست — نیاز: {price:,} ریال', 'error')
            return redirect('/panel/ai-manager/plans')
    sid = create_ai_subscription(uid, code, is_trial=1 if trial else 0, messenger=messenger)
    if not sid:
        flash('خطا در فعال‌سازی', 'error')
        return redirect('/panel/ai-manager/plans')
    if not trial:
        charge_wallet(uid, -plan[2], f'خرید پلن AI: {plan[1]}')
    flash(f'✅ پلن {plan[1]} فعال شد' + (' (تست رایگان)' if trial else ''), 'ok')
    return redirect('/panel/ai-manager')


@aimanager_bp.route('/panel/ai-manager/settings', methods=['GET', 'POST'])
def panel_ai_settings():
    uid = _uid()
    if not uid: return redirect('/panel/login')
    sub = get_active_subscription(uid)
    if not sub:
        flash('اول یه پلن فعال کن', 'error')
        return redirect('/panel/ai-manager/plans')
    if request.method == 'POST':
        data = {
            'plan_code': sub['plan_code'],
            'messenger': (request.form.get('messenger') or 'rubika').strip(),
            'channel_id': (request.form.get('channel_id') or '').strip(),
            'admin_username': (request.form.get('admin_username') or '').strip(),
            'target_channel': (request.form.get('target_channel') or '').strip(),
            'source_channels': ', '.join([x.strip() for x in request.form.getlist('source_channel') if x.strip()]),
            'content_keywords': (request.form.get('content_keywords') or '').strip(),
            'recruit_target': int(request.form.get('recruit_target') or 100),
            'recruit_message': (request.form.get('recruit_message') or '').strip(),
        }
        save_ai_config(uid, data)
        # ذخیره توکن اگه وارد شده
        bot_token = (request.form.get('bot_token') or '').strip()  # اختیاری
        if bot_token:
            save_bot_token(uid, bot_token, data.get('messenger', 'rubika'))
        flash('✅ تنظیمات ذخیره شد', 'ok')
        return redirect('/panel/ai-manager')
    config = get_ai_config(uid)
    messengers = get_messengers()
    return render_template('panel_ai_settings.html',
        sub=sub, config=config, messengers=messengers,
        current_settings=_cs(uid))


@aimanager_bp.route('/panel/ai-manager/toggle', methods=['POST'])
def panel_ai_toggle():
    uid = _uid()
    if not uid: return redirect('/panel/login')
    sub = get_active_subscription(uid)
    if not sub:
        flash('اشتراک فعال نداری', 'error')
        return redirect('/panel/ai-manager')
    config = get_ai_config(uid)
    if not config:
        flash('اول تنظیمات رو ذخیره کن', 'error')
        return redirect('/panel/ai-manager/settings')
    new_state = not config['active']
    toggle_ai_config(uid, new_state)
    if new_state:
        plan = sub['plan_code']
        msgr = config.get('messenger', 'rubika')
        if plan == 'recruit':
            add_ai_task(uid, 'recruit_start', msgr, {'channel': config['channel_id']})
        elif plan == 'content':
            add_ai_task(uid, 'content_start', msgr, {'target': config['target_channel']})
        elif plan == 'combined':
            add_ai_task(uid, 'recruit_start', msgr, {'channel': config['channel_id']})
            add_ai_task(uid, 'content_start', msgr, {'target': config['target_channel']})
    flash(f"{'🟢 فعال شد' if new_state else '🔴 غیرفعال شد'}", 'ok')
    return redirect('/panel/ai-manager')


@aimanager_bp.route('/admin/ai-manager')
def admin_ai_manager():
    if not _is_admin(): return redirect('/admin/login')
    stats = get_ai_stats()
    subs = get_all_ai_subscriptions(100)
    return render_template('admin_ai_manager.html',
        stats=stats, subs=subs, current_settings=_cs())
