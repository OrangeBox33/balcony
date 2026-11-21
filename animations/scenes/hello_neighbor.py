#!/usr/bin/env python3
"""Бегущая строка «ПРИВЕТ, СОСЕД!», потом появляется ладонь и машет."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MSG = "ПРИВЕТ, СОСЕД!"

# ладонь задана геометрией (в координатах кисти, запястье в нуле, вверх — минус y),
# поэтому при повороте пальцы остаются тонкими линиями с просветами
SKIN = (255, 120, 60)
NAIL = (255, 190, 140)
SLEEVE = (0, 90, 255)
CUFF = (220, 220, 240)
FINGERS = [((-3.0, -5.6), (-3.5, -9.4)),        # кисть потоньше: ладонь 7 px, пальцы через 1 px
           ((-1.0, -6.0), (-1.1, -11.2)),
           ((1.0, -6.0), (1.1, -10.8)),
           ((3.0, -5.6), (3.5, -9.2))]
THUMB = ((2.6, -2.4), (5.6, -4.9))


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    k = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - k * dx, py - ay - k * dy), k


def in_palm(x, y):
    if not (-7.0 <= y <= -0.4):
        return False
    half = 3.4
    if y > -2.5:
        half -= (y + 2.5) * 0.9      # к запястью сужается
    return abs(x) <= half


def warm(t):
    """Тёплый градиент вдоль строки, медленно переливается."""
    def c(x, y):
        h = 0.02 + 0.07 * (0.5 + 0.5 * math.sin((x + t) * 0.18))
        return gen.hsv(h, 1.0, 1.0)
    return c


def hand(f, cx, wy, ang, sleeve=True):
    """Кисть, повёрнутая на ang вокруг запястья (cx, wy)."""
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(H):
        for x in range(W):
            u, v = x - cx, y - wy
            hx, hy = ca * u + sa * v, -sa * u + ca * v
            c = None
            if in_palm(hx, hy):
                c = SKIN
            for seg in FINGERS + [THUMB]:
                d, k = seg_dist(hx, hy, *seg)
                if d < 0.55:
                    c = NAIL if k > 0.93 and seg is not THUMB else SKIN
            if c:
                f.set(x, y, c)
    if sleeve:
        for x in range(cx - 3, cx + 4):
            f.set(x, wy, CUFF)
            for yy in range(wy + 1, wy + 4):
                f.set(x, yy, SLEEVE)


def build():
    frames, ms = [], []
    tw = gen.text_width(MSG, gen.FONT7)

    # 1. бегущая строка
    for t in range(tw + W + 1):
        f = gen.Frame()
        f.text(MSG, W - t, 3, warm(t), gen.FONT7)
        frames.append(f)
        ms.append(40)      # бегущая строка в 1,5 раза быстрее (было 60 мс на шаг)

    # 2. ладонь поднимается снизу
    CX, WY = 13, 12
    for k in range(H, -1, -2):
        f = gen.Frame()
        hand(f, CX, WY + k, 0)
        frames.append(f)
        ms.append(60)
    for _ in range(4):
        f = gen.Frame()
        hand(f, CX, WY, 0)
        frames.append(f)
        ms.append(80)

    # 3. машет: качание вокруг запястья, по бокам дуги-«взмахи»
    N = 40
    for t in range(N):
        a = math.sin(t * 2 * math.pi / 10)
        tilt = 0.4 * a
        f = gen.Frame()
        hand(f, CX, WY, tilt)
        if abs(a) > 0.8:
            side = 1 if a > 0 else -1
            xs = CX + 9 if side > 0 else CX - 9
            for yy, dx in ((1, 0), (2, 1), (3, 1), (4, 0)):
                f.set(xs + side * dx, yy, (255, 220, 120))
        frames.append(f)
        ms.append(70)

    # 4. опускается
    for k in range(0, H + 2, 2):
        f = gen.Frame()
        hand(f, CX, WY + k, 0)
        frames.append(f)
        ms.append(60)
    for _ in range(4):
        frames.append(gen.Frame())
        ms.append(80)

    gen.save("hello_neighbor", frames, ms)


if __name__ == "__main__":
    build()
