import React, { useEffect, useMemo, useRef } from 'https://esm.sh/react@19.1.1';
import { createRoot } from 'https://esm.sh/react-dom@19.1.1/client';
import gsap from 'https://esm.sh/gsap@3.13.2';

const h = React.createElement;

function Cubes({ gridSize = 10, radius = 4, maxAngle = 32 }) {
  const scene = useRef(null);
  const activeUntil = useRef(0);
  const cells = useMemo(() => Array.from({ length: gridSize * gridSize }, (_, index) => ({ row: Math.floor(index / gridSize), col: index % gridSize })), [gridSize]);

  useEffect(() => {
    const el = scene.current;
    if (!el || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    const cubeElements = [...el.children];
    const tiltAt = (rowCenter, colCenter) => cubeElements.forEach((cube, index) => {
      const { row, col } = cells[index];
      const distance = Math.hypot(row - rowCenter, col - colCenter);
      const angle = distance < radius ? (1 - distance / radius) * maxAngle : 0;
      gsap.to(cube, { '--cube-x': `${-angle}deg`, '--cube-y': `${angle}deg`, duration: .32, ease: 'power3.out', overwrite: true });
    });
    const point = (event) => { const rect = el.getBoundingClientRect(); return { row: ((event.clientY - rect.top) / rect.height) * gridSize, col: ((event.clientX - rect.left) / rect.width) * gridSize }; };
    const move = (event) => { activeUntil.current = performance.now() + 1200; const { row, col } = point(event); tiltAt(row, col); };
    const ripple = (event) => { const { row, col } = point(event); cubeElements.forEach((cube, index) => { const item = cells[index]; const delay = Math.round(Math.hypot(item.row - row, item.col - col)) * .04; gsap.fromTo(cube, { backgroundColor: '#f5a623', borderColor: '#ffda89', boxShadow: '0 0 20px rgba(245,166,35,.45)' }, { backgroundColor: '#17130e', borderColor: 'rgba(245,166,35,.25)', boxShadow: 'inset 0 0 13px rgba(245,166,35,.025)', duration: .55, delay, ease: 'power3.out' }); }); };
    let position = { row: 3, col: 6 }; let target = { row: 7, col: 3 }; let frame;
    const drift = () => { if (performance.now() > activeUntil.current) { position = { row: position.row + (target.row - position.row) * .018, col: position.col + (target.col - position.col) * .018 }; tiltAt(position.row, position.col); if (Math.hypot(position.row - target.row, position.col - target.col) < .12) target = { row: Math.random() * gridSize, col: Math.random() * gridSize }; } frame = requestAnimationFrame(drift); };
    el.addEventListener('pointermove', move); el.addEventListener('click', ripple); frame = requestAnimationFrame(drift);
    return () => { el.removeEventListener('pointermove', move); el.removeEventListener('click', ripple); cancelAnimationFrame(frame); gsap.killTweensOf(cubeElements); };
  }, [cells, gridSize, maxAngle, radius]);

  return h('div', { ref: scene, className: 'cube-field', 'aria-hidden': 'true' }, cells.map(({ row, col }) => h('span', { className: 'cube-cell', 'data-row': row, 'data-col': col, key: `${row}-${col}` })));
}

const mount = document.querySelector('#cube-react-root');
if (mount) createRoot(mount).render(h(Cubes));
