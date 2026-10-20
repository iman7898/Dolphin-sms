file = 'templates/panel_dashboard.html'
try:
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()
except:
    print("❌ فایل پیدا نشد.")
    exit()

# اسکریپتی که دکمه ها رو دوباره زنده میکنه
script = """
<!-- === REVIVE BUTTONS === -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    // پیدا کردن تمام دکمه ها
    let divs = document.querySelectorAll('div');
    
    divs.forEach(function(btn) {
        let txt = btn.innerText || '';
        // اگه دکمه های 6 گانه بود
        if (txt.includes('عکس') && txt.includes('📷')) {
            btn.onclick = function() { document.querySelector('input[type="file"]').click(); };
        } 
        else if (txt.includes('آپلود از گوشی') || (txt.includes('آپلود') && txt.includes('📁'))) {
            btn.onclick = function() { document.querySelector('input[type="file"]').click(); };
        }
        else if (txt.includes('ایموجی') && txt.includes('😋')) {
            btn.onclick = function() { alert('بخش ایموجی به زودی فعال میشود!'); };
        }
        else if (txt.includes('قوی‌سازی') && txt.includes('🤖')) {
            btn.onclick = function() { alert('هوش مصنوعی در حال قوی کردن متن است...'); };
        }
        else if (txt.includes('تغییر با AI') && txt.includes('✨')) {
            btn.onclick = function() { alert('متن با هوش مصنوعی تغییر میکند...'); };
        }
        else if (txt.includes('ساخت با AI') && txt.includes('🎨')) {
            btn.onclick = function() { alert('در حال ساخت عکس با هوش مصنوعی...'); };
        }
    });
});
</script>
<!-- === REVIVE BUTTONS END === -->
"""

if 'REVIVE BUTTONS' not in html:
    if '</body>' in html:
        html = html.replace('</body>', script + '\n</body>')
    else:
        html += script

with open(file, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ دکمه‌ها با موفقیت زنده شدند.")
