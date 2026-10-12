(function() {
    if (window.__prem_loaded) return;
    window.__prem_loaded = true;

    // CSS
    var style = document.createElement('style');
    style.textContent = `
    .prem-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        z-index: 99999998;
        justify-content: center;
        align-items: center;
        padding: 20px;
        font-family: Vazirmatn, Tahoma, sans-serif;
        direction: rtl;
    }
    .prem-overlay.show {
        display: flex;
        animation: premFade 0.25s ease;
    }
    @keyframes premFade { from{opacity:0} to{opacity:1} }
    .prem-box {
        background: linear-gradient(135deg, #1a1200 0%, #0a0800 100%);
        border: 2px solid #ffbe0b;
        border-radius: 20px;
        padding: 26px 22px;
        max-width: 420px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        text-align: center;
        box-shadow: 0 0 60px rgba(255,190,11,0.4), 0 30px 80px rgba(0,0,0,0.9), inset 0 0 30px rgba(255,190,11,0.05);
        animation: premPop 0.35s cubic-bezier(0.34,1.56,0.64,1);
        position: relative;
    }
    .prem-box::before {
        content: '';
        position: absolute;
        top: -1px; left: 20%; right: 20%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #ffbe0b, #ff6b00, transparent);
        border-radius: 2px;
        box-shadow: 0 0 15px #ffbe0b;
    }
    @keyframes premPop {
        from { transform: scale(0.85) translateY(20px); opacity: 0; }
        to { transform: scale(1) translateY(0); opacity: 1; }
    }
    .prem-star {
        font-size: 60px;
        color: #ffbe0b;
        filter: drop-shadow(0 0 25px #ffbe0b);
        animation: premStar 3s ease-in-out infinite;
        display: inline-block;
    }
    @keyframes premStar {
        0%,100% { transform: rotate(-8deg) scale(1); }
        50% { transform: rotate(8deg) scale(1.1); }
    }
    .prem-title {
        font-size: 20px;
        font-weight: 900;
        color: #ffbe0b;
        text-shadow: 0 0 20px rgba(255,190,11,0.8);
        margin: 12px 0 16px;
        letter-spacing: 1px;
    }
    .prem-active {
        background: linear-gradient(135deg, rgba(0,255,157,0.15), rgba(0,200,130,0.08));
        border: 2px solid #00ff9d;
        border-radius: 14px;
        padding: 18px;
        margin: 16px 0;
        box-shadow: 0 0 25px rgba(0,255,157,0.3);
    }
    .prem-active-title {
        font-size: 16px;
        font-weight: 900;
        color: #00ff9d;
        text-shadow: 0 0 12px rgba(0,255,157,0.8);
        margin-bottom: 6px;
    }
    .prem-admin {
        background: linear-gradient(135deg, rgba(255,0,110,0.15), rgba(255,190,11,0.1));
        border: 2px solid #ff006e;
        border-radius: 14px;
        padding: 18px;
        margin: 16px 0;
        box-shadow: 0 0 25px rgba(255,0,110,0.3);
    }
    .prem-admin-title {
        font-size: 16px;
        font-weight: 900;
        color: #ff006e;
        text-shadow: 0 0 12px rgba(255,0,110,0.8);
        margin-bottom: 6px;
    }
    .prem-inactive {
        background: linear-gradient(135deg, rgba(255,190,11,0.1), rgba(255,100,0,0.05));
        border: 2px dashed #ffbe0b;
        border-radius: 14px;
        padding: 18px;
        margin: 16px 0;
        text-align: right;
    }
    .prem-inactive-title {
        font-size: 16px;
        font-weight: 900;
        color: #ffbe0b;
        text-shadow: 0 0 12px rgba(255,190,11,0.8);
        margin-bottom: 10px;
        text-align: center;
    }
    .prem-feat {
        font-size: 12.5px;
        color: #fff;
        padding: 7px 12px;
        background: rgba(0,0,0,0.3);
        border-radius: 8px;
        border-right: 3px solid #ffbe0b;
        margin-bottom: 6px;
        text-align: right;
    }
    .prem-pricing {
        background: rgba(0,0,0,0.4);
        border-radius: 14px;
        padding: 14px;
        margin: 16px 0;
        border: 1px solid rgba(255,190,11,0.3);
    }
    .prem-pricing-title {
        font-size: 13px;
        font-weight: 800;
        color: #ffbe0b;
        margin-bottom: 12px;
        text-align: center;
    }
    .prem-pricing-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    .prem-plan {
        padding: 12px 8px;
        background: rgba(255,190,11,0.06);
        border: 2px solid rgba(255,190,11,0.25);
        color: #fff;
        border-radius: 12px;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.3s;
        width: 100%;
    }
    .prem-plan:hover { border-color: #ffbe0b; background: rgba(255,190,11,0.12); transform: translateY(-2px); }
    .prem-plan.active {
        border-color: #ffbe0b;
        background: linear-gradient(135deg, rgba(255,190,11,0.2), rgba(255,100,0,0.15));
        box-shadow: 0 0 20px rgba(255,190,11,0.4);
    }
    .prem-plan-dur { font-size: 13px; font-weight: 900; color: #ffbe0b; margin-bottom: 4px; }
    .prem-plan-price { font-size: 11px; color: #e8edf5; }
    .prem-buy {
        width: 100%;
        padding: 16px;
        margin-top: 14px;
        background: linear-gradient(135deg, #ffbe0b, #ff6b00);
        color: #000;
        border: none;
        border-radius: 14px;
        font-size: 16px;
        font-weight: 900;
        font-family: inherit;
        cursor: pointer;
        box-shadow: 0 0 30px rgba(255,190,11,0.6), 0 8px 25px rgba(255,100,0,0.4);
        transition: all 0.3s;
    }
    .prem-buy:hover, .prem-buy:active {
        transform: translateY(-3px);
        box-shadow: 0 0 50px rgba(255,190,11,0.9), 0 12px 35px rgba(255,100,0,0.6);
    }
    .prem-close {
        width: 100%;
        padding: 12px;
        margin-top: 12px;
        background: rgba(255,255,255,0.05);
        color: #7a8599;
        border: 2px solid rgba(255,255,255,0.15);
        border-radius: 12px;
        font-size: 14px;
        font-weight: 700;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.25s;
    }
    .prem-close:hover { background: rgba(255,255,255,0.1); color: #fff; }
    `;
    document.head.appendChild(style);

    // HTML
    var overlay = document.createElement('div');
    overlay.className = 'prem-overlay';
    overlay.innerHTML = '<div class="prem-box" id="premBoxContent"></div>';
    document.body.appendChild(overlay);

    var plan = {days: 30, price: 200000};

    window.openPremiumModal = function() {
        var isAdmin = {{ 'true' if is_admin else 'false' }} || window.location.pathname.indexOf('/admin/') !== -1;
        var isPrem = window.__userIsPremium || false;

        var html = '<div class="prem-star">⭐</div>';
        html += '<div class="prem-title">اشتراک پرمیوم</div>';

        if (isAdmin) {
            html += '<div class="prem-admin">';
            html += '<div class="prem-admin-title">👑 Creator</div>';
            html += '<div style="color:#ffbe0b;font-size:12px">دسترسی کامل رایگان</div>';
            html += '</div>';
        } else if (isPrem) {
            html += '<div class="prem-active">';
            html += '<div class="prem-active-title">✅ پرمیوم فعال است</div>';
            html += '</div>';
        } else {
            html += '<div class="prem-inactive">';
            html += '<div class="prem-inactive-title">⛔ پرمیوم فعال نیست</div>';
            html += '<div style="color:#7a8599;font-size:12px;text-align:center;margin-bottom:10px">با ارتقاء، این امکانات فعال می‌شن:</div>';
            html += '<div class="prem-feat">🎨 شخصی‌سازی بیشتر پنل</div>';
            html += '<div class="prem-feat">🖼 پس‌زمینه‌های ویژه</div>';
            html += '<div class="prem-feat">🔤 فونت‌های حرفه‌ای پرمیوم</div>';
            html += '<div class="prem-feat">🤖 هوش مصنوعی نامحدود</div>';
            html += '<div class="prem-feat">✨ افکت‌های ویژه رابط</div>';
            html += '<div class="prem-feat">🎯 دسترسی زودتر به قابلیت‌های جدید</div>';
            html += '</div>';

            html += '<div class="prem-pricing">';
            html += '<div class="prem-pricing-title">💰 انتخاب اشتراک</div>';
            html += '<div class="prem-pricing-grid">';
            html += '<button class="prem-plan active" onclick="window.__premSelect(this,30,200000)"><div class="prem-plan-dur">۱ ماه</div><div class="prem-plan-price">۲۰۰,۰۰۰ تومان</div></button>';
            html += '<button class="prem-plan" onclick="window.__premSelect(this,90,500000)"><div class="prem-plan-dur">۳ ماه</div><div class="prem-plan-price">۵۰۰,۰۰۰ تومان</div></button>';
            html += '<button class="prem-plan" onclick="window.__premSelect(this,150,750000)"><div class="prem-plan-dur">۵ ماه</div><div class="prem-plan-price">۷۵۰,۰۰۰ تومان</div></button>';
            html += '<button class="prem-plan" onclick="window.__premSelect(this,210,950000)"><div class="prem-plan-dur">۷ ماه</div><div class="prem-plan-price">۹۵۰,۰۰۰ تومان</div></button>';
            html += '<button class="prem-plan" onclick="window.__premSelect(this,365,1500000)" style="grid-column: 1 / -1;"><div class="prem-plan-dur">۱ سال</div><div class="prem-plan-price">۱,۵۰۰,۰۰۰ تومان</div></button>';
            html += '</div>';
            html += '</div>';

            html += '<button class="prem-buy" onclick="window.__premBuy()">💳 خرید و پرداخت</button>';
        }

        html += '<button class="prem-close" onclick="window.closePremiumModal()">بستن</button>';

        document.getElementById('premBoxContent').innerHTML = html;
        overlay.classList.add('show');
    };

    window.closePremiumModal = function() {
        overlay.classList.remove('show');
    };

    window.__premSelect = function(btn, days, price) {
        var all = document.querySelectorAll('.prem-plan');
        for (var i = 0; i < all.length; i++) all[i].classList.remove('active');
        btn.classList.add('active');
        plan = {days: days, price: price};
    };

    window.__premBuy = function() {
        closePremiumModal();
        if (window.alert) {
            window.alert('اشتراک ' + plan.days + ' روزه\nمبلغ: ' + plan.price.toLocaleString('fa-IR') + ' تومان\n\nبا ادمین چت کنید تا فعال شود.');
        }
        setTimeout(function() {
            var base = window.location.pathname.indexOf('/admin/') !== -1 ? '/admin/chat' : '/panel/chat';
            window.location.href = base;
        }, 2000);
    };

    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) window.closePremiumModal();
    });
})();
