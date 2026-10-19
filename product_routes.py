from flask import Blueprint, render_template, request, redirect, session, jsonify
import sqlite3, os, uuid, requests, urllib.parse

product_bp = Blueprint('product', __name__)

def _uid(): return session.get('user_id')

@product_bp.route('/panel/add-product', methods=['GET', 'POST'])
def add_product():
    if not _uid(): return redirect('/panel/login')
    uid = _uid()
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        desc = request.form.get('description', '')
        img = request.form.get('image', '')
        
        if name and price:
            conn = sqlite3.connect('panel.db')
            c = conn.cursor()
            c.execute("INSERT INTO shop_products (shop_id, name, price, description, image) VALUES (?,?,?,?,?)",
                      (uid, name, price, desc, img))
            conn.commit()
            conn.close()
            return redirect('/panel/dashboard')
            
    return render_template('panel_add_product.html')

@product_bp.route('/panel/api/ai-image', methods=['POST'])
def ai_image():
    if not _uid(): return jsonify({'error': 'login'}), 401
    prompt = request.json.get('prompt', '')
    
    try:
        final_prompt = f"{prompt}, professional product photography, white background, high resolution, 4k"
        enc = urllib.parse.quote(final_prompt)
        url = f"https://image.pollinations.ai/prompt/{enc}?width=800&height=800&nologo=true"
        
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            fn = f'ai_prod_{uuid.uuid4().hex[:8]}.jpg'
            path = os.path.join('static/uploads', fn)
            os.makedirs('static/uploads', exist_ok=True)
            with open(path, 'wb') as f:
                f.write(r.content)
            return jsonify({'url': '/' + path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    return jsonify({'error': 'خطا در ساخت عکس'}), 500
