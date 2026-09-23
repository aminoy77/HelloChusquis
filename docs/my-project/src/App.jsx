import { useEffect, useRef } from 'react'
import { Renderer, Program, Mesh, Color, Triangle } from 'ogl'
import gsap from 'gsap'
import logoPrimary from '../../../logo-primary.png'
import kbAccuracy from '../../assets/kb-accuracy.svg'
import v52Latency from '../../assets/v52-latency.svg'
import './App.css'

const VERT = `#version 300 es
in vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`

const FRAG = `#version 300 es
precision highp float;

uniform float uTime;
uniform float uAmplitude;
uniform vec3 uColorStops[3];
uniform vec2 uResolution;
uniform float uBlend;
uniform float uLightMode;

out vec4 fragColor;

vec3 permute(vec3 x) {
  return mod(((x * 34.0) + 1.0) * x, 289.0);
}

float snoise(vec2 v){
  const vec4 C = vec4(
      0.211324865405187, 0.366025403784439,
      -0.577350269189626, 0.024390243902439
  );
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);

  vec3 p = permute(
      permute(i.y + vec3(0.0, i1.y, 1.0))
    + i.x + vec3(0.0, i1.x, 1.0)
  );

  vec3 m = max(
      0.5 - vec3(
          dot(x0, x0),
          dot(x12.xy, x12.xy),
          dot(x12.zw, x12.zw)
      ),
      0.0
  );
  m = m * m;
  m = m * m;

  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);

  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

struct ColorStop {
  vec3 color;
  float position;
};

#define COLOR_RAMP(colors, factor, finalColor) {              \
  int index = 0;                                            \
  for (int i = 0; i < 2; i++) {                               \
     ColorStop currentColor = colors[i];                     \
     bool isInBetween = currentColor.position <= factor;    \
     index = int(mix(float(index), float(i), float(isInBetween))); \
  }                                                         \
  ColorStop currentColor = colors[index];                   \
  ColorStop nextColor = colors[index + 1];                  \
  float range = nextColor.position - currentColor.position; \
  float lerpFactor = (factor - currentColor.position) / range; \
  finalColor = mix(currentColor.color, nextColor.color, lerpFactor); \
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;

  ColorStop colors[3];
  colors[0] = ColorStop(uColorStops[0], 0.0);
  colors[1] = ColorStop(uColorStops[1], 0.5);
  colors[2] = ColorStop(uColorStops[2], 1.0);

  vec3 rampColor;
  COLOR_RAMP(colors, uv.x, rampColor);

  float height = snoise(vec2(uv.x * 2.0 + uTime * 0.1, uTime * 0.25)) * 0.5 * uAmplitude;
  height = exp(height);
  height = (uv.y * 2.0 - height + 0.2);
  float intensity = 0.6 * height;

  float midPoint = 0.20;
  float auroraAlpha = smoothstep(midPoint - uBlend * 0.5, midPoint + uBlend * 0.5, intensity);

  vec3 auroraColor = intensity * rampColor;

  if (uLightMode > 0.5) {
    float energy = clamp(max(intensity, 0.0), 0.0, 1.0);
    float coverage = clamp(auroraAlpha * (0.55 + 0.45 * energy), 0.0, 0.86);
    vec3 chroma = pow(clamp(rampColor, 0.0, 1.0), vec3(1.2));
    float chromaPeak = max(chroma.r, max(chroma.g, chroma.b));
    chroma /= max(chromaPeak, 0.0001);
    fragColor = vec4(mix(vec3(1.0), chroma, min(coverage * 1.08, 0.94)), 1.0);
  } else {
    fragColor = vec4(auroraColor * auroraAlpha, auroraAlpha);
  }
}
`

