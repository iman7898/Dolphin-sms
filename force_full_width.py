import re, glob

fix_css_js = """
<style>
    /* زور زدن عرض 100 درصد به کل فرم و کادرها */
    form[action="/panel/add-product"] { width: 100% !important; display: block !important; padding: 0 !important; }
    form[action="/panel/add-product"] > div { width: 100% !important; display: block !important; box-sizing: border-box !important; }
    #main-upload-box { width: 100% !important; max-width: 100% !important; display: flex !important; }
    
    /* مخفی کردن متن های مزاحم */
    .rogue-text-remove { display: none !important; }
</style>

<script>
    document.addEventListener("DOMContentLoaded", function() {
        // پیدا کردن و مخفی کردن متن "فرمت های مجاز" که بیرون از کادر مونده
        let elements = document.querySelectorAll('*');
        elements.forEach(el => {
            if (el.children.length === 0) { // فقط المان های برگ
                let txt = el.innerText || '';
                if (txt.includes('JPG') || txt.includes('PNG') || txt.includes('فرمت‌های مجاز')) {
                    el.classList.add('rogue-text-remove');
                    if(el.parentElement && el.parentElement.innerText.includes('JPG, PNG')) {
                        el.parentElement.classList.add('rogue-text-remove');
                    }
                }
            }
        });

        // زور زدن عرض 100 درصد به کادر آپلود
        let box = document.getElementById('main-upload-box');
        if (box) {
            box.style.setProperty('width', '100%', 'important');
            box.parentElement.style.setProperty('width', '100%', 'important');
        }
    });
</script>
"""

for file in glob.glob('templates/**/*.html', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'name="name"' in html:
        # پاک کردن کدهای تکراری قبلی
        html = re.sub(r'<style>\s*/\* زور زدن عرض 100 درصد.*?</script>', '', html, flags=re.DOTALL)
        
        # اضافه کردن کد جدید
        if '</body>' in html:
            html = html.replace('</body>', fix_css_js + '\n</body>')
        else:
            html += fix_css_js

        with open(file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ استایل زورگویانه عرض ۱۰۰٪ به {file} اعمال شد.")
