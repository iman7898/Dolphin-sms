import os, re, glob

# اسکریپت جاوااسکریپت برای پیش نمایش عکس و اصلاح فرم
js_code = """
<!-- === IMAGE UPLOAD PREVIEW === -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    // پیدا کردن کادر آپلود
    let uploadBox = Array.from(document.querySelectorAll('div')).find(el => el.innerText.includes('برای آپلود عکس محصول کلیک کنید'));
    if (!uploadBox) return;

    // پیدا کردن فرم
    let form = uploadBox.closest('form');
    if (!form) form = document.querySelector('form');
    if (form) form.setAttribute('enctype', 'multipart/form-data');

    // پیدا کردن اینپوت فایل
    let fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) {
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.name = 'image';
        fileInput.id = 'productImageInput';
        fileInput.style.display = 'none';
        if (form) form.appendChild(fileInput);
    } else {
        fileInput.name = 'image';
        fileInput.id = 'productImageInput';
    }

    // وقتی روی کادر کلیک شد، اینپوت باز بشه
    uploadBox.onclick = function() {
        fileInput.click();
    };

    // وقتی عکس انتخاب شد، پیش نمایش نشون داده بشه
    fileInput.addEventListener('change', function(e) {
        let file = e.target.files[0];
        if (!file) return;

        let reader = new FileReader();
        reader.onload = function(event) {
            let imgPreview = document.getElementById('imgPreview');
            if (!imgPreview) {
                imgPreview = document.createElement('img');
                imgPreview.id = 'imgPreview';
                imgPreview.style.cssText = 'max-width: 100%; max-height: 150px; border-radius: 10px; margin-top: 15px; object-fit: contain; box-shadow: 0 4px 15px rgba(0,255,136,0.3); border: 2px solid #00ff88;';
                uploadBox.appendChild(imgPreview);
            }
            imgPreview.src = event.target.result;
            
            // تغییر متن کادر به موفقیت
            let title = uploadBox.querySelector('div:nth-child(2)');
            if (title) {
                title.innerText = 'عکس با موفقیت انتخاب شد! ✅';
                title.style.color = '#00d4ff';
            }
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
        print(f"✅ اسکریپت پیش‌نمایش عکس به {file} اضافه شد.")
