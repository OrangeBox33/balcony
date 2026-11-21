#!/usr/bin/env python3
"""Снегирь на заснеженной ветке: крутит головой, подпрыгивает, чирикает — над ним всплывает нотка.
Фон — зимнее синее небо (чтобы чёрная шапочка читалась), сверху падают снежинки. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 120
MS = 80
TAU = 2 * math.pi

SKY_TOP = (15, 40, 125)
SKY_BOT = (40, 80, 160)
BARK = (140, 75, 30)
SNOW = (230, 235, 255)
FLAKE = (225, 230, 255)
NOTE = (255, 225, 90)

PAL = {
    "k": (0, 0, 0),
    "x": (150, 150, 170),     # серая спинка
    "r": (255, 35, 25),       # красная грудка
    "W": (245, 245, 250),     # белая полоса на крыле
    "e": (255, 255, 255),     # блик в глазу
    "b": (130, 130, 145),       # клюв
    "l": (120, 70, 40),       # лапки
}

# тело лицом вправо (8 колонок), голова — отдельно, поверх
BODY = [
    "........",
    "........",
    "........",
    "..xrrrr.",
    "kxxrrrrr",
    "kWWrrrrr",
    "kkkrrrr.",
    "k..rrr..",
    "...l.l..",
]
BODY_FLAP = [          # крылышки вверх — в прыжке
    "........",
    "........",
    "kk......",
    ".kxrrrr.",
    ".WWrrrrr",
    "..xrrrrr",
    "..krrrr.",
    "...rrr..",
    "...l.l..",
]
HEADS = {
    "right": [
        "...kkk..",
        "..kkkkk.",
        "..kkkekb",
    ],
    "front": [
        "...kkk..",
        "..kkkkk.",
        "..kekek.",
    ],
    "left": [
        "..kkk...",
        ".kkkkk..",
        "bkekkk..",
    ],
}
# у открытого клюва — щель
OPEN = {"right": ["...kkk..", "..kkkkkb", "..kkkek.", ]}

BIRD_X = 10
BIRD_Y = 2            # верх спрайта; лапки (ряд 8) — на снегу ветки, ряд 10
BRANCH_Y = 11

# сценарий головы по кадрам
def head_dir(t):
    if 18 <= t < 24 or 44 <= t < 50:
        return "front"
    if 24 <= t < 44:
        return "left"
    return "right"


HOP = (58, 68)        # прыжок: кадры
CHIRPS = [(76, 82), (90, 95)]   # клюв открыт
NOTES = [76, 90]      # когда вылетает нотка
NOTE_LIFE = 20
NOTE_SPR = [".##", ".#.", "##.", "##."]

rng = random.Random(41)


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((1, 1, 2))
        self.sw = rng.choice((1, 2))
        self.amp = rng.uniform(0.4, 1.0)
        self.sph = rng.random()

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(TAU * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(10)]


def sky(y):
    k = y / (H - 1)
    return tuple(int(a + (b - a) * k) for a, b in zip(SKY_TOP, SKY_BOT))


def draw_branch(f):
    # ветка чуть поднимается вправо, справа отросток вверх
    for x in range(0, 25):
        y = BRANCH_Y if x < 17 else BRANCH_Y - 1
        f.set(x, y, BARK)
        f.set(x, y + 1, BARK) if x < 6 else None
        if x not in (8, 22):
            f.set(x, y - 1, SNOW)               # снег на ветке
    for i, (x, y) in enumerate([(22, 8), (23, 7), (24, 6)]):
        f.set(x, y + 1, BARK)
        f.set(x, y, SNOW)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for y in range(H):
            c = sky(y)
            for x in range(W):
                f.set(x, y, c)
        for fl in FLAKES:
            x, y = fl.pos(t)
            f.set(x, y, FLAKE)
        draw_branch(f)

        lift = 0
        body = BODY
        if HOP[0] <= t < HOP[1]:
            k = (t - HOP[0]) / (HOP[1] - HOP[0])
            lift = round(2.5 * math.sin(math.pi * k))
            if lift:
                body = BODY_FLAP if (t // 2) % 2 == 0 else BODY
        d = head_dir(t)
        head = HEADS[d]
        if d == "right" and any(a <= t < b for a, b in CHIRPS):
            head = OPEN["right"]
        y0 = BIRD_Y - lift
        f.sprite(body, BIRD_X, y0, pal=PAL)
        f.sprite(head, BIRD_X, y0, pal=PAL)

        for born in NOTES:
            age = t - born
            if 0 <= age < NOTE_LIFE:
                k = age / NOTE_LIFE
                nx = BIRD_X + 8 + round(1.0 * math.sin(age * 0.5))
                ny = round(BIRD_Y - 1 - age * 0.25)
                col = gen.scale(NOTE, 1 - 0.5 * max(0, k - 0.5) * 2)
                f.sprite(NOTE_SPR, nx, ny, pal={"#": col})
        frames.append(f)
    gen.save("bullfinch_v2", frames, MS)


if __name__ == "__main__":
    build()
