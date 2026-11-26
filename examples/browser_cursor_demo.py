"""Demo visible del mouse ámbar: movimiento, clics y teclado.

    python3 examples/browser_cursor_demo.py

Abre un Chromium con interfaz, mueve el cursor ámbar hacia tres botones,
hace clic con pulso, escribe con el teclado y guarda una captura.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.browser_agent import _CURSOR_OVERLAY_JS, create_browser_agent

HTML = """
<!doctype html><html><head><meta charset="utf-8"><style>
  body { background:#121316; color:#fafafa; font:16px -apple-system,sans-serif;
         margin:0; padding:48px; }
  h1 { color:#f5a623; margin:0 0 8px; }
  p { color:#9aa0a6; margin:0 0 36px; }
  .row { display:flex; gap:16px; margin-bottom:32px; }
  button { background:#24262b; color:#f5a623; border:2px solid #f5a623;
           border-radius:12px; padding:18px 30px; font-size:18px; cursor:pointer; }
  button:hover { background:#f5a623; color:#121316; }
  input { background:#24262b; color:#fff; border:2px solid #444;
          border-radius:12px; padding:16px 20px; font-size:18px; width:340px; }
  #status { margin-top:28px; font-size:20px; min-height:28px; }
</style></head><body>
<h1>HelloChusquis — demo de mouse</h1>
<p>Observa la flecha ámbar: se mueve, hace clic con pulso y escribe.</p>
<div class="row">
  <button id="one" onclick="hit('Uno')">Uno</button>
  <button id="two" onclick="hit('Dos')">Dos</button>
  <button id="three" onclick="hit('Tres')">Tres</button>
</div>
<input id="name" placeholder="escribe algo aquí">
<div id="status">Esperando…</div>
<script>
  function hit(x) { document.getElementById('status').textContent = 'Clic: ' + x; }
  document.getElementById('name').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') hit('teclado: ' + this.value);
  });
</script>
</body></html>
"""


async def main():
    agent = create_browser_agent(headless=False, slow=True, debug=False)
    if not await agent.start():
        raise SystemExit("No se pudo abrir el navegador")

    await agent.page.set_content(HTML)
    # set_content recrea el documento: volver a montar el cursor asegura
    # que la demostración no dependa de navigation timing.
    await agent.page.evaluate(_CURSOR_OVERLAY_JS)
    await agent._cursor_move(640, 400)
    print("Cursor ámbar listo. Mirando el navegador…", flush=True)

    for selector, label in (("#one", "Uno"), ("#two", "Dos"), ("#three", "Tres")):
        await asyncio.sleep(0.8)
        ok = await agent.click_element(selector=selector)
        print(f"Clic en {label}: {'ok' if ok else 'falló'}", flush=True)

    await asyncio.sleep(0.8)
    await agent.click_element(selector="#name")
    print("Escribiendo con el teclado…", flush=True)
    await agent.type_text("Hola Chusquis")  # sin selector: el cursor no se mueve
    await agent.press_key("Enter")
    await asyncio.sleep(0.5)

    shot = Path.home() / ".hellochusquis" / "workspace" / "cursor_demo.png"
    shot.parent.mkdir(parents=True, exist_ok=True)
    await agent.page.screenshot(path=str(shot))
    status = await agent.page.locator("#status").inner_text()
    print(f"Estado: {status}", flush=True)
    print(f"Captura: {shot}", flush=True)
    await asyncio.sleep(4)  # tiempo para ver el resultado antes de cerrar
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