function Aurora({
  colorStops = ['#f5a623', '#ffdd8d', '#5eb97e'],
  amplitude = 1.1,
  blend = 0.9,
  lightMode = false,
}) {
  const ctnRef = useRef(null)
  const propsRef = useRef({ colorStops, amplitude, blend, lightMode })

  useEffect(() => {
    propsRef.current = { colorStops, amplitude, blend, lightMode }
  }, [colorStops, amplitude, blend, lightMode])

  useEffect(() => {
    const ctn = ctnRef.current
    if (!ctn) return

    const renderer = new Renderer({ alpha: true, premultipliedAlpha: true, antialias: true })
    const gl = renderer.gl
    gl.clearColor(0, 0, 0, 0)
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.canvas.style.background = 'transparent'

    let program
    const geometry = new Triangle(gl)
    if (geometry.attributes.uv) delete geometry.attributes.uv

    const colorStopsArray = propsRef.current.colorStops.map(hex => {
      const c = new Color(hex)
      return [c.r, c.g, c.b]
    })

    program = new Program(gl, {
      vertex: VERT,
      fragment: FRAG,
      uniforms: {
        uTime: { value: 0 },
        uAmplitude: { value: propsRef.current.amplitude },
        uColorStops: { value: colorStopsArray },
        uResolution: { value: [ctn.offsetWidth, ctn.offsetHeight] },
        uBlend: { value: propsRef.current.blend },
        uLightMode: { value: propsRef.current.lightMode ? 1 : 0 },
      },
    })

    const mesh = new Mesh(gl, { geometry, program })
    ctn.appendChild(gl.canvas)

    let animationId = 0
    const update = (t) => {
      animationId = requestAnimationFrame(update)
      const { time = t * 0.01, speed = 1.0 } = propsRef.current
      program.uniforms.uTime.value = time * speed * 0.1
      program.uniforms.uAmplitude.value = propsRef.current.amplitude ?? 1.0
      program.uniforms.uBlend.value = propsRef.current.blend ?? 0.9
      program.uniforms.uLightMode.value = propsRef.current.lightMode ? 1 : 0
      program.uniforms.uColorStops.value = (propsRef.current.colorStops ?? colorStops).map(hex => {
        const c = new Color(hex)
        return [c.r, c.g, c.b]
      })
      renderer.render({ scene: mesh })
    }

    const resize = () => {
      const width = ctn.offsetWidth
      const height = ctn.offsetHeight
      renderer.setSize(width, height)
      if (program) program.uniforms.uResolution.value = [width, height]
    }

    resize()
    animationId = requestAnimationFrame(update)
    window.addEventListener('resize', resize)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', resize)
      if (ctn && gl.canvas.parentNode === ctn) ctn.removeChild(gl.canvas)
      gl.getExtension('WEBGL_lose_context')?.loseContext()
    }
  }, [])

  return <div ref={ctnRef} className="aurora-container" aria-hidden="true" />
}

function Cubes({
  gridSize = 10,
  cubeSize = 20,
  maxAngle = 48,
  radius = 3,
  easing = 'power3.out',
  duration = { enter: 0.35, leave: 0.8 },
}) {
  const sceneRef = useRef(null)

  useEffect(() => {
    if (!sceneRef.current) return

    const cells = sceneRef.current.querySelectorAll('.cube')
    const tiltAt = (rowCenter, colCenter) => {
      cells.forEach((cube) => {
        const r = Number(cube.dataset.row)
        const c = Number(cube.dataset.col)
        const dist = Math.hypot(r - rowCenter, c - colCenter)
        const angle = dist <= radius ? (1 - dist / radius) * maxAngle : 0

        gsap.to(cube, {
          duration: dist <= radius ? duration.enter : duration.leave,
          ease: easing,
          overwrite: true,
          rotateX: -angle,
          rotateY: angle,
        })
      })
    }

    const onPointerMove = (event) => {
      const rect = sceneRef.current.getBoundingClientRect()
      const cellW = rect.width / gridSize
      const cellH = rect.height / gridSize
      const colCenter = (event.clientX - rect.left) / cellW
      const rowCenter = (event.clientY - rect.top) / cellH
      tiltAt(rowCenter, colCenter)
    }

    const onPointerLeave = () => {
      cells.forEach((cube) => {
        gsap.to(cube, {
          duration: duration.leave,
          rotateX: 0,
          rotateY: 0,
          ease: 'power3.out',
          overwrite: true,
        })
      })
    }

    let rafId = 0
    const loop = () => {
      const pos = { x: 3 + Math.sin(Date.now() * 0.0008) * 2, y: 5 + Math.cos(Date.now() * 0.0009) * 2 }
      tiltAt(pos.y, pos.x)
      rafId = requestAnimationFrame(loop)
    }

    sceneRef.current.addEventListener('pointermove', onPointerMove)
    sceneRef.current.addEventListener('pointerleave', onPointerLeave)
    rafId = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(rafId)
      sceneRef.current?.removeEventListener('pointermove', onPointerMove)
      sceneRef.current?.removeEventListener('pointerleave', onPointerLeave)
    }
  }, [cubeSize, duration.enter, duration.leave, easing, gridSize, maxAngle, radius])

  const cells = Array.from({ length: gridSize })

  return (
    <div className="default-animation">
      <div ref={sceneRef} className="default-animation--scene" style={{
        gridTemplateColumns: `repeat(${gridSize}, ${cubeSize}px)`,
        gridTemplateRows: `repeat(${gridSize}, ${cubeSize}px)`,
      }}>
        {cells.map((_, r) =>
          cells.map((__, c) => (
            <div key={`${r}-${c}`} className="cube" data-row={r} data-col={c}>
              <div className="cube-face cube-face--top" />
              <div className="cube-face cube-face--bottom" />
              <div className="cube-face cube-face--left" />
              <div className="cube-face cube-face--right" />
              <div className="cube-face cube-face--front" />
              <div className="cube-face cube-face--back" />
            </div>
          )),
        )}
      </div>
    </div>
  )
}

