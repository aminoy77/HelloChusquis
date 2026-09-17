// HelloChusquis landing FX — vanilla, 0 deps. Brand palette only.
// Ports: Cubes bg (grid 10 / r3 / 45°) + CountUp fallback + DotGrid CTA + Specular shine.
// ponytail: no gsap/motion/ogl — CSS vars + rAF cover it; ~60fps on integrated GPUs.
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const finePointer = window.matchMedia('(pointer: fine)').matches;

/* ── Cubes ─────────────────────────────────────────────── */
(() => {
  const mount = document.querySelector('#cube-react-root');
  const hero = document.querySelector('.hero');
  if (!mount || !hero) return;
  const gridSize = 10, radius = 3, maxAngle = 45;
  const field = document.createElement('div');
  field.className = 'cube-field';
  field.setAttribute('aria-hidden', 'true');
  const faces = ['top', 'bottom', 'left', 'right', 'front', 'back'];
  const cells = [];
  for (let r = 0; r < gridSize; r += 1) {
    for (let c = 0; c < gridSize; c += 1) {
      const cell = document.createElement('span');
      cell.className = 'cube-cell';
      cell.dataset.row = r;
      cell.dataset.col = c;
      faces.forEach((f) => {
        const face = document.createElement('i');
        face.className = `cube-face cube-face--${f}`;
        cell.append(face);
      });
      field.append(cell);
      cells.push({ el: cell, faces: [...cell.children], row: r, col: c });
    }
  }
  mount.append(field);
  if (reducedMotion) return;

  const tiltAt = (rowCenter, colCenter) => {
    for (const cell of cells) {
      const dist = Math.hypot(cell.row - rowCenter, cell.col - colCenter);
      const angle = dist <= radius ? (1 - dist / radius) * maxAngle : 0;
      cell.el.style.setProperty('--cube-x', `${-angle}deg`);
      cell.el.style.setProperty('--cube-y', `${angle}deg`);
    }
  };
  const resetAll = () => tiltAt(-10, -10);
  const pointOf = (x, y) => {
    const b = field.getBoundingClientRect();
    return {
      row: ((y - b.top) / b.height) * gridSize,
      col: ((x - b.left) / b.width) * gridSize,
      inside: x >= b.left && x <= b.right && y >= b.top && y <= b.bottom
    };
  };

  let lastActive = 0;
  let raf = 0, pending = null;
  hero.addEventListener('pointermove', (e) => {
    const p = pointOf(e.clientX, e.clientY);
    if (!p.inside) return;
    lastActive = performance.now();
    pending = p;
    if (raf) return;
    raf = requestAnimationFrame(() => { tiltAt(pending.row, pending.col); raf = 0; });
  }, { passive: true });
  hero.addEventListener('pointerleave', resetAll);
  hero.addEventListener('click', (e) => {
    if (e.target.closest('a, button')) return;
    const p = pointOf(e.clientX, e.clientY);
    if (!p.inside) return;
    lastActive = performance.now();
    // Ripple ámbar por anillos — staggered class add/remove, sin gsap.
    for (const cell of cells) {
      const ring = Math.round(Math.hypot(cell.row - p.row, cell.col - p.col));
      const delay = ring * 55;
      window.setTimeout(() => {
        cell.faces.forEach((f) => f.classList.add('is-ripple'));
        window.setTimeout(() => cell.faces.forEach((f) => f.classList.remove('is-ripple')), 420);
      }, delay);
    }
  });

  // Auto-drift cuando usuario idle >3s (igual que prop autoAnimate).
  let pos = { row: 3, col: 6 }, tgt = { row: 7, col: 3 };
  const drift = () => {
    if (performance.now() - lastActive > 3000) {
      pos = { row: pos.row + (tgt.row - pos.row) * 0.02, col: pos.col + (tgt.col - pos.col) * 0.02 };
      tiltAt(pos.row, pos.col);
      if (Math.hypot(pos.row - tgt.row, pos.col - tgt.col) < 0.1) {
        tgt = { row: Math.random() * gridSize, col: Math.random() * gridSize };
      }
    }
    requestAnimationFrame(drift);
  };
  if (finePointer) requestAnimationFrame(drift);
})();

