#!/usr/bin/env python3
"""Леденцы-тросточки: три красно-белых леденца в снегу, полоски медленно «едут» вверх,
как на парикмахерском столбике. Вокруг мерцают звёздочки. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 120
MS = 70
P = 4.0                     # период полосок вдоль леденца, px
LAPS = 3                    # на сколько периодов полоски сдвигаются за петлю
SNOW_Y = 13

RED = (235, 0, 25)
WHITE = (235, 235, 235)
SNOW = (140, 145, 175)
STAR_WARM = (255, 210, 110)
STAR_COLD = (190, 205, 255)

# (x ствола, y верха ствола, радиус ручки, куда смотрит ручка: -1 влево, +1 вправо, сдвиг фазы)
CANES = [(8.0, 5.5, 2.0, -1, 0.0), (16.0, 3.5, 2.0, -1, 1.3), (24.0, 6.5, 2.0, -1, 2.6)]


def cane_path(x0, yh, rh, side):
    """Осевая линия: снизу вверх по стволу, дугой через верх, чуть вниз на кончике."""
    pts = []
    y = SNOW_Y + 0.5
    while y > yh:
        pts.append((x0, y))
        y -= 0.1
    cx = x0 + side * rh
    for i in range(61):
        a = math.pi * i / 60
        pts.append((cx - side * rh * math.cos(a), yh - rh * math.sin(a)))
    for i in range(1, 9):
        pts.append((x0 + side * 2 * rh, yh + i * 0.1))
    s, out = 0.0, []
    for i, p in enumerate(pts):
        if i:
            s += math.dist(p, pts[i - 1])
        out.append((p, s))
    return out


def cane_map(x0, yh, rh, side):
    """Для каждого пикселя леденца: длина вдоль пути и боковое смещение."""
    path = cane_path(x0, yh, rh, side)
    m = {}
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            best = None
            for i, ((qx, qy), s) in enumerate(path):
                d = math.hypot(px - qx, py - qy)
                if best is None or d < best[0]:
                    best = (d, i, s)
            d, i, s = best
            if d > 1.05 or py > SNOW_Y:
                continue
            # знак смещения: слева/справа от направления пути
            (ax, ay), _ = path[max(0, i - 1)]
            (bx, by), _ = path[min(len(path) - 1, i + 1)]
            tx, ty = bx - ax, by - ay
            sign = 1 if (tx * (py - ay) - ty * (px - ax)) > 0 else -1
            m[(x, y)] = (s, sign * d)
    return m


MAPS = [cane_map(*c[:4]) for c in CANES]

rng = random.Random(11)
# звёздочки в пустых местах: (x, y, цвет, фаза, сколько вспышек за петлю)
STAR_POS = [(1, 1), (5, 0), (9, 2), (19, 1), (25, 2), (12, 10), (20, 11), (1, 10), (27, 8), (27, 4), (6, 11)]
STARS = [(x, y, rng.choice((STAR_WARM, STAR_COLD)), rng.random(), rng.choice((2, 3))) for x, y in STAR_POS]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for x in range(W):
            f.set(x, SNOW_Y, SNOW)

        # звёзды: мягко разгораются и гаснут, на пике — крестик
        for x, y, col, ph, k in STARS:
            b = math.sin(math.pi * ((t * k / N + ph) % 1)) ** 3
            if b < 0.12:
                continue
            f.set(x, y, gen.scale(col, 0.6 + 0.4 * b))
            if b > 0.75:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    f.set(x + dx, y + dy, gen.scale(col, 0.55))

        phase = t * P * LAPS / N
        for (x0, yh, rh, side, ph), m in zip(CANES, MAPS):
            for (x, y), (s, n) in m.items():
                v = (s + 0.6 * n - phase + ph) / P
                w = 0.5 + 1.8 * math.cos(2 * math.pi * v)      # 1 — красная полоска, 0 — белая
                w = round(min(1.0, max(0.0, w)) * 2) / 2
                f.set(x, y, tuple(int(a + (b - a) * w) for a, b in zip(WHITE, RED)))
        frames.append(f)
    gen.save("candy_canes_v2", frames, MS)


if __name__ == "__main__":
    build()