function CursorGrid({
  cellSize = 40,
  color = '#f5a623',
  radius = 140,
  falloff = 'smooth',
  holdTime = 400,
  fadeDuration = 800,
  lineWidth = 1.2,
  maxOpacity = 1,
  fillOpacity = 0,
  gridOpacity = 0,
  cellRadius = 0,
  clickPulse = true,
  pulseSpeed = 600,
  className = '',
}) {
  const containerRef = useRef(null)
  const canvasRef = useRef(null)
  const wakeRef = useRef(null)

  const FALLOFF_CURVES = {
    linear: (t) => t,
    smooth: (t) => t * t * (3 - 2 * t),
    sharp: (t) => t * t * t,
  }

  const hexToRgb = (hex) => {
    const h = hex.replace('#', '')
    const v = h.length === 3 ? h.split('').map((c) => c + c).join('') : h
    const num = Number.parseInt(v.slice(0, 6), 16)
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255]
  }

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    const ctx = canvas.getContext('2d')
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    let cols = 0
    let rows = 0
    let offX = 0
    let offY = 0
    let alphas = new Float32Array(0)
    let touched = new Float64Array(0)
    let w = 0
    let h = 0
    const pulses = []
    let raf = 0
    let running = false
    let lastFrame = 0

    const rebuild = () => {
      w = container.offsetWidth
      h = container.offsetHeight
      canvas.width = Math.max(1, Math.round(w * dpr))
      canvas.height = Math.max(1, Math.round(h * dpr))
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      cols = Math.ceil(w / cellSize) + 1
      rows = Math.ceil(h / cellSize) + 1
      offX = (w - cols * cellSize) / 2
      offY = (h - rows * cellSize) / 2
      alphas = new Float32Array(cols * rows)
      touched = new Float64Array(cols * rows)
    }

    const cellCenter = (i) => {
      const cx = offX + (i % cols) * cellSize + cellSize / 2
      const cy = offY + Math.floor(i / cols) * cellSize + cellSize / 2
      return [cx, cy]
    }

    const energize = (x, y, boost) => {
      const r = Math.max(radius, 1)
      const ease = FALLOFF_CURVES[falloff] ?? FALLOFF_CURVES.linear
      const now = performance.now()
      const minCol = Math.max(0, Math.floor((x - r - offX) / cellSize))
      const maxCol = Math.min(cols - 1, Math.floor((x + r - offX) / cellSize))
      const minRow = Math.max(0, Math.floor((y - r - offY) / cellSize))
      const maxRow = Math.min(rows - 1, Math.floor((y + r - offY) / cellSize))

      for (let cRow = minRow; cRow <= maxRow; cRow += 1) {
        for (let cCol = minCol; cCol <= maxCol; cCol += 1) {
          const i = cRow * cols + cCol
          const [cx, cy] = cellCenter(i)
          const dist = Math.hypot(cx - x, cy - y)
          if (dist > r) continue
          const level = ease(1 - dist / r) * maxOpacity * (boost ?? 1)
          if (level > alphas[i]) {
            alphas[i] = level
            touched[i] = now
          } else if (level > 0) {
            touched[i] = now
          }
        }
      }
    }

    const draw = (now) => {
      const dt = Math.min(now - lastFrame, 50)
      lastFrame = now
      ctx.clearRect(0, 0, w, h)
      const [cr, cg, cb] = hexToRgb(color)

      if (gridOpacity > 0) {
        ctx.strokeStyle = `rgba(${cr}, ${cg}, ${cb}, ${gridOpacity})`
        ctx.lineWidth = 1
        ctx.beginPath()
        for (let cCol = 0; cCol <= cols; cCol += 1) {
          const x = Math.round(offX + cCol * cellSize) + 0.5
          ctx.moveTo(x, 0)
          ctx.lineTo(x, h)
        }
        for (let cRow = 0; cRow <= rows; cRow += 1) {
          const y = Math.round(offY + cRow * cellSize) + 0.5
          ctx.moveTo(0, y)
          ctx.lineTo(w, y)
        }
        ctx.stroke()
      }

      for (let pi = pulses.length - 1; pi >= 0; pi -= 1) {
        const pulse = pulses[pi]
        const age = (now - pulse.t0) / 1000
        const ringR = age * pulseSpeed
        if (ringR > Math.hypot(w, h)) {
          pulses.splice(pi, 1)
          continue
        }
        const band = cellSize
        const minCol = Math.max(0, Math.floor((pulse.x - ringR - band - offX) / cellSize))
        const maxCol = Math.min(cols - 1, Math.floor((pulse.x + ringR + band - offX) / cellSize))
        const minRow = Math.max(0, Math.floor((pulse.y - ringR - band - offY) / cellSize))
        const maxRow = Math.min(rows - 1, Math.floor((pulse.y + ringR + band - offY) / cellSize))

        for (let cRow = minRow; cRow <= maxRow; cRow += 1) {
          for (let cCol = minCol; cCol <= maxCol; cCol += 1) {
            const i = cRow * cols + cCol
            const [cx, cy] = cellCenter(i)
            const dist = Math.hypot(cx - pulse.x, cy - pulse.y)
            if (Math.abs(dist - ringR) < band / 2 && maxOpacity > alphas[i]) {
              alphas[i] = maxOpacity
              touched[i] = now
            }
          }
        }
      }

      let anyVisible = pulses.length > 0
      const fadeStep = dt / Math.max(fadeDuration, 16)
      const half = cellSize / 2

      for (let i = 0; i < alphas.length; i += 1) {
        let a = alphas[i]
        if (a <= 0) continue
        if (now - touched[i] > holdTime) {
          a = Math.max(0, a - fadeStep)
          alphas[i] = a
          if (a <= 0) continue
        }
        anyVisible = true

        const [cx, cy] = cellCenter(i)
        const gradient = ctx.createRadialGradient(cx, cy, half * 0.1, cx, cy, cellSize)
        gradient.addColorStop(0, `rgba(${cr}, ${cg}, ${cb}, ${a})`)
        gradient.addColorStop(1, `rgba(${cr}, ${cg}, ${cb}, 0)`)

        const x = cx - half + 0.5
        const y = cy - half + 0.5
        const s = cellSize - 1

        ctx.beginPath()
        if (cellRadius > 0) {
          ctx.roundRect(x, y, s, s, cellRadius)
        } else {
          ctx.rect(x, y, s, s)
        }
        if (fillOpacity > 0) {
          ctx.fillStyle = `rgba(${cr}, ${cg}, ${cb}, ${a * fillOpacity})`
          ctx.fill()
        }
        ctx.strokeStyle = gradient
        ctx.lineWidth = lineWidth
        ctx.stroke()
      }

      if (anyVisible) {
        raf = requestAnimationFrame(draw)
      } else {
        running = false
        if (gridOpacity <= 0) ctx.clearRect(0, 0, w, h)
      }
    }

    const wake = () => {
      if (running) return
      running = true
      lastFrame = performance.now()
      raf = requestAnimationFrame(draw)
    }
    wakeRef.current = wake

    const toLocal = (event) => {
      const rect = canvas.getBoundingClientRect()
      return [event.clientX - rect.left, event.clientY - rect.top]
    }

    const onPointerMove = (event) => {
      const [x, y] = toLocal(event)
      energize(x, y)
      wake()
    }

    const onPointerDown = (event) => {
      if (!clickPulse) return
      const [x, y] = toLocal(event)
      pulses.push({ x, y, t0: performance.now() })
      wake()
    }

    const ro = new ResizeObserver(() => {
      rebuild()
      wake()
    })
    ro.observe(container)
    rebuild()
    wake()

    container.addEventListener('pointermove', onPointerMove)
    container.addEventListener('pointerdown', onPointerDown)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      container.removeEventListener('pointermove', onPointerMove)
      container.removeEventListener('pointerdown', onPointerDown)
    }
  }, [cellRadius, cellSize, clickPulse, color, falloff, fadeDuration, fillOpacity, gridOpacity, holdTime, lineWidth, maxOpacity, pulseSpeed, radius])

  useEffect(() => {
    wakeRef.current?.()
  }, [gridOpacity, color, lineWidth, maxOpacity, fillOpacity, cellRadius])

  return (
    <div ref={containerRef} className={`cursor-grid${className ? ` ${className}` : ''}`}>
      <canvas ref={canvasRef} className="cursor-grid__canvas" />
    </div>
  )
}

