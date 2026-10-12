from flask import Blueprint, render_template, request, redirect, session, flash
from database import (add_poster_template, get_poster_templates,
                      delete_poster_template, toggle_poster_template,
                      get_user_settings)

poster_bp = Blueprint('poster', __name__)


def _uid(): return session.get('user_id')
def _is_admin(): return bool(session.get('is_admin'))
def _cs(uid=None):
    try: return get_user_settings(uid or 1)
    except: return None


@poster_bp.route('/panel/posters', methods=['GET', 'POST'])
def panel_posters():
    uid = _uid()
    if not uid: return redirect('/panel/login')

    if request.method == 'POST':
        code = (request.form.get('code') or '').strip().lower().replace(' ', '')
        name = (request.form.get('name') or '').strip()
        prompt = (request.form.get('prompt') or '').strip()
        cat = (request.form.get('category') or 'general').strip()
        if code and name and prompt:
            r = add_poster_template(uid, code, name, prompt, cat)
            if r:
                flash(f'✅ قالب «{code}» اضافه شد', 'ok')
            else:
                flash('❌ کد تکراری است', 'error')
        return redirect('/panel/posters')

    templates = get_poster_templates(uid)
    return render_template('panel_posters.html',
        templates=templates,
        current_settings=_cs(uid))


@poster_bp.route('/panel/posters/<int:tid>/delete', methods=['POST'])
def panel_poster_delete(tid):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    delete_poster_template(tid)
    return redirect('/panel/posters')


@poster_bp.route('/panel/posters/<int:tid>/toggle', methods=['POST'])
def panel_poster_toggle(tid):
    uid = _uid()
    if not uid: return redirect('/panel/login')
    toggle_poster_template(tid)
    return redirect('/panel/posters')
