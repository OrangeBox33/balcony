#!/usr/bin/env python3
"""Кружка какао с зефирками на подоконнике: из неё вьётся пар, за окном ночь и снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 140                 # кадров в петле (8,4 с)
MS = 60
rng = random.Random(140)

FRAME = (170, 95, 40)        # деревянная рама
SILL = (200, 120, 55)
SILL_FRONT = (140, 70, 25)
MULLIONS = (6, 21)           # вертикальные перекладины рамы
SNOW = (140, 160, 220)

MUG = [
    "RCCCCCCCR..",
    "RRRRRRRRRRR",
    "RRRRWRRRR.R",
    "RRRWWWRRR.R",
    "RRRRWRRRRRR",
    "DRRRRRRRD..",
]
MUG_X, MUG_Y = 8, 7          # кружка с ручкой: x 8..18, по центру
MUG_PAL = {"R": (220, 25, 35), "D": (170, 15, 25), "W": (240, 240, 245), "C": (150, 72, 25)}
# зефирки: (x, y, цвет)
MALLOWS = [(10, 7, "w"), (11, 6, "p"), (13, 7, "w"), (14, 6, "w"), (15, 7, "p"), (12, 7, "p")]
MALLOW_PAL = {"w": (245, 245, 250), "p": (255, 130, 170)}


class Flake:
    def __init__(self):
        self.x = rng.uniform(0, W)
        self.y0 = rng.uniform(0, 14)
        self.laps = rng.choice((2, 3))          # сколько раз за петлю пролетит экран
        self.wob = rng.uniform(0.3, 0.8)
        self.ph = rng.uniform(0, 2 * math.pi)
        self.c = gen.scale(SNOW, rng.uniform(0.75, 1.0))


FLAKES = [Flake() for _ in range(13)]


WISPS = [  # x0, амплитуда, сдвигов за петлю, фаза
    (11.0, 1.4, 2, 0.0),
    (14.2, 1.2, 3, 2.2),
]
LAMBDA = 7.0                 # длина волны завитка (строк)


def steam(x, y, t):
    """Яркость пара 0..1 в точке. Два завитка, волна бежит вверх, наверху пар тает."""
    best = 0.0
    for x0, amp, laps, ph in WISPS:
        shift = t / N * LAMBDA * laps * 2          # целое число длин волн за петлю — без шва
        a = amp * (0.5 + 0.5 * (6 - y) / 6)         # наверху завиток шире
        cx = x0 + a * math.sin(2 * math.pi * (y + shift) / LAMBDA + ph)
        d = abs(x + 0.5 - cx)
        puff = 0.5 + 0.5 * math.sin(2 * math.pi * (y + shift) / (LAMBDA / 2) + ph * 2)
        fade = min(1.0, max(0.0, (y + 0.3) / 4.0))
        v = max(0.0, 1 - d / 1.25) * (0.55 + 0.45 * puff) * fade
        best = max(best, v)
    return best


MOON = [".YY.", "YY..", "YY..", ".YY."]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        # снег за окном
        for fl in FLAKES:
            y = (fl.y0 + t / N * 14 * fl.laps) % 14
            x = (fl.x + fl.wob * math.sin(2 * math.pi * t / N * 2 + fl.ph)) % W
            if steam(int(x), int(y), t) < 0.15:
                f.set(int(x), int(y), fl.c)
        f.sprite(MOON, 2, 1, pal={"Y": (255, 220, 120)})
        # рама
        for y in range(12):
            for x in (0, 27) + MULLIONS:
                f.set(x, y, FRAME)
        for x in range(W):
            f.set(x, 12, SILL)
            f.set(x, 13, SILL_FRONT)
        # пар над кружкой (полупрозрачный: поверх рамы прибавляется)
        for y in range(0, 6):
            for x in range(7, 21):
                v = steam(x, y, t)
                if v > 0.25:
                    lv = round((0.6 + 0.4 * v) * 5) / 5
                    c = (int(235 * lv), int(235 * lv), int(245 * lv))
                    o = f.px[y][x]
                    f.set(x, y, tuple(max(a, b) for a, b in zip(o, c)))
        f.sprite(MUG, MUG_X, MUG_Y, pal=MUG_PAL)
        for x, y, k in MALLOWS:
            f.set(x, y, MALLOW_PAL[k])
        frames.append(f)
    gen.save("cocoa", frames, MS)


if __name__ == "__main__":
    build()
