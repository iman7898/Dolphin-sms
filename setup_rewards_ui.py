import os

file_path = 'templates/customer_dashboard.html'
if not os.path.exists(file_path):
    print("⚠️ فایل customer_dashboard.html پیدا نشد!")
    exit()

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

if 'id="pointsModal"' not in html:
    # 1. کد HTML و CSS پنجره (Modal) و اسکریپت هوشمند برای باز کردنش
    modal_html = """
    <!-- ====== شروع پنجره جوایز دلفین ====== -->
    <style>
        #pointsModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,10,20,0.85); z-index: 9999; justify-content: center; align-items: center; backdrop-filter: blur(5px); font-family: Tahoma; }
        .points-modal-content { background: linear-gradient(135deg, #001a33, #003366); border: 2px solid #00d4ff; border-radius: 20px; padding: 25px; width: 90%; max-width: 380px; color: white; box-shadow: 0 0 30px rgba(0,212,255,0.4); position: relative; animation: popIn 0.3s ease-out; }
        @keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        .close-modal { position: absolute; top: 15px; left: 20px; font-size: 28px; cursor: pointer; color: #ff4d4d; font-weight: bold; transition: 0.2s; }
        .close-modal:hover { color: white; transform: scale(1.2); }
        .modal-header { text-align: center; margin-bottom: 20px; }
        .modal-header h2 { color: #00d4ff; margin: 0 0 10px 0; font-size: 22px; text-shadow: 0 0 10px rgba(0,212,255,0.5); }
        .modal-score { font-size: 45px; font-weight: bold; color: #ffd700; text-shadow: 0 0 15px rgba(255,215,0,0.4); }
        .rewards-list { list-style: none; padding: 0; margin: 0; }
        .rewards-list li { background: rgba(255,255,255,0.05); border: 1px solid rgba(0,212,255,0.2); padding: 12px 15px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }
        .rewards-list li:hover { background: rgba(0,212,255,0.1); transform: translateX(-5px); }
        .reward-title { font-size: 14px; color: #e0e0e0; }
        .reward-cost { background: #00d4ff; color: #001a33; padding: 5px 12px; border-radius: 8px; font-weight: bold; font-size: 13px; box-shadow: 0 0 10px rgba(0,212,255,0.4); }
    </style>

    <div id="pointsModal">
        <div class="points-modal-content">
            <span class="close-modal" onclick="document.getElementById('pointsModal').style.display='none'">&times;</span>
            <div class="modal-header">
                <h2>🏆 باشگاه مشتریان دلفین</h2>
                <div class="modal-score">⭐ {{ points or 0 }}</div>
                <p style="color:#aaa; font-size:12px; margin-top:5px;">با هر ۱۰,۰۰۰ تومان خرید، ۱ امتیاز بگیرید!</p>
            </div>
            
            <ul class="rewards-list">
                <li>
                    <span class="reward-title">🚚 ارسال رایگان سفارش</span>
                    <span class="reward-cost">۵۰۰ امتیاز</span>
                </li>
                <li>
                    <span class="reward-title">🎟️ کد تخفیف ۱۰٪</span>
                    <span class="reward-cost">۱۰۰۰ امتیاز</span>
                </li>
                <li>
                    <span class="reward-title">🎁 هدیه ویژه مغازه‌دار</span>
                    <span class="reward-cost">۲۰۰۰ امتیاز</span>
                </li>
            </ul>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            // پیدا کردن هوشمندانه باکس ستاره و امتیاز در بالای صفحه
            const elements = document.querySelectorAll('div, span, a, p');
            elements.forEach(el => {
                if (el.textContent.includes('⭐') && el.textContent.trim().length < 10) {
                    el.style.cursor = 'pointer';
                    // افکت نئون موقع هاور
                    el.addEventListener('mouseenter', () => el.style.transform = 'scale(1.1)');
                    el.addEventListener('mouseleave', () => el.style.transform = 'scale(1)');
                    
                    el.onclick = function(e) {
                        e.preventDefault();
                        document.getElementById('pointsModal').style.display = 'flex';
                    };
                }
            });
        });
    </script>
    <!-- ====== پایان پنجره جوایز دلفین ====== -->
    """
    
    # اضافه کردن به آخر فایل قبل از تگ body
    if '</body>' in html:
        html = html.replace('</body>', modal_html + '\n</body>')
    else:
        html += modal_html
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ پنجره جوایز و امتیازات (UI) با موفقیت به پنل مشتری اضافه شد.")
else:
    print("ℹ️ پنجره جوایز از قبل وجود دارد.")
