#!/usr/bin/env python3
"""Камин и носки: каменный камин, в топке на поленьях мерцает огонь, на полке висят
три красных носка (из одного торчит леденец-тросточка), по полу бегают тёплые блики. Петля без шва."""
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

# ---------------------------------------------------------------- огонь (как campfire, только маленький)

RAMP = [
    (0.00, (0, 0, 0)),
    (0.20, (0, 0, 0)),
    (0.24, (130, 10, 0)),
    (0.40, (220, 35, 0)),
    (0.58, (255, 95, 0)),
    (0.75, (255, 165, 15)),
    (0.90, (255, 220, 70)),
    (1.00, (255, 245, 170)),
]
LEVELS = 24


def heat_color(v):
    v = min(max(v, 0.0), 1.0)
    v = round(v * LEVELS) / LEVELS
    for (a, ca), (b, cb) in zip(RAMP, RAMP[1:]):
        if v <= b:
            k = (v - a) / (b - a) if b > a else 0
            return tuple(int(p + (q - p) * k) for p, q in zip(ca, cb))
    return RAMP[-1][1]


class Noise:
    """Сглаженный шум на решётке, по оси времени замкнут в кольцо длиной period."""

    def __init__(self, nx, period):
        self.nx, self.period = nx, period
        self.v = [[rng.random() for _ in range(period)] for _ in range(nx)]

    def __call__(self, x, z):
        def s(a):
            return a * a * (3 - 2 * a)
        x0, z0 = math.floor(x), math.floor(z)
        fx, fz = s(x - x0), s(z - z0)

        def g(i, k):
            return self.v[i % self.nx][k % self.period]
        a = g(x0, z0) + (g(x0 + 1, z0) - g(x0, z0)) * fx
        b = g(x0, z0 + 1) + (g(x0 + 1, z0 + 1) - g(x0, z0 + 1)) * fx
        return a + (b - a) * fz


OCT = [(Noise(64, 10), 0.6, 0.55, 10, 0.5), (Noise(64, 15), 1.1, 1.0, 15, 0.35), (Noise(64, 25), 1.9, 1.8, 25, 0.15)]
GLINT = Noise(64, 30)

CX = 13.5
HALF = 4.6
BASE_Y = 12.2           # низ пламени (поленья)
SPAN = 4.6              # высота топки


def heat(x, y, t):
    h = (BASE_Y - y) / SPAN
    sway = 0.5 * math.sin(2 * math.pi * (t / N * 3 + y * 0.1))
    n = 0.0
    for noise, fx, fy, period, amp in OCT:
        z = y * fy + t * period / N * 5          # шум бежит вверх; за петлю — 5 кругов
        n += amp * noise((x + sway * (1 + h)) * fx, z % period)
    n /= sum(o[4] for o in OCT)
    hh = max(h, 0)
    width = HALF * (1 - 0.45 * hh) + 0.4
    side = abs(x - CX) / width
    return 1.12 - 1.0 * h + (n - 0.5) * (0.8 + 1.5 * hh) - side * side * 0.75


# ---------------------------------------------------------------- камин

MANTEL_Y = 2
BODY = (2, 25)          # каменный массив по x
TOP, BOTTOM = 3, 12


def in_opening(x, y):
    if y == 8:
        return 10 <= x <= 17
    return 9 <= y <= 12 and 9 <= x <= 18


STONES = [(150, 118, 92), (128, 112, 100), (142, 104, 78), (118, 104, 96), (160, 128, 100)]
SEAM = (96, 80, 70)


def stone_color(x, y):
    row = (y - TOP) // 2
    off = 2 if row % 2 else 0
    bx = (x + off) // 4
    if (x + off) % 4 == 3:          # вертикальный шов между камнями
        return SEAM
    k = (bx * 7 + row * 3) % len(STONES)
    return STONES[k]


SOCK = [
    "WWW..",
    "RRR..",
    "RRR..",
    "RRRR.",
    ".RRRR",
]
SOCK_PAL = {"W": (235, 235, 240), "R": (220, 20, 30)}
SOCK_X = [3, 11, 19]
MANTEL = (190, 105, 45)
MANTEL_EDGE = (220, 140, 70)
FLOOR = (90, 42, 18)
LOG = (125, 58, 22)
LOG_END = (225, 175, 115)


def draw_static(f):
    for x in range(1, 27):
        f.set(x, MANTEL_Y, MANTEL_EDGE if x in (1, 26) else MANTEL)
    for y in range(TOP, BOTTOM + 1):
        for x in range(BODY[0], BODY[1] + 1):
            if not in_opening(x, y):
                f.set(x, y, stone_color(x, y))
    for x in range(W):
        f.set(x, 13, FLOOR)
    for sx in SOCK_X:
        f.sprite(SOCK, sx, TOP, pal=SOCK_PAL)
    # леденец-тросточка из правого носка: крючок над полкой
    cane = [(20, 2), (20, 1), (20, 0), (21, 0), (22, 1)]
    for i, (x, y) in enumerate(cane):
        f.set(x, y, (255, 255, 255) if i % 2 else (255, 20, 30))
    # свечки на полке
    for cx in (3, 24):
        f.set(cx, 1, (210, 200, 180))


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        draw_static(f)
        total = 0.0
        for y in range(8, 12):
            for x in range(9, 19):
                if not in_opening(x, y):
                    continue
                v = heat(x + 0.5, y + 0.5, t)
                total += max(0.0, min(v, 1.0))
                c = heat_color(v)
                if c != (0, 0, 0):
                    f.set(x, y, c)
        # поленья: два бревна с торцами, в щелях тлеет
        for x in range(9, 19):
            if x in (9, 18):
                c = LOG_END
            elif x in (13, 14):
                g = 0.5 + 0.5 * math.sin(2 * math.pi * (t / N * 6 + x * 0.9))
                c = (255, int(70 + 90 * g), 0)
            else:
                c = LOG
            f.set(x, 12, c)
        flick = min(1.0, max(0.0, (total - 9) / 12))     # общая яркость огня 0..1
        # блики на полу перед топкой
        for x in range(4, 24):
            d = abs(x + 0.5 - CX) / 9.5
            n = GLINT(x * 1.6, (t * 30 / N * 4) % 30)
            k = (1 - d * d) * (0.3 + 0.7 * flick) * (1.6 * n - 0.3)
            if k > 0.3:
                k = min(k, 1.0)
                f.set(x, 13, (255, int(90 + 120 * k), int(40 * k)) if k > 0.6 else (int(160 + 95 * k), int(60 + 50 * k), 5))
        # отсвет на камнях у края топки
        for x, y in [(8, 9), (8, 10), (8, 11), (8, 12), (19, 9), (19, 10), (19, 11), (19, 12), (9, 8), (18, 8)]:
            f.add(x, y, (int(70 * flick), int(25 * flick), 0))
        # огоньки свечей
        for i, cx in enumerate((3, 24)):
            g = 0.5 + 0.5 * math.sin(2 * math.pi * (t / N * (7 + 2 * i)) + i)
            f.set(cx, 0, (255, int(150 + 70 * g), int(30 * g)))
        frames.append(f)
    gen.save("fireplace", frames, MS)


if __name__ == "__main__":
    build()