/* ── DotGrid (CTA canvas) ──────────────────────────────── */
(() => {
  const canvas = document.querySelector('.dot-grid-canvas');
  if (!canvas) return;
  const card = canvas.closest('.cta-card');
  const ctx = canvas.getContext('2d');
  const GAP = 26, R = 1.6, PROX = 130, SHOCK_R = 220, PUSH = 5;
  let dots = [], w = 0, h = 0, visible = true;
  const ptr = { x: -9999, y: -9999 };

  const build = () => {
    const rect = card.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    w = rect.width; h = rect.height;
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    dots = [];
    for (let y = GAP / 2; y < h; y += GAP) {
      for (let x = GAP / 2; x < w; x += GAP) {
        dots.push({ x, y, ox: 0, oy: 0, vx: 0, vy: 0 });
      }
    }
    if (reducedMotion) draw(0);
  };

  const draw = (t) => {
    ctx.clearRect(0, 0, w, h);
    for (const d of dots) {
      if (!reducedMotion) {
        // spring retorno elástico manual (sin InertiaPlugin)
        d.vx = (d.vx + -d.ox * 0.08) * 0.82;
        d.vy = (d.vy + -d.oy * 0.08) * 0.82;
        d.ox += d.vx; d.oy += d.vy;
      }
      const dx = d.x - ptr.x, dy = d.y - ptr.y;
      const dist = Math.hypot(dx, dy);
      const k = dist < PROX ? 1 - dist / PROX : 0;
      const a = 0.22 + k * 0.63;
      const r = R + k * 1.4;
      ctx.beginPath();
      ctx.arc(d.x + d.ox, d.y + d.oy, r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(5,5,4,${a.toFixed(3)})`;
      ctx.fill();
    }
    void t;
  };

  if (!reducedMotion) {
    const loop = () => { if (visible) draw(); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  }
  build();
  new ResizeObserver(build).observe(card);
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(card);

  card.addEventListener('pointermove', (e) => {
    const b = canvas.getBoundingClientRect();
    ptr.x = e.clientX - b.left; ptr.y = e.clientY - b.top;
  }, { passive: true });
  card.addEventListener('pointerleave', () => { ptr.x = -9999; ptr.y = -9999; });
  card.addEventListener('click', (e) => {
    if (reducedMotion) return;
    const b = canvas.getBoundingClientRect();
    const cx = e.clientX - b.left, cy = e.clientY - b.top;
    for (const d of dots) {
      const dist = Math.hypot(d.x - cx, d.y - cy);
      if (dist < SHOCK_R) {
        const fall = 1 - dist / SHOCK_R;
        d.vx += ((d.x - cx) / (dist + 1)) * PUSH * fall;
        d.vy += ((d.y - cy) / (dist + 1)) * PUSH * fall;
      }
    }
  });
})();

/* ── Specular shine (CSS conic sigue puntero) ───────────── */
(() => {
  const btns = [...document.querySelectorAll('.specular')];
  if (!btns.length || reducedMotion) return;
  let mx = innerWidth / 2, my = 180, idle = 2.4;
  addEventListener('pointermove', (e) => { mx = e.clientX; my = e.clientY; }, { passive: true });
  let last = performance.now();
  const frame = (now) => {
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    idle += 0.35 * dt; // auto-sweep cuando puntero lejos
    for (const b of btns) {
      const r = b.getBoundingClientRect();
      if (r.bottom < -80 || r.top > innerHeight + 80) continue;
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const dx = Math.max(r.left - mx, 0, mx - r.right);
      const dy = Math.max(r.top - my, 0, my - r.bottom);
      const dist = Math.hypot(dx, dy);
      const over = dist === 0;
      const ang = over
        ? Math.atan2(2 / r.height, -2 / r.width) + ((mx - cx) / (r.width / 2)) * 0.3
        : Math.atan2(cy - my, mx - cx);
      const t = Math.max(0, 1 - dist / 250);
      b.style.setProperty('--sb-angle', `${(over ? ang : (dist < 600 ? ang : idle))}rad`);
      b.style.setProperty('--sb-bright', (t * t * (3 - 2 * t)).toFixed(3));
    }
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
})();
