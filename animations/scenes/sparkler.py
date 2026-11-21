#!/usr/bin/env python3
"""Бенгальский огонь: варежка держит палочку, огонёк ползёт вниз и разбрасывает золотые
искры (лучики, развилки, вспышки), догорает и гаснет — в руке появляется новая палочка,
она вспыхивает в начале петли. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 150                 # кадров в петле (9 с)
MS = 60
rng = random.Random(150)

BURN_END = 124          # к этому кадру огонёк доползает до низа
OUT_END = 131           # догорел и погас
SWAP = (138, 146)       # старая палочка тает, новая проявляется

A = (8.5, 10.8)         # палочка: от кулака...
B = (22.5, 2.8)         # ...до кончика
U_START, U_END = 1.0, 0.36

WIRE = (110, 104, 104)       # сгоревшая часть — тусклая серая
COAT = (165, 135, 100)       # ещё не сгоревший состав
MITTEN = [
    "...MM",
    ".MMMM",
    "MMSMM",
    "MMMMM",
    ".WWW.",
]
MITTEN_PAL = {"M": (40, 90, 235), "S": (230, 235, 255), "W": (235, 235, 240)}
MITTEN_X, MITTEN_Y = 5, 9


def at(u):
    return A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u


STICK = []                      # пиксели палочки с параметром u
for i in range(80):
    u = 0.05 + 0.95 * i / 79
    x, y = at(u)
    p = (round(x - 0.5), round(y - 0.5))
    if not STICK or STICK[-1][0] != p:
        STICK.append((p, u))


def flame_u(t):
    if t <= BURN_END:
        return U_START - (U_START - U_END) * t / BURN_END
    return U_END


def put(f, x, y, c):
    x, y = round(x), round(y)
    if 0 <= x < W and 0 <= y < H:
        o = f.px[y][x]
        f.px[y][x] = tuple(max(a, b) for a, b in zip(o, c))


class Spark:
    def __init__(self, born, big=False):
        self.born = born
        u = flame_u(born)
        self.ox, self.oy = at(u)
        self.ang = rng.uniform(0, 2 * math.pi)
        self.v = rng.uniform(0.75, 1.25) * (1.25 if big else 1)
        self.life = rng.randrange(3, 8)
        self.branch = rng.random() < 0.35
        self.blink = rng.random() < 0.4
        self.bang = rng.uniform(0.45, 0.8)


SPARKS = []
for t in range(OUT_END):
    if t < 3:
        n = 7                                   # вспышка при поджигании
    elif t > BURN_END:
        n = rng.choice((0, 0, 1, 1, 2))         # догорает, искр всё меньше
    else:
        n = rng.choice((3, 3, 4, 5))
    for _ in range(n):
        SPARKS.append(Spark(t, big=t < 3))


def spark_color(k):
    """k — доля прожитой жизни: белый → золото → оранжевый."""
    if k < 0.3:
        return (255, 245, 190)
    if k < 0.6:
        return (255, 195, 45)
    return gen.scale((255, 120, 0), 1 - 0.3 * (k - 0.6) / 0.4)


def draw_spark(f, s, t):
    age = t - s.born
    if age < 0 or age > s.life:
        return
    k = age / s.life
    dx, dy = math.cos(s.ang), math.sin(s.ang)
    r = 0.8 + s.v * age
    fall = 0.04 * age * age                     # искры чуть оседают вниз
    hx, hy = s.ox + dx * r, s.oy + dy * r + fall
    if age == s.life:                           # в конце — либо вспышка-звёздочка, либо гаснет
        if s.blink:
            put(f, hx, hy, (255, 255, 230))
        return
    if s.branch and k >= 0.5:                   # развилка: кончик расходится на два
        for sg in (-1, 1):
            a = s.ang + sg * s.bang
            put(f, hx + math.cos(a) * 0.9, hy + math.sin(a) * 0.9, spark_color(k))
        put(f, hx, hy, spark_color(k + 0.2))
    else:
        put(f, hx, hy, spark_color(k))
    # хвостик-лучик к центру
    for back in ((1.0, 2.0) if k < 0.5 else (1.0,)):
        if r - back > 0.7:
            put(f, hx - dx * back, hy - dy * back, spark_color(min(1, k + 0.35)))


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        uf = flame_u(t)
        burning = t <= OUT_END
        # палочка
        if t < SWAP[0]:
            stick_k, new = 1.0, False
        elif t < (SWAP[0] + SWAP[1]) // 2:
            stick_k, new = 1 - (t - SWAP[0]) / ((SWAP[1] - SWAP[0]) / 2), False
        elif t < SWAP[1]:
            stick_k, new = (t - (SWAP[0] + SWAP[1]) // 2) / ((SWAP[1] - SWAP[0]) / 2), True
        else:
            stick_k, new = 1.0, True
        for (x, y), u in STICK:
            if new:
                c = COAT
            elif u > uf + 0.1:
                c = WIRE
            elif u > uf:                        # только что прогорело — ещё раскалено
                c = (255, 70, 0) if burning else (150, 35, 0)
            else:
                c = COAT
            if stick_k < 1:
                c = gen.scale(c, 0.55 + 0.45 * stick_k) if stick_k > 0.15 else (0, 0, 0)
            f.set(x, y, c)
        # огонёк
        if burning:
            fx, fy = at(uf)
            fade = 1.0 if t <= BURN_END else 1 - (t - BURN_END) / (OUT_END - BURN_END + 1)
            pulse = 0.85 + 0.15 * math.sin(t * 1.9)
            for ddx in (-1, 0, 1):
                for ddy in (-1, 0, 1):
                    glow = (255, 210, 90) if ddx == 0 or ddy == 0 else (255, 140, 20)
                    put(f, fx + ddx - 0.5, fy + ddy - 0.5, gen.scale(glow, fade * pulse))
            put(f, fx - 0.5, fy - 0.5, gen.scale((255, 255, 235), max(fade, 0.5)))
        elif t < SWAP[0]:                       # погасший кончик ещё тлеет
            fx, fy = at(uf)
            g = 1 - (t - OUT_END) / (SWAP[0] - OUT_END)
            if g > 0.2:
                put(f, fx - 0.5, fy - 0.5, gen.scale((255, 60, 0), 0.4 + 0.6 * g))
        for s in SPARKS:
            draw_spark(f, s, t)
        f.sprite(MITTEN, MITTEN_X, MITTEN_Y, pal=MITTEN_PAL)
        frames.append(f)
    gen.save("sparkler", frames, MS)


if __name__ == "__main__":
    build()
