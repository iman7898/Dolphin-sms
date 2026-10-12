from flask import Blueprint, render_template, request, redirect, session, flash
from database import get_user_settings
from url_config import get_public_url, set_public_url

url_admin_bp = Blueprint('url_admin', __name__)


def _is_admin(): return bool(session.get('is_admin'))
def _cs():
    try: return get_user_settings(1)
    except: return None


@url_admin_bp.route('/admin/public-url', methods=['GET', 'POST'])
def admin_public_url():
    if not _is_admin():
        return redirect('/admin/login')

    saved = False
    if request.method == 'POST':
        url = (request.form.get('public_url') or '').strip()
        if url:
            set_public_url(url)
            saved = True
            flash('✅ آدرس عمومی ذخیره شد', 'ok')

    current = get_public_url()
    return render_template('admin_public_url.html',
        current_url=current, saved=saved,
        current_settings=_cs())
