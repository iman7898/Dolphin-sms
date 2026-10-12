from flask import Blueprint, render_template, request, redirect, session
from database import (get_wallet, charge_wallet, deduct_wallet,
                      get_transactions, get_all_wallets, get_user,
                      get_user_settings)

wallet_bp = Blueprint('wallet', __name__)


def _current_uid():
    return session.get('user_id') or session.get('uid') or session.get('id')


def _is_admin():
    return bool(session.get('is_admin'))


@wallet_bp.route('/panel/wallet')
def panel_wallet():
    uid = _current_uid()
    if not uid:
        return redirect('/panel/login')
    u = get_user(uid)
    shop = u[3] if u and len(u) > 3 else ''
    txs = get_transactions(uid, 50)
    last_update = txs[0][5] if txs else 'هنوز تراکنشی نیست'
    try:
        cs = get_user_settings(uid)
    except Exception:
        cs = None
    return render_template('wallet.html',
        balance=get_wallet(uid),
        txs=txs,
        shop=shop,
        last_update=last_update,
        current_settings=cs)


@wallet_bp.route('/admin/wallets')
def admin_wallets():
    if not _is_admin():
        return redirect('/admin/login')
    rows = get_all_wallets()
    total = sum((r[3] or 0) for r in rows)
    try:
        cs = get_user_settings(1)
    except Exception:
        cs = None
    return render_template('admin_wallets.html',
        wallets=rows, total=total, current_settings=cs)


@wallet_bp.route('/admin/wallet/<int:user_id>/charge', methods=['POST'])
def admin_charge(user_id):
    if not _is_admin():
        return redirect('/admin/login')
    try: amount = int(request.form.get('amount', 0))
    except: amount = 0
    if amount > 0:
        charge_wallet(user_id, amount, request.form.get('description') or 'شارژ توسط ادمین')
    return redirect('/admin/wallets')


@wallet_bp.route('/admin/wallet/<int:user_id>/deduct', methods=['POST'])
def admin_deduct(user_id):
    if not _is_admin():
        return redirect('/admin/login')
    try: amount = int(request.form.get('amount', 0))
    except: amount = 0
    if amount > 0:
        deduct_wallet(user_id, amount, request.form.get('description') or 'کسر توسط ادمین')
    return redirect('/admin/wallets')
