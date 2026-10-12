(function() {
    if (window.__ca_loaded) return;
    window.__ca_loaded = true;
    var style = document.createElement('style');
    style.textContent = '.ca-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.88);backdrop-filter:blur(14px);z-index:99999999;justify-content:center;align-items:center;padding:20px;font-family:Vazirmatn,Tahoma,sans-serif;direction:rtl}.ca-overlay.ca-show{display:flex}.ca-box{background:linear-gradient(135deg,#0a0f14,#061018);border:2px solid #00ff9d;border-radius:20px;padding:26px 22px;max-width:400px;width:100%;text-align:center;box-shadow:0 0 60px rgba(0,255,157,0.4);position:relative}.ca-box::before{content:chr(34)chr(34);position:absolute;top:-1px;left:20%;right:20%;height:2px;background:linear-gradient(90deg,transparent,#00ff9d,#00d4ff,transparent);border-radius:2px}.ca-icon{font-size:54px;margin-bottom:12px;color:#00ff9d;filter:drop-shadow(0 0 22px #00ff9d)}.ca-title{font-size:18px;font-weight:900;color:#00ff9d;margin-bottom:12px}.ca-text{font-size:14px;color:#e8edf5;line-height:1.8;margin-bottom:20px}.ca-input{width:100%;padding:12px;background:rgba(0,20,10,0.8);border:2px solid rgba(0,255,157,0.4);border-radius:10px;color:#fff;font-family:inherit;font-size:14px;margin-bottom:16px;box-sizing:border-box}.ca-actions{display:flex;gap:10px}.ca-btn{flex:1;padding:13px;font-size:14px;font-weight:800;font-family:inherit;border-radius:12px;cursor:pointer;border:2px solid}.ca-cancel{background:rgba(255,255,255,0.05);color:#7a8599;border-color:rgba(255,255,255,0.15)}.ca-ok{background:rgba(0,255,157,0.15);color:#00ff9d;border-color:#00ff9d}.ca-ok:hover{background:#00ff9d;color:#000}html.ca-is-admin .ca-box{border-color:#ff006e;box-shadow:0 0 60px rgba(255,0,110,0.4)}html.ca-is-admin .ca-icon{color:#ff006e;filter:drop-shadow(0 0 22px #ff006e)}html.ca-is-admin .ca-title{color:#ff006e}html.ca-is-admin .ca-ok{background:rgba(255,0,110,0.15);color:#ff006e;border-color:#ff006e}html.ca-is-admin .ca-ok:hover{background:#ff006e;color:#fff}';
    document.head.appendChild(style);
    if (window.location.pathname.indexOf('/admin/') !== -1) document.documentElement.classList.add('ca-is-admin');
    var overlay = document.createElement('div');
    overlay.className = 'ca-overlay';
    overlay.innerHTML = '<div class=chr(34)ca-boxchr(34)><div class=chr(34)ca-iconchr(34) id=chr(34)caIconchr(34)></div><div class=chr(34)ca-titlechr(34) id=chr(34)caTitlechr(34)></div><div class=chr(34)ca-textchr(34) id=chr(34)caTextchr(34)></div><div id=chr(34)caInputWrapchr(34)></div><div class=chr(34)ca-actionschr(34) id=chr(34)caActionschr(34)></div></div>';
    document.body.appendChild(overlay);
    var cb = null;
    function close(r) { overlay.classList.remove('ca-show'); var f = cb; cb = null; if (f) f(r); }
    window.__caClose = close;
    window.alert = function(m, t) { document.getElementById('caIcon').textContent = 'M'; document.getElementById('caTitle').textContent = t || 'Payam'; document.getElementById('caText').textContent = String(m); document.getElementById('caInputWrap').innerHTML = ''; document.getElementById('caActions').innerHTML = '<button class=chr(34)ca-btn ca-okchr(34) onclick=chr(34)window.__caClose(true)chr(34)>Bash</button>'; overlay.classList.add('ca-show'); };
    window.confirm = function(m, t) { document.getElementById('caIcon').textContent = '!'; document.getElementById('caTitle').textContent = t || 'Taeed'; document.getElementById('caText').textContent = String(m); document.getElementById('caInputWrap').innerHTML = ''; document.getElementById('caActions').innerHTML = '<button class=chr(34)ca-btn ca-cancelchr(34) onclick=chr(34)window.__caClose(false)chr(34)>Enseraf</button><button class=chr(34)ca-btn ca-okchr(34) onclick=chr(34)window.__caClose(true)chr(34)>Taeed</button>'; overlay.classList.add('ca-show'); return false; };
    window.prompt = function(m, d, t) { document.getElementById('caIcon').textContent = 'P'; document.getElementById('caTitle').textContent = t || 'Vorudi'; document.getElementById('caText').textContent = String(m); document.getElementById('caInputWrap').innerHTML = '<input type=chr(34)textchr(34) class=chr(34)ca-inputchr(34) id=chr(34)caInputchr(34) value=chr(34)' + (d || '') + 'chr(34)>'; document.getElementById('caActions').innerHTML = '<button class=chr(34)ca-btn ca-cancelchr(34) onclick=chr(34)window.__caClose(null)chr(34)>Enseraf</button><button class=chr(34)ca-btn ca-okchr(34) onclick=chr(34)window.__caPromptOK()chr(34)>Taeed</button>'; overlay.classList.add('ca-show'); setTimeout(function(){var i=document.getElementById('caInput');if(i)i.focus();},100); return null; };
    window.__caPromptOK = function() { var i = document.getElementById('caInput'); close(i ? i.value : null); };
    overlay.addEventListener('click', function(e) { if (e.target === overlay) close(null); });
    document.addEventListener('submit', function(e) {
        var f = e.target;
        if (f.tagName !== 'FORM') return;
        var o = f.getAttribute('onsubmit') || '';
        if (o.indexOf('confirm(') === -1) return;
        e.preventDefault();
        e.stopPropagation();
        var m = o.match(/confirm\(.([^.]+).\)/);
        var msg = m ? m[1] : 'Motmaeni?';
        document.getElementById('caIcon').textContent = '!';
        document.getElementById('caTitle').textContent = 'Taeed';
        document.getElementById('caText').textContent = msg;
        document.getElementById('caInputWrap').innerHTML = '';
        document.getElementById('caActions').innerHTML = '<button class=chr(34)ca-btn ca-cancelchr(34) onclick=chr(34)window.__caFormAnswer(false)chr(34)>Enseraf</button><button class=chr(34)ca-btn ca-okchr(34) onclick=chr(34)window.__caFormAnswer(true)chr(34)>Taeed</button>';
        overlay.classList.add('ca-show');
        window.__caPendingForm = f;
    }, true);
    window.__caFormAnswer = function(ok) {
        overlay.classList.remove('ca-show');
        var f = window.__caPendingForm;
        window.__caPendingForm = null;
        if (ok && f) { f.removeAttribute('onsubmit'); f.submit(); }
    };
})();
