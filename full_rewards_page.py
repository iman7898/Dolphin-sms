import os, re, glob

# ==========================================
# 1. ساخت قالب صفحه جدید (customer_rewards.html)
# ==========================================
rewards_html = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>باشگاه مشتریان | دلفین</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Tahoma, sans-serif; }
        body { background: #001220; color: white; padding: 20px; background-image: radial-gradient(circle at top right, #003366, #001220 60%); min-height: 100vh; }
        
        .header { display: flex; align-items: center; margin-bottom: 30px; }
        .back-btn { background: rgba(255,255,255,0.1); border: 1px solid #00d4ff; color: #00d4ff; padding: 8px 15px; border-radius: 10px; text-decoration: none; font-size: 14px; transition: 0.3s; }
        .back-btn:hover { background: #00d4ff; color: #001220; }
        .header h1 { font-size: 18px; margin-right: 15px; color: #fff; }

        .score-card { background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,85,255,0.1)); border: 1px solid #00d4ff; border-radius: 20px; padding: 30px 20px; text-align: center; margin-bottom: 30px; box-shadow: 0 0 20px rgba(0,212,255,0.2); backdrop-filter: blur(10px); }
        .score-title { font-size: 16px; color: #a0c4ff; margin-bottom: 10px; }
        .score-value { font-size: 60px; font-weight: bold; color: #ffd700; text-shadow: 0 0 20px rgba(255,215,0,0.5); line-height: 1; }
        .score-desc { font-size: 12px; color: #ccc; margin-top: 15px; }

        .section-title { font-size: 16px; margin-bottom: 15px; color: #00d4ff; display: flex; align-items: center; gap: 10px; }
        
        .rewards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .reward-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 20px 15px; text-align: center; transition: 0.3s; position: relative; overflow: hidden; }
        .reward-card:hover { transform: translateY(-5px); border-color: #00d4ff; box-shadow: 0 10px 20px rgba(0,212,255,0.2); }
        .reward-icon { font-size: 35px; margin-bottom: 10px; }
        .reward-name { font-size: 14px; margin-bottom: 10px; font-weight: bold; }
        .reward-cost { background: rgba(0,212,255,0.15); color: #00d4ff; padding: 6px 10px; border-radius: 8px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 15px; }
        .redeem-btn { background: #00d4ff; color: #001220; border: none; padding: 8px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .redeem-btn:hover { background: #fff; }
        .redeem-btn:disabled { background: #555; color: #999; cursor: not-allowed; }
    </style>
</head>
<body>

    <div class="header">
        <a href="/customer" class="back-btn">← بازگشت</a>
        <h1>باشگاه مشتریان</h1>
    </div>

    <div class="score-card">
        <div class="score-title">✨ امتیاز فعلی شما</div>
        <!-- اینجا فقط عدد نمایش داده میشه -->
        <div class="score-value">{{ points_num }}</div>
        <div class="score-desc">سطح شما: {{ tier_name }}</div>
    </div>

    <div class="section-title">🎁 جوایز قابل دریافت</div>
    
    <div class="rewards-grid">
        <div class="reward-card">
            <div class="reward-icon">🚚</div>
            <div class="reward-name">ارسال رایگان</div>
            <div class="reward-cost">۵۰۰ امتیاز</div>
            <button class="redeem-btn" {% if points_num < 500 %}disabled{% endif %}>دریافت</button>
        </div>
        <div class="reward-card">
            <div class="reward-icon">🎟️</div>
            <div class="reward-name">تخفیف ۱۰٪</div>
            <div class="reward-cost">۱۰۰۰ امتیاز</div>
            <button class="redeem-btn" {% if points_num < 1000 %}disabled{% endif %}>دریافت</button>
        </div>
        <div class="reward-card">
            <div class="reward-icon">🎁</div>
            <div class="reward-name">هدیه مغازه‌دار</div>
            <div class="reward-cost">۲۰۰۰ امتیاز</div>
            <button class="redeem-btn" {% if points_num < 2000 %}disabled{% endif %}>دریافت</button>
        </div>
        <div class="reward-card">
            <div class="reward-icon">👑</div>
            <div class="reward-name">عضویت VIP</div>
            <div class="reward-cost">۵۰۰۰ امتیاز</div>
            <button class="redeem-btn" {% if points_num < 5000 %}disabled{% endif %}>دریافت</button>
        </div>
    </div>

</body>
</html>
"""
with open('templates/customer_rewards.html', 'w', encoding='utf-8') as f:
    f.write(rewards_html)
print("✅ صفحه جدید customer_rewards.html ساخته شد.")

# ==========================================
# 2. آپدیت app.py (ساخت مسیر جدید و حل باگ)
# ==========================================
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# اضافه کردن مسیر صفحه جدید (اگه نبود)
if "@app.route('/customer/rewards')" not in code and '@app.route("/customer/rewards")' not in code:
    new_route = """
@app.route('/customer/rewards')
def customer_rewards():
    import json
    user_id = session.get('user_id') # اگه اسم سشن فرق داره، اینو بعدا چک میکنیم
    if not user_id:
        return redirect('/login')
    
    # گرفتن اطلاعات کاربر از دیتابیس
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    points_num = 0
    tier_name = "برنزی 🥉"
    
    if user:
        raw_points = user['points'] if 'points' in user.keys() else '0'
        # حل باگ: اگه دیتابیس JSON ذخیره کرده بود، فقط عدد رو دربیار
        try:
            if '{' in str(raw_points):
                data = json.loads(raw_points)
                points_num = int(data.get('points', 0))
                tier_name = data.get('tier', 'برنزی 🥉')
            else:
                points_num = int(raw_points) if raw_points else 0
        except:
            points_num = 0
            
    return render_template('customer_rewards.html', points_num=points_num, tier_name=tier_name)

if __name__ == "__main__":
"""
    code = code.replace('if __name__ == "__main__":', new_route)
    print("✅ مسیر /customer/rewards به app.py اضافه شد.")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

# ==========================================
# 3. پاک کردن مودال زشت از داشبورد مشتری
# ==========================================
for filepath in glob.glob('templates/**/*.html', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # پاک کردن کدهای قبلی
    content = re.sub(r'<!-- ====== پنجره جوایز.*?پایان.*?-->', '', content, flags=re.DOTALL)
    content = re.sub(r'<!-- ====== شروع.*?پایان پنجره جوایز دلفین ====== -->', '', content, flags=re.DOTALL)
    
    # جایگزینی ستاره با لینک به صفحه جدید
    if 'customer_dashboard.html' in filepath:
        # یه استایل خوشگل برای کارت امتیاز
        new_star = """<a href="/customer/rewards" style="text-decoration:none; color:inherit; display:block;"><div style="display:flex; align-items:center; gap:5px; background:rgba(255,215,0,0.1); border:1px solid #ffd700; padding:5px 10px; border-radius:10px;"><span style="color:#ffd700; font-weight:bold;">⭐ امتیاز و جوایز</span></div></a>"""
        
        # پیدا کردن باکس ستاره با رجکس
        content = re.sub(r'<[^>]+>\s*⭐.*?</[^>]+>', new_star, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ کدهای زشت پاک شدند و لینک به صفحه جدید اضافه شد.")
