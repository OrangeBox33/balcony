#!/usr/bin/env python3
"""Подарок с сюрпризом: коробка вздрагивает раз, другой — сильнее, крышка подпрыгивает,
из щели бьёт фонтанчик золотых звёздочек. Крышка захлопывается, бант качается. Петля."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70

BOX_X, BOX_Y = 8, 8          # корпус 12×6: x 8..19, y 8..13
BODY = (200, 0, 35)
LID = (255, 30, 60)
RIB = (255, 190, 0)
KNOT = (255, 235, 120)
GLOW = (255, 220, 110)

BODY_ROWS = [
    "bbbbbyybbbbb",
    "bbbbbyybbbbb",
    "yyyyyyyyyyyy",
    "bbbbbyybbbbb",
    "bbbbbyybbbbb",
    "bbbbbyybbbbb",
]
LID_ROWS = [
    "LLLLLLyyLLLLLL",
    "LLLLLLyyLLLLLL",
]
# бант: петли качаются относительно узелка (tilt -1/0/1)
BOW = {
    0: [".yy..yy.", "..yKKy.."],
    -1: ["yy..yy..", "..yKKy.."],
    1: ["..yy..yy", "..yKKy.."],
}
PAL = {"b": BODY, "y": RIB, "L": LID, "K": KNOT}

STARS = [(2, 2), (5, 9), (1, 12), (24, 1), (26, 7), (22, 11), (10, 1), (19, 3), (3, 5), (25, 12)]
STAR_COLORS = [(255, 220, 60), (255, 255, 255), (255, 240, 170), (255, 170, 30)]


def draw_body(f, dx, dy):
    f.sprite(BODY_ROWS, BOX_X + dx, BOX_Y + dy, pal=PAL)


def draw_lid(f, dx, dy, lid_up, tilt):
    ly = BOX_Y - 2 + dy - lid_up
    if lid_up > 1:                          # из коробки светит: тёплая полоска над краем
        for x in range(BOX_X + 1, BOX_X + 11):
            f.set(x + dx, BOX_Y - 1 + dy, GLOW)
    f.sprite(LID_ROWS, BOX_X - 1 + dx, ly, pal=PAL)
    bow = BOW[tilt]
    f.sprite(bow, BOX_X + 2 + dx, ly - 2, pal=PAL)


class Spark:
    def __init__(self, rnd, x, y, t0):
        self.x, self.y, self.t0 = x, y, t0
        side = 1 if x > BOX_X + 5.5 else -1
        self.vx = side * rnd.uniform(0.35, 0.95)
        self.vy = rnd.uniform(-0.75, -0.2)
        self.life = rnd.randint(14, 24)
        self.big = rnd.random() < 0.35
        self.c = rnd.choice(STAR_COLORS)
        self.ph = rnd.uniform(0, 6.28)

    def draw(self, f, t):
        age = t - self.t0
        if age < 0 or age >= self.life:
            return
        x = self.x + self.vx * age
        y = self.y + self.vy * age + 0.045 * age * age
        k = 1.0 if age < self.life * 0.5 else 1 - (age - self.life * 0.5) / (self.life * 0.5)
        k *= 0.75 + 0.25 * math.sin(self.ph + age * 1.7)
        c = gen.scale(self.c, max(k, 0))
        ix, iy = round(x), round(y)
        if iy >= BOX_Y and BOX_X - 1 <= ix <= BOX_X + 12:
            return                              # в коробку не залетаем
        f.add(ix, iy, c)
        if self.big and age < self.life * 0.6:
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(ix + ddx, iy + ddy, gen.scale(c, 0.55))


def build():
    rnd = random.Random(5)
    # сценарий: (кадров, сдвиг x, сдвиг y, подъём крышки)
    seq = []
    seq += [(0, 0, 0)] * 14                                    # тишина
    seq += [(1, 0, 0), (0, 0, 0)]                              # раз — чуть
    seq += [(0, 0, 0)] * 12
    seq += [(1, 0, 0), (-1, 0, 0), (1, -1, 0), (-1, 0, 0), (0, 0, 0)]   # два — сильнее, подскок
    seq += [(0, 0, 0)] * 6
    POP = len(seq)
    seq += [(0, 0, 1), (0, 0, 3), (0, 0, 4), (0, 0, 4)]
    seq += [(0, 0, 4 if (k // 3) % 3 else 3) for k in range(22)]   # крышка парит, звёзды летят
    seq += [(0, 0, 3), (0, 0, 2), (0, 0, 0)]                   # хлоп!
    SLAM = len(seq) - 1
    seq += [(0, 0, 0)] * 24                                    # бант качается, пауза
    N = len(seq)

    sparks = []
    for i in range(30):
        t0 = POP + 1 + i * 2 // 3
        sx = BOX_X + 5.5 + rnd.choice((-1, 1)) * rnd.uniform(1.5, 5)
        sparks.append(Spark(rnd, sx, BOX_Y - rnd.uniform(1.5, 3.5), t0))
    assert max(s.t0 + s.life for s in sparks) < N

    star_ph = [rnd.randrange(N) for _ in STARS]
    frames = []
    for t, (dx, dy, lid) in enumerate(seq):
        f = gen.Frame()
        for (sx, sy), ph in zip(STARS, star_ph):
            k = 0.5 + 0.5 * math.cos(2 * math.pi * ((t + ph) / N * 2))
            f.set(sx, sy, gen.scale((170, 170, 210), 0.55 + 0.45 * k))
        # бант качается после хлопка, затухая
        tilt = 0
        a = t - SLAM
        if 0 < a < 22:
            tilt = round(1.4 * math.exp(-a / 9) * math.sin(a * 0.9))
            tilt = max(-1, min(1, tilt))
        elif POP <= t < SLAM:
            tilt = [0, 1, 0, -1][(t // 3) % 4]
        draw_body(f, dx, dy)
        for s in sparks:
            s.draw(f, t)
        draw_lid(f, dx, dy, lid, tilt)
        frames.append(f)
    gen.save("gift_surprise", frames, MS)


if __name__ == "__main__":
    build()
