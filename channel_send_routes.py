from flask import Blueprint, render_template, request, redirect, session, jsonify
import os, sqlite3, requests, uuid, io
from PIL import Image
from database import get_shop_channels, add_shop_channel, delete_shop_channel, get_user_settings

channel_send_bp = Blueprint('channel_send', __name__)

def _uid(): return session.get('user_id')

def _get_token():
    conn = sqlite3.connect('panel.db', timeout=15)
    c = conn.cursor()
    c.execute("SELECT token FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    conn.close()
    return r[0] if r else None

@channel_send_bp.route('/panel/channel-send', methods=['GET', 'POST'])
def panel_channel_send():
    if not _uid(): return redirect('/panel/login')
    uid = _uid()
    msg = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_channel':
            ch = (request.form.get('channel_id') or '').strip().replace('@', '')
            add_shop_channel(uid, '@' + ch, request.form.get('title',''), request.form.get('tag',''))
            msg = ('ok', '✅ کانال اضافه شد')
        elif action == 'del_channel':
            delete_shop_channel(int(request.form.get('cid') or 0), uid)
            msg = ('ok', '✅ کانال حذف شد')
        elif action == 'send':
            ch_id = '@' + (request.form.get('target_channel') or '').strip().replace('@', '')
            text = (request.form.get('text') or '').strip()
            tag = (request.form.get('tag') or '').strip()
            final_text = f'{text}\n\n🏪 {tag}' if tag else text
            
            tok = _get_token()
            if not tok:
                msg = ('error', '❌ توکن ربات تنظیم نشده')
            else:
                img_file = request.files.get('image_file')
                try:
                    if img_file and img_file.filename != '':
                        img = Image.open(img_file).convert('RGB')
                        buf = io.BytesIO()
                        img.save(buf, format='JPEG', quality=85)
                        buf.seek(0)
                        
                        r1 = requests.post(f'https://botapi.rubika.ir/v3/{tok}/requestSendFile', json={'type': 'Image'}, timeout=20)
                        upload_url = r1.json()['data']['upload_url']
                        
                        r2 = requests.post(upload_url, files={'file': ('image.jpg', buf, 'image/jpeg')}, timeout=60)
                        file_id = r2.json()['data']['file_id']
                        
                        r3 = requests.post(f'https://botapi.rubika.ir/v3/{tok}/sendFile', json={'chat_id': ch_id, 'file_id': file_id, 'text': final_text}, timeout=30)
                        res = r3.json()
                    else:
                        r3 = requests.post(f'https://botapi.rubika.ir/v3/{tok}/sendMessage', json={'chat_id': ch_id, 'text': final_text}, timeout=20)
                        res = r3.json()
                        
                    if res.get('status') == 'OK':
                        msg = ('ok', f'✅ با موفقیت به {ch_id} ارسال شد')
                    else:
                        msg = ('error', f"❌ خطای روبیکا: {res.get('dev_message') or res}")
                except Exception as e:
                    msg = ('error', f'❌ خطا: {str(e)[:100]}')

    channels = get_shop_channels(uid)
    try: cs = get_user_settings(uid)
    except: cs = None
    
    return render_template('panel_channel_send.html', channels=channels, msg=msg, is_premium=True, current_settings=cs)


@channel_send_bp.route('/panel/channel-send/ai', methods=['POST'])
def channel_send_ai():
    try:
        from ai_service import enhance_for_channel
        return jsonify({'result': enhance_for_channel((request.json or {}).get('text', ''))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@channel_send_bp.route('/panel/channel-send/emoji', methods=['POST'])
def channel_send_emoji():
    try:
        from ai_service import suggest_emoji
        return jsonify({'emoji': suggest_emoji((request.json or {}).get('word', ''))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@channel_send_bp.route('/panel/channel-send/ai-image', methods=['POST'])
def channel_send_ai_image():
    try:
        prompt = (request.json or {}).get('prompt', '').strip()
        if not prompt: return jsonify({'error': 'پرامپت خالیه'}), 400

        import urllib.parse
        from ai_service import ask_ai
        
        system_msg = "Translate to English and make it a highly detailed, photorealistic architectural image prompt. Output ONLY English."
        enhanced = ask_ai(prompt, system_msg) or prompt
        
        final_prompt = f"{enhanced}, 8k, photorealistic, cinematic lighting, highly detailed"
        enc = urllib.parse.quote(final_prompt)
        
        url = f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=1024&model=flux-realism&nologo=true"
        r = requests.get(url, timeout=120)
        
        if r.status_code != 200:
            return jsonify({'error': 'سرور AI شلوغه، دوباره تلاش کن'}), 500
            
        fn = f'ai_{uuid.uuid4().hex[:8]}.jpg'
        path = os.path.join('static/uploads', fn)
        with open(path, 'wb') as f: f.write(r.content)
        
        return jsonify({'url': '/' + path})
    except Exception as e:
        return jsonify({'error': f'خطا: {str(e)}'}), 500

@channel_send_bp.route('/panel/channel-send/edit-image', methods=['POST'])
def channel_send_edit_image():
    try:
        prompt = request.form.get('prompt', '').strip()
        img_file = request.files.get('image')
        
        if not prompt or not img_file: 
            return jsonify({'error': 'عکس یا پرامپت ارسال نشده'}), 400

        import urllib.parse
        from ai_service import ask_ai

        # ۱. ترجمه و غنی‌سازی پرامپت با هوش مصنوعی
        print(f"DEBUG: Original prompt: {prompt}", flush=True)
        system_msg = """You are a professional AI image editor. Translate the user's request to English and expand it into a highly detailed prompt. Focus on the SPECIFIC CHANGES requested (e.g., lighting, background, colors). Output ONLY the English prompt."""
        enhanced = ask_ai(prompt, system_msg)
        
        if not enhanced or len(enhanced) < 5:
            enhanced = prompt
            
        final_prompt = f"{enhanced}, masterpiece, ultra-detailed, dramatic lighting, 8k resolution, photorealistic, high contrast"
        enc = urllib.parse.quote(final_prompt)
        print(f"DEBUG: Enhanced prompt: {final_prompt}", flush=True)

        # ۲. آپلود عکس به Catbox
        print("DEBUG: Uploading image to Catbox...", flush=True)
        files = {'fileToUpload': (img_file.filename, img_file.read(), img_file.mimetype)}
        data = {'reqtype': 'fileupload'}
        r_host = requests.post('https://catbox.moe/user/api.php', data=data, files=files, timeout=30)
        
        if r_host.status_code != 200 or not r_host.text.startswith('https://'):
            print(f"DEBUG: Upload failed: {r_host.text}", flush=True)
            return jsonify({'error': 'خطا در آپلود موقت عکس'}), 500
            
        public_url = r_host.text.strip()
        
        # ۳. ارسال به Pollinations با مدل Flux
        ai_url = f"https://image.pollinations.ai/prompt/{enc}?image={public_url}&model=flux&nologo=true&enhance=true&width=1024&height=1024"
        
        print("DEBUG: Requesting AI edit...", flush=True)
        r_ai = requests.get(ai_url, timeout=120)
        
        if r_ai.status_code != 200: 
            return jsonify({'error': 'سرور هوش مصنوعی شلوغه، دوباره تلاش کن'}), 500

        # ۴. ذخیره و بازگشت
        fn = f'edit_{uuid.uuid4().hex[:8]}.jpg'
        path = os.path.join('static/uploads', fn)
        with open(path, 'wb') as f: 
            f.write(r_ai.content)

        print(f"DEBUG: Edit successful: {fn}", flush=True)
        return jsonify({'url': '/' + path})
        
    except Exception as e:
        print(f"DEBUG ERROR EDIT: {str(e)}", flush=True)
        return jsonify({'error': f'خطا: {str(e)[:50]}'}), 500

@channel_send_bp.route('/panel/premium', methods=['GET', 'POST'])
def panel_premium():
    from database import get_premium, activate_premium
    if request.method == 'POST' and session.get('is_admin'):
        activate_premium(session['user_id'], 30)
        return redirect('/panel/premium')
    return render_template('panel_premium.html', premium=get_premium(session['user_id']))

# ============ BULK CSV UPLOAD ============
@channel_send_bp.route('/panel/products/upload-csv', methods=['GET', 'POST'])
def panel_upload_csv():
    if not _uid(): return redirect('/panel/login')
    import csv, io
    
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file and file.filename.endswith('.csv'):
            # خواندن فایل
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            reader = csv.DictReader(stream)
            
            conn = sqlite3.connect('panel.db')
            c = conn.cursor()
            count = 0
            
            try:
                for row in reader:
                    name = row.get('name')
                    price = int(row.get('price', 0))
                    cat = row.get('category', '')
                    unit = row.get('unit', 'عدد')
                    
                    c.execute("""INSERT INTO shop_products (shop_id, name, price, unit, category, available) 
                                 VALUES (?, ?, ?, ?, ?, 1)""", (_uid(), name, price, unit, cat))
                    count += 1
                conn.commit()
                msg = f'✅ {count} محصول با موفقیت اضافه شد'
            except Exception as e:
                msg = f'❌ خطا در خط {count+1}: {str(e)}'
            finally:
                conn.close()
        else:
            msg = '❌ فایل نامعتبر است (باید CSV باشد)'
            
        return render_template('panel_upload_csv.html', msg=msg)
        
    return render_template('panel_upload_csv.html')
