import re, glob

new_form = """
<form method="POST" enctype="multipart/form-data" action="/panel/add-product">
    <div style="margin-bottom: 20px; padding: 30px 20px; background: #031526; border: 2px dashed #00ff88; border-radius: 15px; text-align: center; cursor: pointer; position: relative; overflow: hidden; min-height: 180px; display: flex; flex-direction: column; justify-content: center; align-items: center;" onclick="document.getElementById('imgInput').click()">
        <img id="imgPreview" style="display:none; width: 100%; height: 100%; object-fit: cover; position: absolute; top:0; left:0; border-radius: 13px;" />
        <div id="upload-text" style="position: relative; z-index: 2; pointer-events: none;">
            <div style="font-size: 50px; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(0,255,136,0.5));">📸</div>
            <div style="color: #00ff88; font-weight: bold; font-size: 18px; font-family: Tahoma;">برای آپلود عکس محصول کلیک کنید</div>
            <div style="color: #6688aa; font-size: 12px; margin-top: 8px; font-family: Tahoma;">(فرمت JPG, PNG)</div>
        </div>
    </div>
    <input type="file" id="imgInput" name="image" accept="image/*" style="display: none;" onchange="
        let file = this.files[0];
        if(file){
            let reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('imgPreview').src = e.target.result;
                document.getElementById('imgPreview').style.display = 'block';
                document.getElementById('upload-text').style.display = 'none';
            }
            reader.readAsDataURL(file);
        }
    ">

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
"""

for file in glob.glob('templates/**/*.html', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()

    # پیدا کردن فرم محصول (با رجکس بر اساس فیلد نام محصول)
    if 'name="name"' in html or "name='name'" in html:
        pattern = r'<form[^>]*>(?:(?!</form>).)*?(?:name=["\']name["\'])(?:(?!</form>).)*?</form>'
        
        if re.search(pattern, html, flags=re.DOTALL):
            # جایگزینی فرم قدیمی با فرم جدید و سالم
            html = re.sub(pattern, new_form, html, flags=re.DOTALL)
            
            # پاک کردن کدهای مزخرف قبلی
            html = re.sub(r'<!-- === IMAGE UPLOAD PREVIEW === -->.*?<!-- === IMAGE UPLOAD PREVIEW END === -->', '', html, flags=re.DOTALL)
            html = re.sub(r'<!-- REMOVE_AI_BUTTONS_SCRIPT -->.*?<!-- REMOVE_AI_BUTTONS_SCRIPT -->', '', html, flags=re.DOTALL)
            
            with open(file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ فرم محصول در {file} به طور کامل و تمیز بازنویسی شد.")
