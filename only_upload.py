import os

file = 'templates/panel_dashboard.html'
if not os.path.exists(file):
    print("⚠️ فایل پیدا نشد!")
    exit()

with open(file, 'r', encoding='utf-8') as f:
    html = f.read()

script = """
<!-- REMOVE_AI_BUTTONS_SCRIPT -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    // 1. پیدا کردن و مخفی کردن 6 دکمه
    let divs = document.querySelectorAll('div');
    let grid = null;
    for (let d of divs) {
        if (d.innerText && d.innerText.includes('قوی‌سازی متن') && d.children.length > 1) {
            grid = d;
            break;
        }
    }
    
    if (grid) {
        grid.style.display = 'none'; // مخفی کردن کامل 6 دکمه
        
        // 2. ساخت کادر بزرگ آپلود
        let uploadArea = document.createElement('div');
        uploadArea.style.cssText = 'margin-bottom: 20px; padding: 30px 20px; background: #031526; border: 2px dashed #00ff88; border-radius: 15px; text-align: center; cursor: pointer; transition: 0.3s;';
        uploadArea.onmouseover = () => uploadArea.style.background = '#06213b';
        uploadArea.onmouseout = () => uploadArea.style.background = '#031526';
        
        uploadArea.onclick = function() {
            let fileInput = document.querySelector('input[type="file"]');
            if(fileInput) fileInput.click();
        };
        
        uploadArea.innerHTML = `
            <div style="font-size: 50px; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(0,255,136,0.5));">📸</div>
            <div style="color: #00ff88; font-weight: bold; font-size: 18px; font-family: Tahoma;">برای آپلود عکس محصول کلیک کنید</div>
            <div style="color: #6688aa; font-size: 13px; margin-top: 8px; font-family: Tahoma;">فرمت‌های مجاز: JPG, PNG</div>
        `;
        
        // قرار دادن کادر بعد از دکمه‌های مخفی شده
        grid.parentNode.insertBefore(uploadArea, grid.nextSibling);
    }

    // 3. اطمینان از اینکه فرم قابلیت آپلود فایل رو داره
    let forms = document.querySelectorAll('form');
    forms.forEach(f => {
        f.setAttribute('enctype', 'multipart/form-data');
        let fi = f.querySelector('input[type="file"]');
        if (!fi) {
            let newFi = document.createElement('input');
            newFi.type = 'file';
            newFi.name = 'image';
            newFi.accept = 'image/*';
            newFi.style.display = 'none';
            f.appendChild(newFi);
        } else {
            fi.style.display = 'none';
            if (!fi.name) fi.name = 'image';
        }
    });
});
</script>
<!-- REMOVE_AI_BUTTONS_SCRIPT -->
"""

if 'REMOVE_AI_BUTTONS_SCRIPT' not in html:
    if '</body>' in html:
        html = html.replace('</body>', script + '\n</body>')
    else:
        html += script

with open(file, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ 6 دکمه پاک شدند و کادر آپلود عکس جایگزین شد.")
