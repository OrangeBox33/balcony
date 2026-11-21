#!/usr/bin/env python3
"""Пережимает готовые GIF текущим кодировщиком gen.write_gif — без перерисовки сцен.

    python3 tools/repack.py                 # все animations/wled/*.gif
    python3 tools/repack.py earth fireplace # только эти
    python3 tools/repack.py --full ...      # обратно в режим «каждый кадр целиком»

Картинка не меняется: после записи файл декодируется заново и сверяется попиксельно
и по длительности с исходным; при расхождении исходный файл возвращается на место.
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import gen  # noqa: E402


def timeline(path):
    """Кадры как их видно на экране + паузы (в сотых); одинаковые подряд склеены."""
    im = Image.open(path)
    out = []
    for i in range(im.n_frames):
        im.seek(i)
        f = im.convert("RGB").tobytes()
        cs = int(im.info.get("duration", 0) / 10)
        if out and out[-1][0] == f:
            out[-1][1] += cs
        else:
            out.append([f, cs])
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    delta = "--full" not in sys.argv
    files = [gen.OUT / f"{n}.gif" for n in args] if args else sorted(gen.OUT.glob("*.gif"))
    before = after = 0
    for p in files:
        src = p.read_bytes()
        tl = timeline(p)
        w, h = Image.open(p).size
        imgs = [Image.frombytes("RGB", (w, h), f) for f, _ in tl]
        gen.write_gif(imgs, p, [cs * 10 for _, cs in tl], delta=delta)
        if timeline(p) != tl:
            p.write_bytes(src)
            print(f"{p.stem:22s} РАСХОЖДЕНИЕ — оставлен исходный файл")
            continue
        n = p.stat().st_size
        before += len(src)
        after += n
        print(f"{p.stem:22s} {len(src) / 1024:6.1f} → {n / 1024:6.1f} КБ  ({len(tl)} разных кадров)")
    print(f"\nвсего {before / 1024:.0f} → {after / 1024:.0f} КБ")


if __name__ == "__main__":
    main()
