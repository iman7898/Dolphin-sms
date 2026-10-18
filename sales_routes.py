from flask import Blueprint, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime, timedelta

sales_bp = Blueprint('sales', __name__)

def _uid(): return session.get('user_id')
def _cs(uid):
    try:
        from database import get_user_settings
        return get_user_settings(uid)
    except: return None

@sales_bp.route('/panel/sales', methods=['GET'])
def sales_dashboard():
    if not _uid(): return redirect('/panel/login')
    uid = _uid()
    
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    
    # آمار امروز
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM shop_sales WHERE shop_id=? AND DATE(created_at)=?", (uid, today))
    today_stat = c.fetchone()
    
    # آمار کل ماه
    c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM shop_sales WHERE shop_id=? AND strftime('%Y-%m', created_at)=?", (uid, datetime.now().strftime('%Y-%m')))
    month_stat = c.fetchone()
    
    conn.close()
    return render_template('panel_sales.html', today_stat=today_stat, month_stat=month_stat, current_settings=_cs(uid))

@sales_bp.route('/panel/sales/add', methods=['POST'])
def sales_add():
    if not _uid(): return jsonify({'error': 'not logged in'}), 401
    amount = request.json.get('amount')
    try:
        amount = int(amount)
    except:
        return jsonify({'error': 'مبلغ نامعتبر است'})
        
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO shop_sales (shop_id, amount) VALUES (?, ?)", (_uid(), amount))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@sales_bp.route('/panel/sales/chart-data')
def sales_chart_data():
    if not _uid(): return jsonify({'error': 'not logged in'}), 401
    uid = _uid()
    
    conn = sqlite3.connect('panel.db')
    c = conn.cursor()
    
    # داده‌های ۷ روز اخیر
    labels = []
    data = []
    for i in range(6, -1, -1):
        d = datetime.now() - timedelta(days=i)
        day_str = d.strftime('%Y-%m-%d')
        day_name = d.strftime('%A')
        # تبدیل به فارسی
        days_fa = {'Saturday':'شنبه', 'Sunday':'یکشنبه', 'Monday':'دوشنبه', 'Tuesday':'سه‌شنبه', 'Wednesday':'چهارشنبه', 'Thursday':'پنجشنبه', 'Friday':'جمعه'}
        labels.append(days_fa.get(day_name, day_name))
        
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM shop_sales WHERE shop_id=? AND DATE(created_at)=?", (uid, day_str))
        data.append(c.fetchone()[0])
        
    conn.close()
    return jsonify({'labels': labels, 'data': data})
