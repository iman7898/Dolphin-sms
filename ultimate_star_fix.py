import os, glob

modal_and_script = """
<div id="pointsModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,10,20,0.85); z-index:9999; justify-content:center; align-items:center; backdrop-filter:blur(5px); font-family:Tahoma;">
    <div style="background:linear-gradient(135deg, #001a33, #003366); border:2px solid #00d4ff; border-radius:20px; padding:25px; width:90%; max-width:380px; color:white; box-shadow:0 0 30px rgba(0,212,255,0.4); position:relative;">
        <span onclick="document.getElementById('pointsModal').style.display='none'" style="position:absolute; top:15px; left:20px; font-size:28px; cursor:pointer; color:#ff4d4d; font-weight:bold;">&times;</span>
        <div style="text-align:center; margin-bottom:20px;">
            <h2 style="color:#00d4ff; margin:0 0 10px 0; font-size:22px;">🏆 باشگاه مشتریان</h2>
            <div style="font-size:45px; font-weight:bold; color:#ffd700;">⭐ {{ points or 0 }}</div>
            <p style="color:#aaa; font-size:12px; margin-top:5px;">با هر ۱۰,۰۰۰ تومان خرید، ۱ امتیاز بگیرید!</p>
        </div>
        <ul style="list-style:none; padding:0; margin:0;">
            <li style="background:rgba(255,255,255,0.05); border:1px solid rgba(0,212,255,0.2); padding:12px 15px; border-radius:12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:14px; color:#e0e0e0;">🚚 ارسال رایگان سفارش</span>
                <span style="background:#00d4ff; color:#001a33; padding:5px 12px; border-radius:8px; font-weight:bold; font-size:13px;">۵۰۰ امتیاز</span>
            </li>
            <li style="background:rgba(255,255,255,0.05); border:1px solid rgba(0,212,255,0.2); padding:12px 15px; border-radius:12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:14px; color:#e0e0e0;">🎟️ کد تخفیف ۱۰٪</span>
                <span style="background:#00d4ff; color:#001a33; padding:5px 12px; border-radius:8px; font-weight:bold; font-size:13px;">۱۰۰۰ امتیاز</span>
            </li>
        </ul>
    </div>
</div>

<script>
// این اسکریپت به کل صفحه گوش میده. هر جا کلیک شد، چک میکنه آیا روی ستاره بوده یا نه!
document.addEventListener('click', function(e) {
    let target = e.target;
    // چک میکنیم اگه خودش یا والدش ستاره داشته باشن
    if ((target.innerText && target.innerText.includes('⭐')) || (target.parentElement && target.parentElement.innerText && target.parentElement.innerText.includes('⭐'))) {
        let modal = document.getElementById('pointsModal');
        if(modal) {
            modal.style.display = 'flex';
        }
    }
});
</script>
"""

files_updated = 0
for filepath in glob.glob('templates/**/*.html', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # اگه ستاره توی این فایل بود
    if '⭐' in content:
        # اگه مودال از قبل نبود، اضافه کن
        if 'id="pointsModal"' not in content:
            if '</body>' in content:
                content = content.replace('</body>', modal_and_script + '\n</body>')
            else:
                content += modal_and_script
            files_updated += 1
            print(f"✅ پنجره جوایز به فایل {filepath} اضافه شد.")
        else:
            print(f"ℹ️ پنجره جوایز از قبل در {filepath} وجود دارد.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 عملیات تمام شد. {files_updated} فایل آپدیت شدند.")
