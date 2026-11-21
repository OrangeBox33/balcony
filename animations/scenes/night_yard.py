#!/usr/bin/env python3
"""Ночь, обычный двор: пятиэтажка с окнами, у подъезда лампочка, горит фонарь над скамейкой,
машина под снегом, падает снег. В окнах изредка зажигается и гаснет свет. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160
MS = 60
GROUND = 13
rng = random.Random(5)

SNOW = (200, 200, 225)
SNOW_DIM = (130, 130, 150)
SNOW_WARM = (255, 215, 140)
LIT_GROUND = (235, 200, 140)

POLE = (110, 110, 125)
LAMP = (255, 225, 130)
POLE_X, LAMP_X, LAMP_Y = 9, 11, 3

HOUSE_X0 = 15               # пятиэтажка: x 15..27, этажи — ряды окон 3,5,7,9,11
WALL = (90, 100, 150)
WIN_COLORS = [(255, 190, 60), (255, 150, 40), (255, 220, 120)]
TV = (110, 150, 255)
DOOR_X = 21

CAR = [
    ".WWWW..",
    ".RccRw.",
    "RRRRRRR",
    ".x...x.",
]
CAR_PAL = {"W": SNOW, "w": SNOW_DIM, "c": (0, 0, 0), "R": (170, 30, 10), "x": (110, 110, 120)}

BENCH = [
    "WWWW",
    "nnnn",
    "x..x",
]
BENCH_PAL = {"W": SNOW_WARM, "n": (170, 85, 25), "x": (130, 110, 90)}


def in_cone(x, y):
    if y <= LAMP_Y:
        return 0.0
    half = (y - LAMP_Y) * 0.55 + 0.3
    return max(0.0, 1 - abs(x - LAMP_X) / half)


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((2, 3, 3, 4))        # оборотов падения за петлю
        self.sw = rng.choice((1, 2, 3))           # покачиваний за петлю
        self.amp = rng.uniform(0.4, 1.2)
        self.sph = rng.random()
        self.bright = rng.random() < 0.6

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(20)]

# окна: (x, y) → цвет; часть окон по ходу петли включается/выключается
WINDOWS = {}
for fy in (3, 5, 7, 9, 11):
    for wx in range(HOUSE_X0 + 1, W, 2):
        if fy == 11 and wx == DOOR_X:
            continue
        WINDOWS[(wx, fy)] = None
cells = list(WINDOWS)
for c in cells:
    WINDOWS[c] = rng.choice(WIN_COLORS) if rng.random() < 0.45 else None
TV_WIN = (18, 7)
WINDOWS[TV_WIN] = TV
# окна, которые щёлкают выключателем: (клетка, кадр включения, кадр выключения)
TOGGLES = []
for c in rng.sample([c for c in cells if c != TV_WIN], 7):
    on = rng.randrange(N)
    TOGGLES.append((c, on, (on + rng.randrange(40, 100)) % N, rng.choice(WIN_COLORS)))


def window_color(c, t):
    for cc, on, off, col in TOGGLES:
        if cc == c:
            active = (on <= t < off) if on < off else (t >= on or t < off)
            return col if active else None
    if c == TV_WIN:   # телевизор мерцает
        k = 0.75 + 0.25 * math.sin(2 * math.pi * t * 9 / N) * math.sin(2 * math.pi * t * 4 / N)
        return gen.scale(TV, k)
    return WINDOWS[c]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()

        # снег на земле: под фонарём тёплый
        for x in range(W):
            c = in_cone(x, GROUND)
            f.set(x, GROUND, tuple(int(a + (b - a) * c) for a, b in zip(SNOW_DIM, LIT_GROUND)))

        # снежинки — позади предметов
        for fl in FLAKES:
            x, y = fl.pos(t)
            if 0 <= y < GROUND:
                f.set(x, y, SNOW_WARM if in_cone(x, y) > 0.15 else (SNOW if fl.bright else SNOW_DIM))

        # пятиэтажка
        for y in range(3, GROUND):
            for x in range(HOUSE_X0, W):
                f.set(x, y, WALL)
        for x in range(HOUSE_X0, W):
            f.set(x, 2, SNOW)                    # снег на крыше
        for c in WINDOWS:
            col = window_color(c, t)
            f.set(c[0], c[1], col if col else (0, 0, 0))
        f.set(DOOR_X, 11, (0, 0, 0))             # подъезд
        f.set(DOOR_X, 12, (0, 0, 0))
        f.set(DOOR_X, 10, LAMP)                  # лампочка над подъездом

        # фонарь
        for y in range(LAMP_Y - 1, GROUND):
            f.set(POLE_X, y, POLE)
        f.set(POLE_X + 1, LAMP_Y - 1, POLE)
        f.set(LAMP_X, LAMP_Y - 1, POLE)
        f.set(POLE_X + 1, LAMP_Y - 2, SNOW)      # снег на колпаке
        f.set(LAMP_X, LAMP_Y - 2, SNOW)
        f.set(LAMP_X, LAMP_Y, LAMP)

        f.sprite(BENCH, 10, 10, pal=BENCH_PAL)
        f.sprite(CAR, 0, 9, pal=CAR_PAL)
        frames.append(f)
    gen.save("night_yard", frames, MS)


if __name__ == "__main__":
    build()
