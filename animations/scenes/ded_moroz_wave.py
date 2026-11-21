#!/usr/bin/env python3
"""Дед Мороз крупным планом: шапка с опушкой, борода, румяные щёки.
Машет рукой в варежке, посреди петли подмигивает; вокруг идёт снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 112                 # 7 взмахов по 16 кадров
MS = 70
WAVE = 16
rng = random.Random(11)

FX = 3                  # левый край лица
# 15 колонок, центр — колонка 7
FACE = [
    "....rrrrrrr....",
    "..rrrrrrrrrrr..",
    ".rrrrrrrrrrrrr.",
    "WWWWWWWWWWWWWWW",
    "Wss.sssssss.ssW",
    "bss.sssssss.ssb",
    "bsppssnnnssppsb",
    "bbWWWWWsWWWWWbb",
    "bWWbbsmmmsbbWWb",
    "bbbbbbbbbbbbbbb",
    ".bbbbbbbbbbbbb.",
    "..bbbbbbbbbbb..",
    "...bbbbbbbbb...",
    ".....bbbbb.....",
]
PAL = {
    "r": (220, 0, 20),
    "W": (255, 255, 255),
    "b": (200, 205, 235),       # борода чуть темнее и голубее усов — чтобы усы читались
    "s": (255, 135, 80),
    "p": (255, 40, 90),
    "n": (255, 70, 50),
    "m": (200, 0, 30),
}
COAT = (170, 0, 15)
MITTEN = (255, 30, 30)
CUFF = (255, 255, 255)

SNOW = (200, 200, 230)
SNOW_DIM = (120, 120, 150)


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((1, 2, 2))            # оборотов падения за петлю
        self.amp = rng.uniform(0.3, 1.0)
        self.sph = rng.random()
        self.bright = rng.random() < 0.55

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * 2 / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(18)]


def line(f, x0, y0, x1, y1, c, thick=False):
    n = int(max(abs(x1 - x0), abs(y1 - y0), 1) * 2)
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = y0 + (y1 - y0) * i / n
        f.set(round(x), round(y), c)
        if thick:
            f.set(round(x) + 1, round(y), c)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fl in FLAKES:
            x, y = fl.pos(t)
            f.set(x, y, SNOW if fl.bright else SNOW_DIM)

        # шуба: плечи под бородой
        for y in range(9, H):
            half = 8 + min(2, y - 9)
            for x in range(round(FX + 7 - half), round(FX + 7 + half) + 1):
                f.set(x, y, COAT)
        for y in range(9, H):            # белая опушка по центру шубы
            f.set(FX + 7, y, CUFF)

        # рука: от плеча к локтю, предплечье качается вокруг локтя
        sx, sy = FX + 16, 11
        ex, ey = FX + 19, 8
        a = 0.5 * math.sin(2 * math.pi * t / WAVE)
        hx = ex + 3.2 * math.sin(a)
        hy = ey - 3.2 * math.cos(a)
        line(f, sx, sy, ex, ey, COAT, thick=True)
        line(f, ex, ey, hx, hy, COAT, thick=True)
        # варежка: кулачок 3×3 + большой палец, белая манжета
        mx, my = round(hx), round(hy)
        f.set(mx, my + 1, CUFF)
        f.set(mx + 1, my + 1, CUFF)
        for dx in (-1, 0, 1):
            for dy in (-3, -2, -1):
                f.set(mx + dx + (1 if dx == -1 and dy == -3 else 0), my + dy, MITTEN)
        f.set(mx - 2, my - 1, MITTEN)      # большой палец

        # лицо
        f.sprite(FACE, FX, 0, pal=PAL)
        # глаза: открытый — 1×2, подмигнувший — чёрточка 2×1 со «смешинкой»
        wink = 52 <= t < 64
        f.set(FX + 3, 4, (0, 0, 0))
        f.set(FX + 3, 5, (0, 0, 0))
        if wink:
            f.set(FX + 11, 4, PAL["s"])
            f.set(FX + 10, 5, (0, 0, 0))
            f.set(FX + 11, 5, (0, 0, 0))
            f.set(FX + 12, 5, (0, 0, 0))
            # улыбка шире
            f.set(FX + 5, 8, PAL["m"])
            f.set(FX + 9, 8, PAL["m"])
        else:
            f.set(FX + 11, 4, (0, 0, 0))
            f.set(FX + 11, 5, (0, 0, 0))
        frames.append(f)
    gen.save("ded_moroz_wave", frames, MS)


if __name__ == "__main__":
    build()
