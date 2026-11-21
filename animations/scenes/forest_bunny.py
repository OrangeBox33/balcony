#!/usr/bin/env python3
"""Зайчик в ночном лесу: выглядывает из-за большой ёлки, шевелит ушами, моргает,
выходит, делает два прыжка по снегу, сидит, прыгает обратно и прячется. Идёт снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 140
MS = 70
GROUND = 13

SNOW = (200, 200, 225)
SNOW_DIM = (120, 120, 145)
DRIFT = (150, 150, 175)
NEEDLE = (10, 115, 40)
TRUNK = (120, 65, 25)
MOON = (235, 195, 70)
MOON_LIGHT = (255, 230, 130)

TREE_PAL = {"G": NEEDLE, "W": SNOW, "T": TRUNK}

# большая ёлка — нижние лапы до самого снега, за ней прячется зайчик;
# снег на лапах только слева, чтобы белый зайчик не сливался с краем ёлки
TREE_BIG = [
    "....W....",
    "...WGW...",
    "..WGGGW..",
    "...GGG...",
    "..WGGGW..",
    ".WGGGGGG.",
    "..GGGGG..",
    ".WGGGGGG.",
    "WGGGGGGGG",
    ".GGGGGGG.",
    "..GGGGG..",
]
TREE_S = [
    "..W..",
    ".WGW.",
    "..G..",
    ".WGW.",
    "WGGGW",
    "..T..",
]
TREES = [(TREE_BIG, 1), (TREE_S, 23)]

MOON_X, MOON_Y = 21, 1
MOON_SPR = [
    ".MMM.",
    "MLMMM",
    "MMMMM",
    "MMMLM",
    ".MMM.",
]
MOON_PAL = {"M": MOON, "L": MOON_LIGHT}

BUNNY_PAL = {"W": (245, 245, 255), "k": (0, 0, 0), "p": (255, 100, 150)}
EARS = {
    "up": [".W.W.", ".W.W."],
    "left": ["W..W.", ".W.W."],    # левое ушко клонится
    "right": [".W..W", ".W.W."],
}
FACE = ["WWWWW", "WkWkW", "WWpWW", ".WWW.", "WWWWW"]
BH = 7                              # высота зайчика


def bunny_rows(ears="up", blink=False):
    face = FACE[:]
    if blink:
        face[1] = "WWWWW"
    return EARS[ears] + face


HIDE_X = 3                          # за ёлкой (колонки 3..7 закрыты лапами)

# сценарий: (кадров, x от, x до, прыжок?)
PLAN = [
    (10, HIDE_X, HIDE_X, False),     # спрятался
    (10, HIDE_X, 7, False),          # высовывается
    (28, 7, 7, False),               # выглядывает: уши, моргание
    (5, 7, 11, False),               # выходит
    (10, 11, 14, True),              # прыг
    (10, 14, 17, True),              # прыг
    (25, 17, 17, False),             # сидит
    (10, 17, 14, True),
    (10, 14, 11, True),
    (10, 11, HIDE_X, False),         # прячется
    (12, HIDE_X, HIDE_X, False),
]
assert sum(p[0] for p in PLAN) == N

# моменты: моргание и шевеление ушами (кадры от начала петли)
BLINKS = {33, 34, 35, 86, 87, 88}
WIGGLE = [(24, 30), (39, 44), (92, 98)]


def bunny_at(t):
    """(x, подъём над землёй) в кадре t."""
    s = 0
    for n, x0, x1, hop in PLAN:
        if t < s + n:
            k = (t - s) / n
            x = x0 + (x1 - x0) * k
            lift = 2.4 * math.sin(math.pi * k) if hop else 0.0
            return round(x), round(lift)
        s += n
    raise ValueError(t)


rng = random.Random(23)


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((1, 2, 2, 3))        # оборотов падения за петлю — медленно
        self.sw = rng.choice((1, 2, 3))
        self.amp = rng.uniform(0.4, 1.2)
        self.sph = rng.random()
        self.bright = rng.random() < 0.6

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(14)]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        f.sprite(MOON_SPR, MOON_X, MOON_Y, pal=MOON_PAL)
        for fl in FLAKES:
            x, y = fl.pos(t)
            if not fl.bright and 0 <= y < GROUND:
                f.set(x, y, SNOW_DIM)
        for x in range(W):
            f.set(x, GROUND, SNOW_DIM)
        for x in (0, 11, 21, 22):            # сугробики
            f.set(x, GROUND - 1, DRIFT)

        bx, lift = bunny_at(t)
        ears = "up"
        for a, b in WIGGLE:
            if a <= t < b:
                ears = "left" if (t - a) // 2 % 2 == 0 else "right"
        f.sprite(bunny_rows(ears, t in BLINKS), bx, GROUND - BH - lift, pal=BUNNY_PAL)

        for spr, x in TREES:
            f.sprite(spr, x, GROUND - len(spr), pal=TREE_PAL)
        for fl in FLAKES:
            x, y = fl.pos(t)
            if fl.bright and 0 <= y < GROUND:
                f.set(x, y, SNOW)
        frames.append(f)
    gen.save("forest_bunny", frames, MS)


if __name__ == "__main__":
    build()
