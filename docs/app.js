// HelloChusquis landing — real Aurora shader (vanilla WebGL, no deps).
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Hello in different languages, animated swap. Runs first so it never depends on GL. */
  var hellos = ['Hola', 'Hello', 'Ciao', 'Bonjour', 'Olá', 'Hallo', 'Hej', 'こんにちは', '你好'];
  var hi = 0;
  var helloEl = document.getElementById('hello-word');
  if (helloEl && !reduce) {
    setInterval(function () {
      helloEl.classList.add('is-leaving');
      setTimeout(function () {
        hi = (hi + 1) % hellos.length;
        helloEl.textContent = hellos[hi];
        helloEl.classList.remove('is-leaving');
        helloEl.classList.add('is-entering');
        setTimeout(function () { helloEl.classList.remove('is-entering'); }, 400);
      }, 220);
    }, 2600);
  }

  /* Aurora background — exact simplex shader, palette color stops. */
  try { (function aurora() {
    var canvas = document.getElementById('aurora');
    if (!canvas) return;
    function hex(h) {
      h = h.replace('#', '');
      return [parseInt(h.slice(0, 2), 16) / 255, parseInt(h.slice(2, 4), 16) / 255, parseInt(h.slice(4, 6), 16) / 255];
    }
    var STOPS = ['#f5a623', '#ffd37b', '#5eb97e'].map(hex); // palette
    var VERT = '#version 300 es\nin vec2 position;\nvoid main(){gl_Position=vec4(position,0.0,1.0);}';
    var FRAG = `#version 300 es
precision highp float;
uniform float uTime; uniform float uAmplitude; uniform vec3 uColorStops[3];
uniform vec2 uResolution; uniform float uBlend;
out vec4 fragColor;
vec3 permute(vec3 x){return mod(((x*34.0)+1.0)*x,289.0);}
float snoise(vec2 v){
  const vec4 C=vec4(0.211324865405187,0.366025403784439,-0.577350269189626,0.024390243902439);
  vec2 i=floor(v+dot(v,C.yy)); vec2 x0=v-i+dot(i,C.xx);
  vec2 i1=(x0.x>x0.y)?vec2(1.0,0.0):vec2(0.0,1.0);
  vec4 x12=x0.xyxy+C.xxzz; x12.xy-=i1; i=mod(i,289.0);
  vec3 p=permute(permute(i.y+vec3(0.0,i1.y,1.0))+i.x+vec3(0.0,i1.x,1.0));
  vec3 m=max(0.5-vec3(dot(x0,x0),dot(x12.xy,x12.xy),dot(x12.zw,x12.zw)),0.0);
  m=m*m; m=m*m;
  vec3 x=2.0*fract(p*C.www)-1.0; vec3 h=abs(x)-0.5; vec3 ox=floor(x+0.5); vec3 a0=x-ox;
  m*=1.79284291400159-0.85373472095314*(a0*a0+h*h);
  vec3 g; g.x=a0.x*x0.x+h.x*x0.y; g.yz=a0.yz*x12.xz+h.yz*x12.yw;
  return 130.0*dot(m,g);
}
struct ColorStop{vec3 color;float position;};
#define COLOR_RAMP(colors,factor,finalColor){int index=0;for(int i=0;i<2;i++){ColorStop c=colors[i];bool b=c.position<=factor;index=int(mix(float(index),float(i),float(b)));}ColorStop c=colors[index];ColorStop n=colors[index+1];float r=n.position-c.position;float l=(factor-c.position)/r;finalColor=mix(c.color,n.color,l);}
void main(){
  vec2 uv=gl_FragCoord.xy/uResolution;
  ColorStop colors[3];
  colors[0]=ColorStop(uColorStops[0],0.0);colors[1]=ColorStop(uColorStops[1],0.5);colors[2]=ColorStop(uColorStops[2],1.0);
  vec3 ramp;COLOR_RAMP(colors,uv.x,ramp);
  float h=snoise(vec2(uv.x*2.0+uTime*0.1,uTime*0.25))*0.5*uAmplitude;
  h=exp(h);h=(uv.y*2.0-h+0.2);float intensity=0.6*h;
  float mid=0.20;
  float alpha=smoothstep(mid-uBlend*0.5,mid+uBlend*0.5,intensity);
  vec3 col=intensity*ramp+vec3(0.05,0.03,0.012)*alpha;
  fragColor=vec4(col*alpha,alpha);
}`;
    var gl;
    try {
      gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: true });
      if (!gl) throw new Error('no webgl2');
    } catch (e) {
      document.body.classList.add('hero-fallback');
      return;
    }
    function shader(type, src) {
      var s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    }
    var prog;
    try {
      prog = gl.createProgram();
      gl.attachShader(prog, shader(gl.VERTEX_SHADER, VERT));
      gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, FRAG));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('link');
    } catch (e) {
      document.body.classList.add('hero-fallback');
      return;
    }
    gl.useProgram(prog);
    var vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, 'position');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    var U = function (n) { return gl.getUniformLocation(prog, n); };
    var uTime = U('uTime'), uAmp = U('uAmplitude'), uStops = U('uColorStops'),
        uRes = U('uResolution'), uBlend = U('uBlend');
    gl.uniform1f(uAmp, 1.0);
    gl.uniform1f(uBlend, 0.5);
    gl.uniform3fv(uStops, new Float32Array(STOPS[0].concat(STOPS[1], STOPS[2])));
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    function resize() {
      var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      var w = Math.max(1, Math.floor(canvas.clientWidth * dpr));
      var h = Math.max(1, Math.floor(canvas.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w; canvas.height = h;
        gl.viewport(0, 0, w, h);
        gl.uniform2f(uRes, w, h);
      }
    }
    window.addEventListener('resize', resize);
    window.addEventListener('load', resize);
    if ('ResizeObserver' in window && canvas.parentElement) {
      new ResizeObserver(resize).observe(canvas.parentElement);
    }
    resize();
    var visible = true;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; }).observe(canvas);
    }
    var t0 = performance.now();
    function frame(now) {
      requestAnimationFrame(frame);
      if (!visible || document.hidden) return;
      gl.uniform1f(uTime, (now - t0) * 0.001); // original drift rate
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    if (reduce) {
      gl.uniform1f(uTime, 8.0);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    } else {
      requestAnimationFrame(frame);
    }
  })(); } catch (err) { document.body.classList.add('hero-fallback'); }

  /* Scroll reveal. */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* Animated counters. */
  var counters = document.querySelectorAll('[data-count]');
  function countUp(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    var suffix = el.getAttribute('data-suffix') || '';
    if (reduce || !isFinite(target)) { el.textContent = target + suffix; return; }
    var start = performance.now(), dur = 1200;
    (function tick(t) {
      var p = Math.min(1, (t - start) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * e) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    })(start);
  }
  if ('IntersectionObserver' in window && !reduce) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { countUp(e.target); cio.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { cio.observe(el); });
  } else {
    counters.forEach(countUp);
  }

  /* Terminal typing loop (real commands). */
  var cmds = ['hellochusquis', 'hellochusquis --quick', 'hellochusquis web', 'hellochusquis api --port 8080'];
  var cmdEl = document.getElementById('typed-cmd');
  var ci = 0;
  function typeCmd(text, done) {
    var i = 0;
    cmdEl.textContent = '';
    var iv = setInterval(function () {
      cmdEl.textContent = text.slice(0, ++i);
      if (i >= text.length) { clearInterval(iv); setTimeout(done, 1800); }
    }, 55);
  }
  if (cmdEl && !reduce) {
    (function loop() { typeCmd(cmds[ci % cmds.length], function () { ci++; loop(); }); })();
  }

  /* Copy buttons. */
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy');
      function ok() {
        btn.classList.add('copied');
        var old = btn.textContent;
        btn.textContent = 'copied';
        setTimeout(function () { btn.classList.remove('copied'); btn.textContent = old; }, 1400);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(ok, ok);
      } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
        ok();
      }
    });
  });
})();
