// 🎉 Confetti سبک — بدون کتابخانه
(function() {
  const COLORS = ['#00ff9d','#00d4ff','#bf00ff','#ffd700','#ff2e63','#ff8c00'];
  const PIECES = 80;
  let canvas, ctx, pieces = [], running = false;

  function init() {
    canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999';
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    ctx = canvas.getContext('2d');
    window.addEventListener('resize', () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    });
  }

  function createPieces() {
    pieces = [];
    for (let i = 0; i < PIECES; i++) {
      pieces.push({
        x: Math.random() * canvas.width,
        y: -20 - Math.random() * canvas.height * 0.5,
        w: 6 + Math.random() * 6,
        h: 8 + Math.random() * 8,
        vy: 2 + Math.random() * 4,
        vx: -1 + Math.random() * 2,
        rot: Math.random() * 360,
        vr: -4 + Math.random() * 8,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        alpha: 1
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = 0;
    for (const p of pieces) {
      p.x += p.vx;
      p.y += p.vy;
      p.rot += p.vr;
      if (p.y > canvas.height * 0.7) p.alpha -= 0.015;
      if (p.alpha <= 0) continue;
      alive++;
      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot * Math.PI / 180);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
      ctx.restore();
    }
    if (alive > 0) {
      requestAnimationFrame(draw);
    } else {
      running = false;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  window.confetti = function() {
    if (!canvas) init();
    createPieces();
    if (!running) {
      running = true;
      draw();
    }
  };
})();
