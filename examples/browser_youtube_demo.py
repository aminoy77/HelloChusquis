"""Demo real: YouTube con mouse ámbar, clics y teclado.

    python3 examples/browser_youtube_demo.py

Rechaza cookies, busca un vídeo, lo abre y guarda capturas en
~/.hellochusquis/workspace/ para poder mostrarlo.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.browser_agent import create_browser_agent

QUERY = "capybara relaxing"
SHOTS = Path.home() / ".hellochusquis" / "workspace"


async def shot(page, name):
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / name
    await page.screenshot(path=str(path))
    print(f"  captura: {path}", flush=True)


async def main():
    agent = create_browser_agent(headless=False, slow=True, debug=False)
    if not await agent.start():
        raise SystemExit("No se pudo abrir el navegador")

    try:
        print("1/5 Abriendo YouTube…", flush=True)
        await agent.navigate("https://www.youtube.com")
        await asyncio.sleep(1)
        await shot(agent.page, "youtube_demo_1_home.png")

        print("2/5 Rechazando cookies…", flush=True)
        reject = agent.page.get_by_text("Reject all", exact=True)
        if await reject.count() and await reject.nth(0).is_visible():
            print(f"  clic en Reject all: {await agent.click_element(text='Reject all')}", flush=True)
            await asyncio.sleep(1)
        else:
            print("  no apareció el diálogo", flush=True)

        print(f"3/5 Buscando '{QUERY}'…", flush=True)
        clicked = await agent.click_element(selector='input[name="search_query"]')
        print(f"  clic en buscador: {clicked}", flush=True)
        print(f"  escritura: {await agent.type_text(QUERY)}", flush=True)
        await agent.press_key("Enter")
        await asyncio.sleep(2)
        await shot(agent.page, "youtube_demo_2_results.png")

        print("4/5 Abriendo el primer vídeo…", flush=True)
        ready = await agent.wait_for_element(
            'ytd-video-renderer a#video-title', timeout=15
        )
        print(f"  resultados listos: {ready}", flush=True)
        print(f"  clic en vídeo: {await agent.click_element(selector='ytd-video-renderer a#video-title')}", flush=True)
        await asyncio.sleep(3)
        await shot(agent.page, "youtube_demo_3_video.png")

        print("5/5 Estado final", flush=True)
        report = await agent.page_report() or {}
        print(f"  título: {report.get('title')}", flush=True)
        print(f"  vídeo: {report.get('video')}", flush=True)
        await asyncio.sleep(8)  # deja el vídeo abierto para verlo
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
