#!/usr/bin/env python3
"""
Лист кадров анимации «как на диодах» — чтобы посмотреть её глазами (через просмотр PNG).

    python3 animations/tools/sheet.py volcano              → /tmp-подобный путь печатается
    python3 animations/tools/sheet.py volcano out.png --every 2 --cols 6
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("out", nargs="?")
ap.add_argument("--every", type=int, default=0, help="брать каждый N-й кадр (по умолчанию — чтобы влезло ~36)")
ap.add_argument("--cols", type=int, default=6)
ap.add_argument("--start", type=int, default=0)
a = ap.parse_args()

im = Image.open(gen.OUT / f"{a.name}.gif")
n = im.n_frames
every = a.every or max(1, (n - a.start + 35) // 36)
idx = list(range(a.start, n, every))
tiles = []
for i in idx:
    im.seek(i)
    t = gen.led_preview(im.convert("RGB"), 9)
    d = ImageDraw.Draw(t)
    d.text((3, 1), str(i), fill=(255, 255, 0))
    tiles.append(t)
tw, th = tiles[0].size
cols = min(a.cols, len(tiles))
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 4), rows * (th + 4)), (70, 0, 70))
for k, t in enumerate(tiles):
    sheet.paste(t, ((k % cols) * (tw + 4), (k // cols) * (th + 4)))
out = Path(a.out) if a.out else gen.HERE / "tools" / "sheets" / f"{a.name}.png"
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out)
print(f"{out}  ({n} кадров, показан каждый {every}-й)")
