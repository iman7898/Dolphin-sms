"""📢 ارسال به کانال + AI"""
from flask import Blueprint, render_template, request, redirect, session, flash
import os, sqlite3, requests as _rq

channel_send_bp = Blueprint('channel_send', __name__)

UPLOAD_DIR = 'static/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _uid(): return session.get('user_id')

def _get_token():
    conn = sqlite3.connect('panel.db', timeout=15)
    c = conn.cursor()
    c.execute("SELECT token FROM admin_bots WHERE active=1 AND token!='' ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    conn.close()
    return r[0] if r else None


@channel_send_bp.route('/panel/channel-send/ai', methods=['POST'])
def channel_send_ai():
    """قوی‌سازی متن با AI"""
    if not _uid():
        return {'error': 'not logged in'}, 401
    from database import is_premium
    if not is_premium(_uid()):
        return {'error': 'پرمیوم نیستی'}, 403
    text = (request.json or {}).get('text', '')
    if not text:
        return {'error': 'متن خالیه'}, 400
    from ai_service import enhance_for_channel
    result = enhance_for_channel(text)
    if not result:
        return {'error': 'AI جواب نداد'}, 500
    return {'result': result}


@channel_send_bp.route('/panel/channel-send/emoji', methods=['POST'])
def channel_send_emoji():
    """پیشنهاد ایموجی"""
    if not _uid():
        return {'error': 'not logged in'}, 401
    word = (request.json or {}).get('word', '')
    from ai_service import suggest_emoji
    emoji = suggest_emoji(word)
    return {'emoji': emoji}


@channel_send_bp.route('/panel/channel-send/upload', methods=['POST'])
def channel_send_upload():
    """آپلود عکس"""
    if not _uid():
        return {'error': 'not logged in'}, 401
    from database import is_premium
    if not is_premium(_uid()):
        return {'error': 'پرمیوم نیستی'}, 403
    if 'image' not in request.files:
        return {'error': 'عکسی نبود'}, 400
    f = request.files['image']
    if not f.filename:
        return {'error': 'اسم فایل خالیه'}, 400
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
        return {'error': 'فرمت پشتیبانی نمیشه'}, 400
    import time
    fn = f'ch_{_uid()}_{int(time.time())}.{ext}'
    path = os.path.join(UPLOAD_DIR, fn)
    f.save(path)
    return {'url': '/' + path}


@channel_send_bp.route('/panel/channel-send/send-photo', methods=['POST'])
def channel_send_photo():
    """ارسال عکس به کانال"""
    if not _uid():
        return {'error': 'not logged in'}, 401
    from database import is_premium
    if not is_premium(_uid()):
        return {'error': 'پرمیوم نیستی'}, 403
    tok = _get_token()
    if not tok:
        return {'error': 'توکن ربات نیست'}, 500
    data = request.json or {}
    ch = (data.get('channel') or '').strip()
    img_url = (data.get('image') or '').strip()
    caption = (data.get('caption') or '').strip()
    if not ch or not img_url:
        return {'error': 'کانال یا عکس نیست'}, 400
    # تبدیل URL نسبی به مطلق
    if img_url.startswith('/'):
        # برای روبیکا نیاز به URL عمومی یا آپلود
        pass
    try:
        r = _rq.post(f'https://botapi.rubika.ir/v3/{tok}/sendPhoto?v=3.6',
                     json={'chat_id': ch, 'photo': img_url, 'caption': caption},
                     timeout=30)
        j = r.json()
        if j.get('status') == 'OK':
            return {'ok': True, 'result': j}
        return {'error': j.get('dev_message') or j.get('message') or 'خطا'}
    except Exception as e:
        return {'error': str(e)[:200]}


@channel_send_bp.route('/panel/premium', methods=['GET', 'POST'])
def panel_premium():
    """صفحه پریمیوم"""
    if not _uid():
        return redirect('/panel/login')
    from database import get_premium, activate_premium
    uid = _uid()
    p = get_premium(uid)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'activate' and session.get('is_admin'):
            activate_premium(uid, 30)
            flash('✅ ۳۰ روز پریمیوم فعال شد', 'ok')
        return redirect('/panel/premium')
    return render_template('panel_premium.html', premium=p)

@channel_send_bp.route('/panel/channel-send/send-photo', methods=['POST'])
def channel_send_photo():
    """ارسال عکس به کانال"""
    if not _uid():
        return {'error': 'not logged in'}, 401
    from database import is_premium
    if not is_premium(_uid()):
        return {'error': 'پرمیوم نیستی'}, 403
    tok = _get_token()
    if not tok:
        return {'error': 'توکن ربات نیست'}, 500
    data = request.json or {}
    ch = (data.get('channel') or '').strip()
    img_url = (data.get('image') or '').strip()
    caption = (data.get('caption') or '').strip()
    if not ch or not img_url:
        return {'error': 'کانال یا عکس نیست'}, 400
    try:
        local_path = img_url.lstrip('/')
        if not os.path.exists(local_path):
            return {'error': f'فایل پیدا نشد: {local_path}'}, 400
        # آپلود با multipart
        with open(local_path, 'rb') as f:
            fname = os.path.basename(local_path)
            files = {'file': (fname, f, 'image/jpeg')}
            up = _rq.post(f'https://botapi.rubika.ir/v3/{tok}/uploadFile?v=3.6',
                          files=files, timeout=60)
        upj = up.json()
        if upj.get('status') != 'OK':
            return {'error': 'آپلود: ' + str(upj.get('dev_message') or upj.get('message') or upj)[:200]}
        file_id = (upj.get('data', {}).get('file_id') or
                   upj.get('data', {}).get('fileId') or
                   upj.get('data', {}).get('file', {}).get('id'))
        if not file_id:
            return {'error': 'file_id نیومد: ' + str(upj)[:300]}
        # ارسال با file_id
        r = _rq.post(f'https://botapi.rubika.ir/v3/{tok}/sendPhoto?v=3.6',
                     json={'chat_id': ch, 'photo': file_id, 'caption': caption},
                     timeout=30)
        j = r.json()
        if j.get('status') == 'OK':
            return {'ok': True, 'file_id': file_id, 'result': j}
        return {'error': j.get('dev_message') or j.get('message') or 'خطا', 'detail': str(j)[:200]}
    except Exception as e:
        return {'error': str(e)[:300]}

@channel_send_bp.route('/panel/channel-send/send-photo', methods=['POST'])
def channel_send_photo():
    """ارسال عکس به کانال — روش درست"""
    if not _uid():
        return {'error': 'not logged in'}, 401
    from database import is_premium
    if not is_premium(_uid()):
        return {'error': 'پرمیوم نیستی'}, 403
    tok = _get_token()
    if not tok:
        return {'error': 'توکن ربات نیست'}, 500
    data = request.json or {}
    ch = (data.get('channel') or '').strip()
    img_url = (data.get('image') or '').strip()
    caption = (data.get('caption') or '').strip()
    if not ch or not img_url:
        return {'error': 'کانال یا عکس نیست'}, 400
    local_path = img_url.lstrip('/')
    if not os.path.exists(local_path):
        return {'error': f'فایل پیدا نشد: {local_path}'}, 400
    from rubika_file import upload_and_send_file
    result = upload_and_send_file(tok, ch, local_path, caption)
    if result.get('status') == 'OK':
        return {'ok': True, 'result': result}
    return {'error': result.get('message') or 'خطا'}

