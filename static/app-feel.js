(function(){
  // ===== Splash =====
  if (!sessionStorage.getItem('splash_shown')){
    var sp = document.createElement('div');
    sp.id = 'app-splash';
    sp.innerHTML = '<div class="sp-logo">🛒</div><div class="sp-name">پنل من</div><div class="sp-dots"><span></span><span></span><span></span></div>';
    document.body.appendChild(sp);
    setTimeout(function(){ sp.classList.add('hide'); }, 1200);
    setTimeout(function(){ if(sp.parentNode) sp.parentNode.removeChild(sp); }, 2000);
    sessionStorage.setItem('splash_shown', '1');
  }

  // ===== Toast global =====
  window.showToast = function(msg, type){
    var t = document.getElementById('app-toast');
    if (!t){
      t = document.createElement('div');
      t.id = 'app-toast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.className = type === 'error' ? 'error show' : 'show';
    clearTimeout(t._timer);
    t._timer = setTimeout(function(){ t.classList.remove('show'); }, 2500);
  };

  // ===== Haptic =====
  window.haptic = function(ms){
    if (navigator.vibrate) navigator.vibrate(ms || 10);
  };

  // ===== به همه کلیک‌ها لرزش کوچیک =====
  document.addEventListener('click', function(e){
    var el = e.target.closest('button, a, .tab, .ni, .cat, .main-cat, .prod, .shop');
    if (el) window.haptic(8);
  }, true);

  // ===== Page fade =====
  document.addEventListener('DOMContentLoaded', function(){
    document.body.classList.add('page-fade');
  });

  // ===== Pull to Refresh =====
  var startY = 0, pulling = false;
  var ptr = document.createElement('div');
  ptr.id = 'ptr';
  ptr.textContent = '↓';
  document.body.appendChild(ptr);

  document.addEventListener('touchstart', function(e){
    if (window.scrollY === 0){
      startY = e.touches[0].clientY;
      pulling = true;
    }
  }, {passive:true});

  document.addEventListener('touchmove', function(e){
    if (!pulling) return;
    var dy = e.touches[0].clientY - startY;
    if (dy > 80 && window.scrollY === 0){
      ptr.classList.add('show');
      ptr.textContent = '↻';
    }
  }, {passive:true});

  document.addEventListener('touchend', function(){
    if (ptr.classList.contains('show')){
      ptr.classList.add('spin');
      ptr.textContent = '↻';
      setTimeout(function(){ location.reload(); }, 300);
    }
    pulling = false;
  }, {passive:true});
})();