function App() {
  return (
    <div className="landing-page">
      <header className="topbar">
        <div className="container nav-shell">
          <div className="brand" aria-label="HelloChusquis brand">
            <img src={logoPrimary} alt="HelloChusquis logo" className="brand-logo" />
            <span>HelloChusquis</span>
          </div>
          <nav className="nav-links" aria-label="Main navigation">
            <a href="#features">Features</a>
            <a href="#proof">Proof</a>
            <a href="#workflow">Workflow</a>
            <a href="#install" className="nav-button">Install</a>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-aurora"><Aurora /></div>
          <div className="hero-grid" aria-hidden="true" />
          <div className="container hero-content">
            <div className="hero-copy">
              <div className="eyebrow">LOCAL-FIRST AI FOR BUILDERS</div>
              <h1>
                Give your work <span className="gradient-text">an agent</span> you can trust.
              </h1>
              <p className="hero-subtitle">
                HelloChusquis keeps the conversation close to your terminal, your browser, and your systems — with
                tools, memory, safe approvals, and clear local control.
              </p>

              <div className="hero-actions">
                <a href="#install" className="primary-btn">Install now</a>
                <a href="#features" className="secondary-btn">See features</a>
              </div>

              <div className="stats-strip">
                <div className="stat-pill">
                  <strong>421</strong>
                  <span>tests passing</span>
                </div>
                <div className="stat-pill">
                  <strong>48+</strong>
                  <span>tool integrations</span>
                </div>
                <div className="stat-pill">
                  <strong>100%</strong>
                  <span>local by default</span>
                </div>
              </div>
            </div>

            <div className="hero-visual" aria-label="HelloChusquis workspace preview">
              <div className="hero-cubes" aria-hidden="true">
                <Cubes />
              </div>

              <div className="app-window">
                <div className="window-bar">
                  <span className="dot red" />
                  <span className="dot amber" />
                  <span className="dot green" />
                </div>

                <div className="window-body">
                  <div className="window-grid">
                    <div className="terminal-panel">
                      <div className="prompt-line">
                        <span className="prompt">$</span>
                        <span>hellochusquis</span>
                      </div>
                      <div className="terminal-body">
                        <span className="terminal-tag">search</span>
                        <span> latest Python release and summarize what changed</span>
                      </div>
                      <div className="terminal-lines">
                        <span>• open docs</span>
                        <span>• inspect repo</span>
                        <span>• run bounded shell commands</span>
                      </div>
                    </div>

                    <div className="mini-panel">
                      <div className="mini-panel__header">
                        <span>signal</span>
                        <span className="status">live</span>
                      </div>
                      <div className="mini-panel__body">
                        <div className="mini-metric">
                          <strong>86%</strong>
                          <small>→ 100%</small>
                        </div>
                        <div className="mini-metric">
                          <strong>4.2x</strong>
                          <small>faster</small>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="signal-card">
                    <div className="signal-copy">
                      <span className="signal-label">Query result</span>
                      <h3>Keep context useful.</h3>
                    </div>
                    <CursorGrid className="signal-grid" cellSize={16} radius={86} color="#f5a623" />
                  </div>
                </div>
              </div>

              <div className="floating-badge badge-one">
                <span className="badge-kicker">factual reach</span>
                <strong>100%</strong>
              </div>

              <div className="floating-badge badge-two">
                <span className="badge-kicker">local</span>
                <strong>safe</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="proof section" id="proof">
          <div className="container proof-grid">
            <div className="proof-card proof-visual">
              <img src={kbAccuracy} alt="Knowledge accuracy chart" />
            </div>
            <div className="proof-card proof-copy">
              <div className="eyebrow eyebrow-dark">PROOF</div>
              <h2>Measured gains, not empty promises.</h2>
              <p>
                The knowledge layer improves factual recall, while the workflow keeps actions visible and scoped to the
                task. That means stronger answers with safer execution.
              </p>
              <ul>
                <li>Retrieval coverage that stays useful in real work</li>
                <li>Explainable tool calls rather than opaque black-box behavior</li>
                <li>Local-first defaults that keep credentials and context in your control</li>
              </ul>
            </div>
          </div>

          <div className="container chart-row">
            <div className="chart-card">
              <div className="card-label">Latency</div>
              <img src={v52Latency} alt="Latency improvement chart" />
            </div>
            <div className="chart-card compact">
              <div className="card-label">Workflow</div>
              <div className="workflow-list">
                <span>terminal</span>
                <span>web</span>
                <span>api</span>
                <span>telegram</span>
              </div>
            </div>
          </div>
        </section>

        <section className="features section" id="features">
          <div className="container">
            <div className="section-heading">
              <div className="eyebrow">WHY IT WORKS</div>
              <h2>Everything your stack already needs, in one control plane.</h2>
            </div>

            <div className="feature-grid">
              <article className="feature-card">
                <div className="feature-icon">01</div>
                <h3>Work beside your code</h3>
                <p>Search repos, inspect files, run bounded shell tasks, and plan work without leaving the agent.</p>
              </article>
              <article className="feature-card">
                <div className="feature-icon">02</div>
                <h3>Connect the tools you trust</h3>
                <p>GitHub, Slack, Docker, Notion, AWS, Stripe, Postgres, and more can be added without turning the setup into a swamp.</p>
              </article>
              <article className="feature-card">
                <div className="feature-icon">03</div>
                <h3>Keep context useful</h3>
                <p>Memory, summaries, and retrieval stay local so the system remembers what matters without turning every prompt into a transcript dump.</p>
              </article>
            </div>
          </div>
        </section>

        <section className="showcase section" id="workflow">
          <div className="container showcase-grid">
            <div className="showcase-copy">
              <div className="eyebrow">WORKFLOW</div>
              <h2>From a single prompt to a safe, visible result.</h2>
              <p>
                Plan, execute, and review in one place. Every turn is searchable, every tool call is visible, and every
                permission boundary stays clear.
              </p>
              <div className="mini-list">
                <span>Command execution</span>
                <span>Web access</span>
                <span>File management</span>
                <span>Approval gates</span>
              </div>
            </div>

            <div className="showcase-panel">
              <div className="showcase-cubes" aria-hidden="true">
                <Cubes />
              </div>
              <div className="showcase-bubble bubble-top">visible</div>
              <div className="showcase-bubble bubble-bottom">safe</div>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer" id="install">
        <div className="container footer-shell">
          <div>
            <div className="brand compact">
              <img src={logoPrimary} alt="HelloChusquis logo" className="brand-logo" />
              <span>HelloChusquis</span>
            </div>
          </div>

          <div className="footer-actions">
            <code>python -m pip install hellochusquis</code>
            <a href="https://github.com/aminoy77/HelloChusquis" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
