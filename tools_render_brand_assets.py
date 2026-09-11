from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ubuntu/HelloChusquis')
ASSETS = ROOT / 'docs' / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)

BG = '#0a0a0c'
TEXT = '#f1efe9'
MUTED = '#a3a0b0'
GRID = '#26262e'
AMBER = '#f5a623'
GREEN = '#34d399'

try:
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
    TINY = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
    MONO = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 10)
except OSError:
    FONT = SMALL = TINY = MONO = ImageFont.load_default()


def centered(draw, box, text, font, fill):
    x1, y1, x2, y2 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((x1 + x2 - (bbox[2] - bbox[0])) / 2, (y1 + y2 - (bbox[3] - bbox[1])) / 2), text, font=font, fill=fill)


def chart_accuracy():
    im = Image.new('RGB', (1120, 600), BG)
    d = ImageDraw.Draw(im)
    centered(d, (0, 20, 1120, 48), 'Factual accuracy: bare model vs + MDknowledge', FONT, TEXT)
    plot_left, plot_top, plot_right, plot_bottom = 88, 56, 1096, 496
    for y, label in [(386, '25%'), (276, '50%'), (166, '75%'), (56, '100%')]:
        d.line((plot_left, y, plot_right, y), fill=GRID, width=2)
        d.text((plot_left - 12, y - 10), label, font=SMALL, fill=MUTED, anchor='ra')
    groups = [
        ('~1B*', '55→90%', 55, 90, AMBER),
        ('3B', '86→100%', 86, 100, GREEN),
        ('~8B*', '92→99%', 92, 99, AMBER),
        ('~32B*', '97→100%', 97, 100, AMBER),
    ]
    scale = (plot_bottom - plot_top) / 100
    xs = [180, 450, 720, 990]
    for x, (name, change, bare, kb, accent) in zip(xs, groups):
        bare_h = bare * scale
        kb_h = kb * scale
        d.rounded_rectangle((x - 48, plot_bottom - bare_h, x - 10, plot_bottom), radius=6, fill=MUTED)
        d.rounded_rectangle((x + 10, plot_bottom - kb_h, x + 48, plot_bottom), radius=6, fill=accent)
        centered(d, (x - 70, 510, x + 70, 535), name, FONT, TEXT)
        centered(d, (x - 90, 540, x + 90, 562), change, TINY, MUTED)
    d.ellipse((776, 25, 786, 35), fill=MUTED)
    d.text((796, 21), 'bare', font=SMALL, fill=MUTED)
    d.ellipse((886, 25, 896, 35), fill=AMBER)
    d.text((906, 21), '+ KB', font=SMALL, fill=MUTED)
    d.text((88, 580), '35-question factual probe. 3B measured on qwen2.5-coder:3b; * projected (same retrieval coverage).', font=TINY, fill=MUTED)
    im.save(ASSETS / 'kb-accuracy.png', optimize=True)


def chart_latency():
    im = Image.new('RGB', (1120, 528), BG)
    d = ImageDraw.Draw(im)
    centered(d, (0, 20, 1120, 48), 'v5.2 latency wins (seconds, log scale)', FONT, TEXT)
    plot_left, plot_top, plot_right, plot_bottom = 88, 56, 1096, 432
    for y, label in [(56, '100s'), (178, '10s'), (300, '1s'), (422, '0.1s')]:
        d.line((plot_left, y, plot_right, y), fill=GRID, width=2)
        d.text((plot_left - 12, y - 10), label, font=SMALL, fill=MUTED, anchor='ra')
    groups = [('KB ingest', '64s→0.5s', 64, .5), ('browser fail', '30s→0.2s', 30, .2), ('search worst', '9.6s→6.2s', 9.6, 6.2)]
    # Map log10 seconds from 0.1 to 100 over plot height.
    import math
    def y_for(seconds):
        return plot_bottom - ((math.log10(seconds) + 1) / 3) * (plot_bottom - plot_top)
    xs = [260, 560, 860]
    for x, (name, change, before, after) in zip(xs, groups):
        d.rounded_rectangle((x - 56, y_for(before), x - 10, plot_bottom), radius=6, fill=MUTED)
        d.rounded_rectangle((x + 10, y_for(after), x + 56, plot_bottom), radius=6, fill=GREEN)
        centered(d, (x - 100, 452, x + 100, 476), name, FONT, TEXT)
        centered(d, (x - 100, 480, x + 100, 502), change, TINY, MUTED)
    d.ellipse((776, 25, 786, 35), fill=MUTED)
    d.text((796, 21), 'before', font=SMALL, fill=MUTED)
    d.ellipse((896, 25, 906, 35), fill=GREEN)
    d.text((916, 21), 'v5.2', font=SMALL, fill=MUTED)
    im.save(ASSETS / 'v52-latency.png', optimize=True)


def favicon():
    source = Image.open(ROOT / 'docs' / 'logo-primary.png').convert('RGBA')
    alpha = source.getchannel('A')
    bbox = alpha.getbbox()
    if bbox:
        source = source.crop(bbox)
    source.thumbnail((56, 56), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (64, 64), (5, 5, 4, 255))
    canvas.alpha_composite(source, ((64 - source.width) // 2, (64 - source.height) // 2))
    canvas.save(ROOT / 'docs' / 'favicon.png', optimize=True)
    canvas.save(ROOT / 'docs' / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == '__main__':
    chart_accuracy()
    chart_latency()
    favicon()
    print('rendered chart PNGs and favicon assets')
