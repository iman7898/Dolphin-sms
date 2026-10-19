import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# پیدا کردن مسیر قبلی و حذف کامل اون
code = re.sub(r"@app\.route\(['\"]/customer/rewards['\"]\)\s*def customer_rewards\(\):.*?(?=@app\.route|if __name__)", "", code, flags=re.DOTALL)

# نوشتن مسیر جدید با اتصال مستقیم به دیتابیس
new_route = """
@app.route('/customer/rewards')
def customer_rewards():
    import json
    import sqlite3
    
    # پیدا کردن آیدی کاربر از سشن
    user_id = session.get('user_id') or session.get('uid') or session.get('customer_id') or session.get('id')
    
    if not user_id:
        return "❌ خطا: شما لاگین نیستید. لطفاً دوباره وارد شوید."
    
    # اتصال مستقیم به دیتابیس (بدون نیاز به تابع get_db)
    conn = sqlite3.connect('panel.db')
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    points_num = 0
    tier_name = "برنزی 🥉"
    
    if user:
        try:
            raw_points = user['points']
            if raw_points and str(raw_points).strip().startswith('{'):
                data = json.loads(raw_points)
                points_num = int(data.get('points', 0))
                tier_name = data.get('tier', 'برنزی 🥉')
            else:
                points_num = int(raw_points) if raw_points else 0
        except Exception as e:
            print("Error parsing points:", e)
            points_num = 0
            
    return render_template('customer_rewards.html', points_num=points_num, tier_name=tier_name)

"""
# تزریق قبل از app.run
if 'if __name__ == "__main__":' in code:
    code = code.replace('if __name__ == "__main__":', new_route + 'if __name__ == "__main__":')
else:
    code += new_route

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ ارور get_db برطرف شد و مسیر اصلاح شد.")
