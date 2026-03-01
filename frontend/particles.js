function initParticles(canvasId, config) {
  const defaults = { count: 120, speed: 0.15, maxRadius: 1.5, maxOpacity: 0.25, connectionOpacity: 0.04 };
  const cfg = Object.assign({}, defaults, config);

  const c = document.getElementById(canvasId), x = c.getContext('2d');
  let W, H, pts = [];
  function resize() { W = c.width = innerWidth; H = c.height = innerHeight; }
  resize(); addEventListener('resize', resize);

  for (let i = 0; i < cfg.count; i++) {
    pts.push({
      x: Math.random() * innerWidth,
      y: Math.random() * innerHeight,
      vx: (Math.random() - .5) * cfg.speed,
      vy: (Math.random() - .5) * cfg.speed,
      r: Math.random() * cfg.maxRadius + .3,
      o: Math.random() * cfg.maxOpacity + .03,
      color: ['180,143,212', '139,159,212', '212,165,116', '196,122,138'][Math.floor(Math.random() * 4)]
    });
  }

  function draw() {
    x.clearRect(0, 0, W, H);
    pts.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      x.beginPath();
      x.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      x.fillStyle = `rgba(${p.color},${p.o})`;
      x.fill();
    });
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          x.beginPath();
          x.moveTo(pts[i].x, pts[i].y);
          x.lineTo(pts[j].x, pts[j].y);
          x.strokeStyle = `rgba(180,143,212,${(1 - dist / 120) * cfg.connectionOpacity})`;
          x.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
}
