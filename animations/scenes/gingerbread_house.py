#!/usr/bin/env python3
"""Пряничный домик: крыша в белой глазури с сосульками и мармеладками, окошки светятся,
из трубы идёт дымок, у двери леденец-тросточка. Падает снег. Петля без шва."""
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
rng = random.Random(23)

GINGER = (160, 65, 10)
ICING = (240, 240, 245)
SNOW = (200, 200, 225)
SNOW_DIM = (130, 130, 155)
GROUND_C = (150, 150, 180)
WIN = (255, 205, 80)
DOOR = (230, 40, 90)
KNOB = (255, 210, 60)
BRICK = (190, 45, 20)
SMOKE = (175, 175, 190)
RED = (235, 0, 25)

WALL_X0, WALL_X1, WALL_Y0 = 7, 18, 8
# крыша: ряд → (x от, x до); нижний ряд — свес с глазурью
ROOF = {3: (12, 13), 4: (10, 15), 5: (9, 16), 6: (7, 18), 7: (6, 19)}
EAVE = 7
GUMDROPS = {(11, 5): (240, 0, 40), (15, 6): (0, 200, 40), (13, 4): (255, 170, 0), (9, 6): (180, 0, 230)}
ICICLES = {7: 1, 10: 1, 13: 1, 16: 2, 18: 1}     # x → длина под свесом
WINDOWS = [(8, 9), (11, 9)]                            # левый верхний угол окна 2×2, под ним — подоконник из глазури
DOOR_X = 14                                            # дверь 2×3
CHIMNEY_X = 8                                          # труба 2 px, ряды 3..5, шапка снега в ряду 2
CANE = [  # леденец у двери, ручкой к дому
    ".WR",
    "R.W",
    "..R",
    "..W",
    "..R",
]
CANE_X = 20


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((2, 3, 3))
        self.sw = rng.choice((1, 2, 3))
        self.amp = rng.uniform(0.4, 1.2)
        self.sph = rng.random()
        self.bright = rng.random() < 0.6

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(18)]

PUFF_EVERY = 20               # новый клуб дыма каждые 20 кадров → 8 за петлю
PUFF_LIFE = 46


def smoke(f, t):
    for i in range(N // PUFF_EVERY):
        age = (t - i * PUFF_EVERY) % N
        if age >= PUFF_LIFE:
            continue
        k = age / PUFF_LIFE
        x = CHIMNEY_X + 0.5 - 0.17 * age + 0.6 * math.sin(age * 0.25 + i)
        y = 1.6 - 2.2 * math.sqrt(k)
        c = gen.scale(SMOKE, 1 - 0.35 * k)
        f.set(round(x), round(y), c)
        if k < 0.5:                                  # пока клуб молодой — он пухлее
            f.set(round(x) + 1, round(y), gen.scale(SMOKE, 0.7))


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for x in range(W):
            f.set(x, GROUND, GROUND_C)

        for fl in FLAKES:
            x, y = fl.pos(t)
            if 0 <= y < GROUND:
                f.set(x, y, SNOW if fl.bright else SNOW_DIM)

        smoke(f, t)

        # труба
        for y in range(3, 6):
            f.set(CHIMNEY_X, y, BRICK)
            f.set(CHIMNEY_X + 1, y, BRICK)
        f.set(CHIMNEY_X, 2, ICING)
        f.set(CHIMNEY_X + 1, 2, ICING)

        # стены
        for y in range(WALL_Y0, GROUND):
            for x in range(WALL_X0, WALL_X1 + 1):
                f.set(x, y, GINGER)
        # крыша: пряник с глазурью по краям, нижний ряд — сплошная глазурь
        for y, (a, b) in ROOF.items():
            for x in range(a, b + 1):
                f.set(x, y, ICING if (x in (a, b) or y == EAVE) else GINGER)
        for (x, y), c in GUMDROPS.items():
            f.set(x, y, c)
        # сосульки
        for x, n in ICICLES.items():
            for dy in range(n):
                f.set(x, EAVE + 1 + dy, ICING if dy == 0 else gen.scale(ICING, 0.7))

        # окошки: тёплый свет чуть дышит, у каждого свой ритм
        for i, (wx, wy) in enumerate(WINDOWS):
            k = 0.88 + 0.12 * math.sin(2 * math.pi * (t * (2 + i) / N + i * 0.4))
            for dx in range(2):
                for dy in range(2):
                    f.set(wx + dx, wy + dy, gen.scale(WIN, k))
                f.set(wx + dx, wy + 2, ICING)
        # дверь с ручкой
        for dy in range(3):
            f.set(DOOR_X, 10 + dy, DOOR)
            f.set(DOOR_X + 1, 10 + dy, DOOR)
        f.set(DOOR_X + 1, 11, KNOB)

        f.sprite(CANE, CANE_X, 8, pal={"R": RED, "W": ICING})
        frames.append(f)
    gen.save("gingerbread_house", frames, MS)


if __name__ == "__main__":
    build()
