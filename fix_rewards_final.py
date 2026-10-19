import re, glob

# 1. اضافه کردن جاوااسکریپت به داشبورد مشتری
for filepath in glob.glob('templates/**/*customer*.html', recursive=True) + glob.glob('templates/**/*dashboard*.html', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # پاک کردن کدهای قبلی
    content = re.sub(r'<script>\s*document\.addEventListener\("DOMContentLoaded".*?</script>', '', content, flags=re.DOTALL)
    
    # اسکریپت جدید و ضدگلوله
    js_redirect = """
    <script>
    document.addEventListener('click', function(e) {
        // هر جایی که کلیک شد، چک کن اگه متنش ستاره داشت، برو به صفحه جوایز
        let targetText = e.target.innerText || '';
        let parentText = e.target.parentElement ? e.target.parentElement.innerText : '';
        
        if (targetText.includes('⭐') || parentText.includes('⭐')) {
            window.location.href = '/customer/rewards';
        }
    });
    </script>
    """
    
    if '</body>' in content and 'window.location.href = \'/customer/rewards\'' not in content:
        content = content.replace('</body>', js_redirect + '\n</body>')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ اسکریپت هدایت به {filepath} اضافه شد.")

# 2. اصلاح کد پایتون (app.py) برای پیدا کردن سشن و رفع باگ JSON
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# پاک کردن مسیر قبلی اگه وجود داشت
code = re.sub(r"@app\.route\(['\"]/customer/rewards['\"]\)\s*def customer_rewards\(\):.*?(?=@app\.route|if __name__)", "", code, flags=re.DOTALL)

new_route = """
@app.route('/customer/rewards')
def customer_rewards():
    import json
    # پیدا کردن آیدی کاربر با هر اسمی که توی سشن باشه
    user_id = session.get('user_id') or session.get('uid') or session.get('customer_id') or session.get('id')
    
    if not user_id:
        return "❌ خطا: شما لاگین نیستید یا سشن شما منقضی شده است. لطفاً از حساب خارج و دوباره وارد شوید."
    
    db = get_db() # تابع اتصال به دیتابیس
    # گرفتن اطلاعات کاربر
    user = db.execute("SELECT * FROM users WHERE id = ? OR username = ?", (user_id, user_id)).fetchone()
    
    points_num = 0
    tier_name = "برنزی 🥉"
    
    if user:
        try:
            raw_points = user['points']
            # اگه دیتابیس رشته JSON ذخیره کرده باشه، عدد رو در میاریم
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
# اضافه کردن قبل از app.run
if 'if __name__ == "__main__":' in code:
    code = code.replace('if __name__ == "__main__":', new_route + 'if __name__ == "__main__":')
else:
    code += new_route

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ مسیر /customer/rewards در app.py اصلاح شد.")
