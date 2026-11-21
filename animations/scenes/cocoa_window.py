#!/usr/bin/env python3
"""Окно с какао, вид изнутри: деревянная рама, за стеклом ночь и снег, на подоконнике
кружка какао с зефирками и паром, рядом горит свечка. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160
MS = 60
rng = random.Random(31)

SKY = (5, 15, 95)
WOOD = (170, 80, 20)
SILL = (210, 115, 40)
WALL = (125, 50, 10)
DRIFT = (170, 175, 210)
SNOW = (170, 175, 215)
SNOW_DIM = (115, 120, 165)
MOON = (255, 230, 150)

MUG = (215, 20, 35)
MUG_BAND = (240, 235, 235)
COCOA = (160, 70, 15)
MALLOW = (250, 250, 250)
MALLOW_PINK = (255, 140, 180)
STEAM = (235, 225, 225)

CANDLE = (245, 230, 185)
HOLDER = (240, 200, 40)

SILL_Y = 11
GLASS_Y0, GLASS_Y1 = 1, 10             # стекло: ряды 1..10
PANES = [(1, 12), (15, 26)]            # стекло по x; между ними — переплёт 13..14
MUG_X = 4                              # кружка: x 4..8, ряды 7..10, ручка справа
CANDLE_X = 20                          # свеча 2 px: x 20..21, ряды 7..9, подсвечник в ряду 10


def in_glass(x, y):
    return GLASS_Y0 <= y <= GLASS_Y1 and any(a <= x <= b for a, b in PANES)


def mix(a, b, k):
    k = min(1.0, max(0.0, k))
    return tuple(int(p + (q - p) * k) for p, q in zip(a, b))


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((2, 3, 3))
        self.sw = rng.choice((1, 2))
        self.amp = rng.uniform(0.4, 1.0)
        self.sph = rng.random()
        self.bright = rng.random() < 0.6

    def pos(self, t):
        span = GLASS_Y1 + 2
        y = (self.ph * span + t * self.k * span / N) % span
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(16)]
# сугроб снаружи у нижнего края стекла
DRIFT_H = {x: (2 if x in (2, 3, 4, 9, 10, 17, 18, 19, 24, 25) else 1) for x in range(W)}

# пар: две струйки над кружкой (x основания, частота покачивания, фаза)
STEAMS = [(5.5, 2, 0.0), (7.5, 3, 0.45)]
STEAM_TOP = 1


def steam(f, t):
    """Струйки непрерывные, плавно извиваются; вверх по ним бегут светлые сгустки."""
    pix = set()
    for x0, k, ph in STEAMS:
        for y in range(STEAM_TOP, 6):
            h = (5.5 - y) / (5.5 - STEAM_TOP)                     # 0 у кружки, 1 вверху
            sway = (0.3 + 1.1 * h) * math.sin(2 * math.pi * (y * 0.2 - t * k / N + ph))
            puls = 0.5 + 0.5 * math.sin(2 * math.pi * (y * 0.25 - t * (k + 2) / N + ph))
            b = (0.6 + 0.4 * puls) * (1 - 0.5 * h)
            x = round(x0 + sway)
            if in_glass(x, y):
                f.set(x, y, mix(SKY, STEAM, b))
                pix.add((x, y))
    return pix


def candle(f, t):
    # свеча и подсвечник
    for y in range(7, 10):
        f.set(CANDLE_X, y, CANDLE)
        f.set(CANDLE_X + 1, y, gen.scale(CANDLE, 0.85))
    for x in range(CANDLE_X - 1, CANDLE_X + 3):
        f.set(x, 10, HOLDER)
    # огонёк: основание оранжевое, язычок жёлтый, кончик чуть качается и дрожит
    p = 2 * math.pi * t / N
    flick = 0.5 + 0.25 * math.sin(p * 7) + 0.15 * math.sin(p * 13 + 1) + 0.1 * math.sin(p * 23 + 2)
    sway = math.sin(p * 3) * 0.6 + math.sin(p * 11) * 0.25
    f.set(CANDLE_X, 6, (255, 120 + int(40 * flick), 0))
    f.set(CANDLE_X + 1, 6, (255, 100 + int(40 * flick), 0))
    tx = CANDLE_X + (1 if sway > 0.15 else 0)
    f.set(tx, 5, (255, 210, 90 + int(80 * flick)))
    if flick > 0.62:                                  # язычок иногда вытягивается
        f.set(tx, 4, (255, 170, 30))
    return flick


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        # ночное небо за стеклом
        for y in range(GLASS_Y0, GLASS_Y1 + 1):
            for x in range(W):
                if in_glass(x, y):
                    f.set(x, y, SKY)
        steam_px = steam(f, t)
        # снег
        for fl in FLAKES:
            x, y = fl.pos(t)
            if in_glass(x, y) and (x, y) not in steam_px:
                f.set(x, y, SNOW if fl.bright else SNOW_DIM)
        for x, y in ((24, 2), (25, 2), (23, 3), (23, 4), (24, 5), (25, 5)):   # месяц-«С»
            f.set(x, y, MOON)
        for x, h in DRIFT_H.items():
            for dy in range(h):
                if in_glass(x, GLASS_Y1 - dy):
                    f.set(x, GLASS_Y1 - dy, DRIFT)

        # рама
        for x in range(W):
            f.set(x, 0, WOOD)
        for y in range(SILL_Y):
            f.set(0, y, WOOD)
            f.set(W - 1, y, WOOD)
            f.set(13, y, WOOD)
            f.set(14, y, WOOD)

        flick = candle(f, t)

        # подоконник: под свечой тёплое пятно, дышит вместе с огоньком
        for x in range(W):
            glow = max(0.0, 1 - abs(x - CANDLE_X - 0.5) / 4.5) * (0.35 + 0.3 * flick)
            f.set(x, SILL_Y, mix(SILL, (255, 175, 80), glow))
            f.set(x, SILL_Y + 1, WALL)                # торец доски; ниже — тёмная комната

        # кружка
        for y in range(7, 11):
            for x in range(MUG_X, MUG_X + 5):
                f.set(x, y, MUG_BAND if y == 8 else MUG)
        for x in range(MUG_X + 1, MUG_X + 4):
            f.set(x, 7, COCOA)
        for x, y in ((MUG_X + 5, 7), (MUG_X + 6, 8), (MUG_X + 5, 9)):
            f.set(x, y, MUG)
        # зефирки чуть покачиваются на какао
        bob = math.sin(2 * math.pi * t * 2 / N)
        f.set(MUG_X + 1, 6 if bob > -0.3 else 7, MALLOW)
        f.set(MUG_X + 3, 6 if bob < 0.3 else 7, MALLOW_PINK)
        f.set(MUG_X + 2, 7, MALLOW)
        frames.append(f)
    gen.save("cocoa_window", frames, MS)


if __name__ == "__main__":
    build()
