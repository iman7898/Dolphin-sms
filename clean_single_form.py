import re, glob

new_form = """
<form method="POST" enctype="multipart/form-data" action="/panel/add-product" style="margin-top:15px;">
    <div style="margin-bottom: 20px; padding: 20px; background: #031526; border: 2px dashed #00ff88; border-radius: 15px; text-align: center; cursor: pointer; position: relative; min-height: 180px; display: flex; flex-direction: column; justify-content: center; align-items: center;" id="main-upload-box" onclick="document.getElementById('imgInput').click()">
        
        <div id="preview-container" style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; width: 100%;"></div>
        
        <div id="upload-text" style="pointer-events: none;">
            <div style="font-size: 50px; margin-bottom: 10px; filter: drop-shadow(0 0 10px rgba(0,255,136,0.5));">📸</div>
            <div style="color: #00ff88; font-weight: bold; font-size: 16px; font-family: Tahoma;">برای آپلود عکس کلیک کنید</div>
            <div style="color: #6688aa; font-size: 12px; margin-top: 5px; font-family: Tahoma;">(می‌توانید چند عکس انتخاب کنید)</div>
        </div>
        
        <div id="add-more-btn" style="display: none; margin-top: 15px; background: #00ff88; color: #031526; width: 40px; height: 40px; border-radius: 50%; font-size: 26px; font-weight: bold; line-height: 38px; box-shadow: 0 0 15px rgba(0,255,136,0.5); pointer-events: auto; cursor: pointer;">+</div>
    </div>
    
    <input type="file" id="imgInput" name="image" accept="image/*" multiple style="display: none;">
    
    <div style="margin-bottom: 15px; text-align:right;">
        <label style="color: white; display:block; margin-bottom:8px; font-family:Tahoma; font-weight:bold;">📦 نام محصول</label>
        <input type="text" name="name" placeholder="مثلاً سیب قرمز" style="width:100%; padding:15px; background:#021222; border:1.5px solid #0066ff; border-radius:12px; color:white; font-family:Tahoma; outline:none; box-sizing:border-box;" required>
    </div>
    <div style="margin-bottom: 15px; text-align:right;">
        <label style="color: white; display:block; margin-bottom:8px; font-family:Tahoma; font-weight:bold;">💰 قیمت (تومان)</label>
        <input type="number" name="price" placeholder="مثلاً ۵۰۰۰۰" style="width:100%; padding:15px; background:#021222; border:1.5px solid #0066ff; border-radius:12px; color:white; font-family:Tahoma; outline:none; box-sizing:border-box;" required>
    </div>
    <div style="margin-bottom: 15px; text-align:right;">
        <label style="color: white; display:block; margin-bottom:8px; font-family:Tahoma; font-weight:bold;">📝 توضیحات</label>
        <textarea name="description" placeholder="توضیح کوتاه درباره محصول..." style="width:100%; padding:15px; background:#021222; border:1.5px solid #0066ff; border-radius:12px; color:white; font-family:Tahoma; height:100px; outline:none; box-sizing:border-box; resize:none;"></textarea>
    </div>
    <button type="submit" style="width:100%; padding:15px; background:linear-gradient(90deg, #00ff88, #00d4ff); color:#021222; border:none; border-radius:15px; font-weight:bold; font-size:16px; font-family:Tahoma; cursor:pointer; box-shadow:0 4px 15px rgba(0,180,219,0.3);">💾 ثبت محصول</button>
</form>

<script>
    document.addEventListener("DOMContentLoaded", function() {
        // مخفی کردن دکمه‌های رنگی قبلی
        document.querySelectorAll('div').forEach(function(d) {
            if (d.innerText && d.innerText.includes('قوی‌سازی متن') && !d.innerText.includes('نام محصول')) {
                d.style.setProperty('display', 'none', 'important');
            }
        });

        let selectedFiles = [];
        let input = document.getElementById('imgInput');
        
        document.getElementById('add-more-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            input.click();
        });

        input.addEventListener('change', function(e) {
            let files = Array.from(e.target.files);
            selectedFiles = selectedFiles.concat(files);
            this.value = '';
            updatePreviews();
        });

        function updatePreviews() {
            let container = document.getElementById('preview-container');
            container.innerHTML = '';
            selectedFiles.forEach((file, index) => {
                let reader = new FileReader();
                reader.onload = function(e) {
                    let div = document.createElement('div');
                    div.style.cssText = 'position: relative; width: 80px; height: 80px;';
                    
                    let img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.cssText = 'width: 100%; height: 100%; object-fit: cover; border-radius: 10px; border: 2px solid #00ff88;';
                    
                    let delBtn = document.createElement('div');
                    delBtn.innerHTML = '&times;';
                    delBtn.style.cssText = 'position: absolute; top: -5px; right: -5px; background: #ff4d4d; color: white; width: 20px; height: 20px; border-radius: 50%; text-align: center; line-height: 20px; font-weight: bold; cursor: pointer; font-size: 14px;';
                    delBtn.onclick = function(e) {
                        e.stopPropagation();
                        selectedFiles.splice(index, 1);
                        updatePreviews();
                    };
                    
                    div.appendChild(img);
                    div.appendChild(delBtn);
                    container.appendChild(div);
                };
                reader.readAsDataURL(file);
            });

            if (selectedFiles.length > 0) {
                document.getElementById('upload-text').style.display = 'none';
                document.getElementById('add-more-btn').style.display = 'block';
            } else {
                document.getElementById('upload-text').style.display = 'block';
                document.getElementById('add-more-btn').style.display = 'none';
            }
        }
    });
</script>
"""

for file in glob.glob('templates/**/*.html', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'name="name"' in html:
        # 1. پاک کردن تمام فرم‌های اضافه شده
        html = re.sub(r'<form[^>]*action=["\']/panel/add-product["\'][^>]*>.*?</form>', '', html, flags=re.DOTALL)
        
        # 2. پاک کردن کادرهای آپلود قدیمی
        html = re.sub(r'<div[^>]*>.*?برای آپلود عکس.*?</div>', '', html, flags=re.DOTALL)
        
        # 3. اضافه کردن فقط یک فرم تمیز
        if '</body>' in html:
            html = html.replace('</body>', new_form + '\n</body>')
        else:
            html += new_form

        with open(file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ فایل {file} تمیز شد.")
