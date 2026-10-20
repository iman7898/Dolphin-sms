import os, re, glob

js_code = """
<!-- === IMAGE UPLOAD PREVIEW === -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    // پیدا کردن کادر آپلود
    let uploadBox = Array.from(document.querySelectorAll('div')).find(el => el.innerText.includes('برای آپلود عکس محصول کلیک کنید') || el.innerText.includes('عکس با موفقیت انتخاب شد'));
    if (!uploadBox) return;

    let fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) return;

    // وقتی عکس انتخاب شد
    fileInput.addEventListener('change', function(e) {
        let file = e.target.files[0];
        if (!file) return;

        let reader = new FileReader();
        reader.onload = function(event) {
            // 1. پاک کردن کل محوای داخل کادر (متن و آیکون)
            uploadBox.innerHTML = '';
            
            // 2. تغییر ظاهر کادر (حذف خط چین و گرد کردن گوشه ها)
            uploadBox.style.border = '2px solid #00ff88';
            uploadBox.style.padding = '0';
            uploadBox.style.overflow = 'hidden';
            uploadBox.style.background = '#000';
            
            // 3. ساخت تگ عکس و گذاشتنش داخل کادر
            let imgPreview = document.createElement('img');
            imgPreview.src = event.target.result;
            imgPreview.style.cssText = 'width: 100%; height: 250px; object-fit: cover; display: block;';
            
            uploadBox.appendChild(imgPreview);
        };
        reader.readAsDataURL(file);
    });
});
</script>
<!-- === IMAGE UPLOAD PREVIEW END === -->
"""

for file in glob.glob('templates/**/*.html', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'برای آپلود عکس محصول کلیک کنید' in html:
        # پاک کردن اسکریپت‌های قبلی برای جلوگیری از تداخل
        html = re.sub(r'<!-- === IMAGE UPLOAD PREVIEW === -->.*?<!-- === IMAGE UPLOAD PREVIEW END === -->', '', html, flags=re.DOTALL)
        
        # اضافه کردن اسکریپت جدید
        if '</body>' in html:
            html = html.replace('</body>', js_code + '\n</body>')
        else:
            html += js_code

        with open(file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ کد پیش‌نمایش عکس داخل کادر به {file} اعمال شد.")
