# Diseño lanzamiento HelloChusquis — uneed.best 31/1/2027

Fecha: 2026-09-13. Estado: aprobado por owner. Objetivo único: stars + descargas PyPI. OSS, sin revenue. Día D perfecto, cero roto.

## 1. Contexto verificado

- Repo: HelloChusquis, agente AI local-first (terminal + web 7272 + REST API + Telegram).
- Versión real código: 5.4 (CHANGELOG). `pyproject.toml` dice 5.2 → drift a corregir en Fase 0.
- Tests: 398/398 verde (2026-09-13). Badge README dice 359 → corregir.
- Providers: catálogo 54–74 según superficie; pendiente unificar número público.
- Memoria: SQLite sesiones/summaries/learnings + `MDknowledge/` 1200+ ficheros (~9900 facts).
- Skills hoy: `core/skills.py` con formato JSON propio (`skills/*.json`), approval-gated, bounded shell. `skills-lock.json` + `.agents/skills/` son de hyperframes (vídeo), no del runtime.
- Subagentes: 12 builtins en `agents/`, presupuestos duros (12 steps / 12k tokens / 180s, 8 concurrentes).
- Vídeo launch 30s existe: `videos/hellochusquis-launch/renders/video.mp4` (1.3 MB, 1920×1080).

## 2. Reglas uneed.best (investigadas 2026-09-13)

- 85k makers, newsletter 22k (top3 semanal). Hasta 45 lanzamientos/día. Podio diario = visibilidad.
- Listing permanente solo con 10+ votos (lanzamientos gratis). Lanzamientos de pago conservan backlink dofollow DR75 siempre.
- Línea gratis cerrada desde ago-2026 (espera 6+ meses). Para asegurar 31/1/2027 hace falta Fast-track (~$15) o Skip-the-line (~$30). Acción Fase 0: reservar fecha YA.
- 31/1/2027 = domingo. Tráfico bajo (ideal mar–jue). Compensar con pre-launch page + pre-rally. No mover fecha (decisión owner: lanzamiento oficial ese día).
- Leaderboard rolling: votos valen siempre, también post-launch. Streak 5 días = +1 multiplicador (x2). Pro = +3 votos + relaunch mensual + Discord privado.
- Página necesita: logo, título, descripción, video preview, screenshots, Deal badge (oferta → badge + clics). Comprar votos = ban.
- Pre-launch page recoge emails → boost día D.

## 3. Estrategia elegida: A + C + skills acotado

- A (estabilidad primero): congelar features en dic. Todo el esfuerzo a install, onboarding, web/API, docs, demo.
- C (comunidad): streak diario ene, Discord, Reddit/X, HN Show previo, respuesta comentarios <1h.
- Skills universal: ÚNICA feature nueva. Justificación: imán de stars en votantes AI/dev de uneed; YAGNI pasa porque el ecosistema SKILL.md es estándar de facto y el coste es bajo si se acota.
- B (feature-blitz: cloud sync, marketplace, móvil) RECHAZADO: rompe meta día-perfecto.

## 4. Fases y criterios de salida

### Fase 0 — Ahora/Sep 2026: asegurar base
- [ ] Unificar versión a una sola fuente (pyproject = CHANGELOG = badge).
- [ ] Corregir badge tests (359 → real) y número providers/tools público.
- [ ] `pip install hellochusquis` limpio verificado en venv (3.10/11/12, mac/linux). `install.sh` probado.
- [ ] `python -m unittest discover tests -q` verde + `ruff check .` + `hellochusquis doctor --contracts`.
- [ ] Reservar fecha uneed (Fast-track/Skip) + publicar pre-launch page.
- [ ] Recortar preview vídeo para uneed desde render existente.
- Salida: install limpio 100%, fecha reservada, pre-launch online.

### Fase 1 — Oct: estabilidad
- [ ] Onboarding <2min: `config` / `--quick` → primer chat útil.
- [ ] `web`, `api`, `telegram` sin crash; auth loopback/remoto intacto; roles viewer/operator/owner.
- [ ] Memoria + MDknowledge sin regresión (probe factual 35q).
- [ ] Congelar catálogo providers/tools salvo roto.
- Salida: cero tracebacks en flujo demo, doctor verde.

### Fase 2 — Nov: universal skills (alcance cerrado)
Diseño mínimo sobre `core/skills.py` existente:
- [ ] Descubrimiento: `~/.hellochusquis/skills/*/SKILL.md` + `.agents/skills/` repo + workspace. Orden: workspace > home > repo.
- [ ] Parse frontmatter `name/description` con stdlib (sin deps). Cuerpo MD = prompt_template. Archivos auxiliares del folder accesibles por referencia.
- [ ] Reusar `SkillRegistry.list/find`, inyección a system prompt, ejecución shell con approval gate existente. Sin marketplace, sin auto-install, sin red.
- [ ] CLI `hellochusquis skills list/run`, 2 skills demo, docs.
- [ ] Tests: parse válido/inválido, path traversal bloqueado, approval requerido, prompt inyectado.
- Corte duro 1-dic: después solo bugfix.
- `ponytail:` scan recursivo ingenuo O(n), suficiente hasta ~500 skills; índice invertido si hace falta.

### Fase 3 — Dic: freeze + packaging
- [ ] Cero features. Solo fixes con regresión.
- [ ] README: banner, GIF demo, quickstart 3 pasos, badges reales, tabla superficies, sección skills, links uneed.
- [ ] SEO: `hellochusquis.dev`, sitemap, og.
- [ ] PyPI dry-runs semanales + matriz install + guía 5-min.
- [ ] Deal badge uneed (oferta OSS: cheat-sheet/template gratis).

### Fase 4 — Ene 2027: comunidad + día D
- [ ] Streak diario desde 1-ene (posts, votos, feedback ajeno).
- [ ] Pre-rally: emails pre-launch, X, Reddit (r/selfhosted, r/LocalLLaMA), HN Show días antes.
- [ ] Día D: link voto directo, vídeo, screenshots web/TUI, changelog, responder <1h.
- [ ] Post: 2 semanas momentum (votos rolling valen), fix <24h, objetivo newsletter top3.
- Salida: 10+ votos día D (permanencia), objetivo podio top3.

## 5. Métricas

- Día D: votos, posición diaria, visitas página uneed, installs PyPI semana.
- Calidad: tests verdes, issues críticos 0, tiempo install→primer chat.
- Post: stars GitHub, downloads PyPI/mes, votos rolling.

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Domingo flojo | Pre-launch emails + rally previo + votos rolling |
| Scope creep skills | Corte 1-dic, sin marketplace |
| Install roto día D | Matriz + dry-runs dic/ene |
| Version drift | Fuente única Fase 0 |
| <10 votos (listing no permanente) | Reserva pagada (dofollow asegurado) + pre-rally |

## 7. Decisiones tomadas

- Canal: uneed.best 31/1/2027, fecha fija.
- Estrategia A+C+skills acotado. B rechazado.
- Spec en español (petición owner).

## 8. Self-review spec (2026-09-13)

- Placeholders: ninguno (precios uneed con ~ por posible cambio; verificado sep-2026).
- Consistencia: fases secuenciales sin solape de features tras 1-dic. OK.
- Alcance: un solo feature (skills loader). OK, no descomponer.
- Ambigüedad: "número providers/tools público" queda como tarea Fase 0 con conteo real. OK.
