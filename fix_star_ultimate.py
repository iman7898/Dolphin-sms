import os, re, glob

# 1. پاک کردن کدهای قبلی از تمام فایل‌های HTML
for filepath in glob.glob('templates/**/*.html', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # حذف مودال و اسکریپت‌های قبلی (اگه وجود داشته باشن)
    content = re.sub(r'<!-- ====== شروع پنجره جوایز.*?پایان پنجره جوایز دلفین ====== -->', '', content, flags=re.DOTALL)
    content = re.sub(r'<div id="pointsModal".*?</script>', '', content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 2. کدهای جدید و ضدگلوله
modal_and_script = """
<!-- ====== پنجره جوایز دلفین (نسخه نهایی) ====== -->
<style>
    #pointsModal { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,10,20,0.9); z-index: 999999; justify-content: center; align-items: center; backdrop-filter: blur(5px); font-family: Tahoma; }
    .points-content { background: linear-gradient(135deg, #001a33, #003366); border: 2px solid #00d4ff; border-radius: 20px; padding: 25px; width: 85%; max-width: 350px; color: white; box-shadow: 0 0 30px rgba(0,212,255,0.6); position: relative; text-align: center; }
    .close-btn { position: absolute; top: 10px; left: 15px; font-size: 30px; cursor: pointer; color: #ff4d4d; font-weight: bold; }
    .reward-item { background: rgba(255,255,255,0.08); border: 1px solid rgba(0,212,255,0.3); padding: 12px; border-radius: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .reward-btn { background: #00d4ff; color: #001a33; padding: 5px 10px; border-radius: 8px; font-weight: bold; font-size: 12px; cursor: pointer; border: none; }
    #floatingRewardBtn { position: fixed; bottom: 70px; left: 15px; background: #00ff88; color: #000; padding: 10px 15px; border-radius: 30px; font-weight: bold; font-family: Tahoma; box-shadow: 0 4px 15px rgba(0,255,136,0.5); z-index: 99999; cursor: pointer; display: flex; align-items: center; gap: 5px; border: 2px solid #fff; }
</style>

<div id="pointsModal" onclick="if(event.target.id === 'pointsModal') this.style.display='none'">
    <div class="points-content">
        <span class="close-btn" onclick="document.getElementById('pointsModal').style.display='none'">&times;</span>
        <h2 style="color:#00d4ff; margin:0 0 10px 0; font-size:20px;">🏆 باشگاه مشتریان</h2>
        <div style="font-size:40px; font-weight:bold; color:#ffd700; margin-bottom:15px;">⭐ {{ points|default(0) }}</div>
        
        <div class="reward-item">
            <span style="font-size:13px;">🚚 ارسال رایگان</span>
            <button class="reward-btn">۵۰۰ امتیاز</button>
        </div>
        <div class="reward-item">
            <span style="font-size:13px;">🎟️ تخفیف ۱۰٪</span>
            <button class="reward-btn">۱۰۰۰ امتیاز</button>
        </div>
        <div class="reward-item">
            <span style="font-size:13px;">🎁 هدیه مغازه‌دار</span>
            <button class="reward-btn">۲۰۰۰ امتیاز</button>
        </div>
    </div>
</div>

<!-- دکمه شناور (برای اینکه مطمئن باشیم باز میشه) -->
<div id="floatingRewardBtn" onclick="document.getElementById('pointsModal').style.display='flex'">
    🏆 جوایز دلفین
</div>

<script>
    // اسکریپت خشن برای پیدا کردن هر چیزی که ستاره داره
    setTimeout(function() {
        var allElements = document.querySelectorAll('*');
        for (var i = 0; i < allElements.length; i++) {
            var el = allElements[i];
            // اگه تگ شامل ستاره بود و فرزندی نداشت (یعنی خودش متن ستاره رو داره)
            if (el.textContent && el.textContent.includes('⭐') && el.children.length === 0) {
                el.style.cursor = 'pointer';
                el.style.border = '2px dashed #00ff88'; // برای اینکه ببینی کجا رو باید بزنی
                el.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('pointsModal').style.display = 'flex';
                };
            }
        }
    }, 1000); // 1 ثانیه صبر میکنه تا صفحه کامل لود بشه
</script>
<!-- ====== پایان ====== -->
"""

# 3. پیدا کردن فایل مشتری و اضافه کردن کد
customer_files = glob.glob('templates/**/*customer*.html', recursive=True) + glob.glob('templates/**/*dashboard*.html', recursive=True)
files_updated = 0

for filepath in set(customer_files):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'pointsModal' not in content:
        if '</body>' in content:
            content = content.replace('</body>', modal_and_script + '\n</body>')
        else:
            content += modal_and_script
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        files_updated += 1
        print(f"✅ آپدیت شد: {filepath}")

if files_updated == 0:
    print("⚠️ فایل مشتری پیدا نشد! مجبورم به همه فایل‌ها اضافه کنم.")
    for filepath in glob.glob('templates/**/*.html', recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'pointsModal' not in content and '</body>' in content:
            content = content.replace('</body>', modal_and_script + '\n</body>')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
