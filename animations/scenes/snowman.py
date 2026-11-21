#!/usr/bin/env python3
"""Снеговик: три кома, ведро на голове, нос-морковка, руки-веточки. Падает снег и понемногу
ложится на ведро; изредка снеговик моргает, а потом машет рукой — и стряхивает снег с ведра.
Петля без шва."""
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
rng = random.Random(11)

SNOW = (215, 220, 245)      # снеговик
SHADE = (140, 150, 195)     # тень на комах
GROUND_C = (110, 115, 150)
DRIFT = (140, 145, 180)
FLAKE = (200, 200, 225)
FLAKE_DIM = (125, 125, 150)
BUCKET = (30, 85, 230)
BRIM = (80, 140, 255)
CARROT = (255, 105, 0)
CARROT_TIP = (220, 60, 0)
STICK = (165, 90, 30)
BLACK = (0, 0, 0)

# комы: строка → (x0, x1); центр фигуры 13.5
BODY = {
    3: (11, 16), 4: (11, 16), 5: (12, 15),                  # голова
    6: (11, 16), 7: (10, 17), 8: (11, 16),                  # средний ком
    9: (10, 17), 10: (9, 18), 11: (9, 18), 12: (10, 17),    # нижний ком
}
# тень снизу-справа на каждом коме — так комы отделяются друг от друга
SHADE_PX = {(14, 5), (15, 5),
            (17, 7), (14, 8), (15, 8), (16, 8),
            (18, 10), (18, 11), (14, 12), (15, 12), (16, 12), (17, 12)}
EYES = [(12, 3), (15, 3)]
BUTTONS = [(13, 7), (14, 10)]
BLINKS = [(40, 4), (100, 4)]          # (начало, длительность)

# ведро: верх 12..15 в строке 1, поля 11..16 в строке 2; снег копится в строке 0
CAP_X = [13, 15, 12, 14]
CAP_AT = [10, 34, 58, 82]             # кадры, когда очередная снежинка ложится на ведро
WAVE_T0, WAVE_LEN = 108, 44           # машет рукой
DROP_T = WAVE_T0 + 8                  # снег соскальзывает с ведра

REST = math.radians(42)               # руки в покое — вверх-в-стороны


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((2, 2, 3))
        self.sw = rng.choice((1, 2))
        self.amp = rng.uniform(0.4, 1.0)
        self.sph = rng.random()
        self.bright = rng.random() < 0.6

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(18)]


def arm(f, sx, sy, a, side):
    """Ветка из плеча (sx, sy) под углом a над горизонтом; side=-1 влево, +1 вправо."""
    dx, dy = side * math.cos(a), -math.sin(a)
    pts = [(round(sx + dx * i), round(sy + dy * i)) for i in range(4)]
    for p in pts:
        f.set(*p, STICK)
    tx, ty = sx + dx * 3, sy + dy * 3
    for da in (0.75, -0.75):          # два пальца-развилки на конце
        b = a + da
        f.set(round(tx + side * math.cos(b) * 1.2), round(ty - math.sin(b) * 1.2), STICK)


def wave_angle(t):
    d = t - WAVE_T0
    if not 0 <= d < WAVE_LEN:
        return REST
    p = d / WAVE_LEN
    lift = math.sin(math.pi * p) ** 0.6                     # поднял — помахал — опустил
    swing = math.sin(2 * math.pi * 3 * p) * 0.35 * math.sin(math.pi * p)
    return REST + lift * math.radians(28) + swing


def cap_flakes(f, t):
    """Снег на ведре: копится по снежинке, на взмахе соскальзывает по бокам."""
    for i, (x, at) in enumerate(zip(CAP_X, CAP_AT)):
        if at <= t < DROP_T + i:
            f.set(x, 0, SNOW)
        d = t - (DROP_T + i)
        if 0 <= d < 9:
            side = -1 if x <= 13 else 1
            edge = 11 if side < 0 else 16
            px = edge + side * (1 + d * 0.35) + side * (x in (12, 15))
            py = d * 0.9
            f.set(round(px), round(py), gen.scale(FLAKE, 1 - d / 14))


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()

        for fl in FLAKES:
            x, y = fl.pos(t)
            if 0 <= y < GROUND:
                f.set(x, y, FLAKE if fl.bright else FLAKE_DIM)

        for x in range(W):
            f.set(x, GROUND, GROUND_C)
        for x in (2, 3, 4, 23, 24):          # сугробы
            f.set(x, GROUND - 1, DRIFT)

        for y, (x0, x1) in BODY.items():
            for x in range(x0, x1 + 1):
                f.set(x, y, SHADE if (x, y) in SHADE_PX else SNOW)

        closed = any(s <= t < s + n for s, n in BLINKS)
        for e in EYES:
            f.set(*e, SNOW if closed else BLACK)
        for b in BUTTONS:
            f.set(*b, BLACK)
        f.set(14, 4, CARROT)
        f.set(15, 4, CARROT)
        f.set(16, 4, CARROT)
        f.set(17, 4, CARROT_TIP)

        for x in range(12, 16):
            f.set(x, 1, BUCKET)
        for x in range(11, 17):
            f.set(x, 2, BRIM)
        cap_flakes(f, t)

        arm(f, 9, 7, REST, -1)
        arm(f, 18, 7, wave_angle(t), 1)
        frames.append(f)
    gen.save("snowman", frames, MS)


if __name__ == "__main__":
    build()
