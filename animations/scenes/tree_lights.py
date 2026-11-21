#!/usr/bin/env python3
"""Ёлка горит: на верхушке мягко светится жёлтая звезда, по ёлке разноцветные огоньки
по очереди плавно разгораются и гаснут, внизу три подарка с бантиками. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 128
MS = 65
CX = 13

# ярусы: строка → полуширина; три яруса с «уступами»
HALF = {3: 1, 4: 2, 5: 3, 6: 2, 7: 3, 8: 4, 9: 5, 10: 4, 11: 5, 12: 6}
TIER_EDGE = {5, 9, 12}                 # нижние строки ярусов — чуть темнее
NEEDLE = (10, 125, 35)
NEEDLE_DARK = (0, 95, 30)
TRUNK = (150, 75, 20)

STAR = (255, 200, 30)
STAR_CORE = (255, 240, 150)
STAR_PX = [(13, 0), (12, 1), (14, 1), (13, 2)]
STAR_GLOW = [(12, 0), (14, 0), (12, 2), (14, 2), (11, 1), (15, 1)]

LIGHTS_C = [(255, 25, 15), (255, 170, 0), (40, 100, 255), (230, 40, 200)]

GIFTS = [                                # слева и справа от ёлки, маленький — под ней
    ([".y.y.",
      "RRyRR",
      "yyyyy",
      "RRyRR"], 1, 10, {"R": (180, 15, 20), "y": (230, 165, 0)}),
    ([".W.W.",
      "bbWbb",
      "WWWWW",
      "bbWbb"], 21, 10, {"b": (20, 65, 210), "W": (180, 180, 210)}),
    (["mmm",
      "pmp"], 16, 12, {"p": (140, 0, 210), "m": (255, 100, 180)}),
]


def tree_cells():
    return [(x, y) for y, hw in HALF.items() for x in range(CX - hw, CX + hw + 1)]


def light_positions():
    """Огоньки косой решёткой по всей ёлке; зажигаются в перемешанном (но постоянном) порядке."""
    pts = [(x, y) for x, y in tree_cells() if y >= 4 and (x + 2 * y) % 4 == 1]
    pts = [p for p in pts if not (15 <= p[0] <= 19 and p[1] == 12)]   # под маленьким подарком
    random.Random(4).shuffle(pts)
    return pts


LIGHTS = light_positions()
WIDTH = 0.55


def bump(p):
    """Плавный «вдох»: 0 → 1 → 0 на отрезке длиной WIDTH, остальное время 0."""
    p %= 1.0
    if p > WIDTH:
        return 0.0
    return 0.5 - 0.5 * math.cos(2 * math.pi * p / WIDTH)


def draw_tree(f):
    for x, y in tree_cells():
        f.set(x, y, NEEDLE_DARK if y in TIER_EDGE else NEEDLE)
    for x in range(CX - 1, CX + 2):
        f.set(x, 13, TRUNK)


def draw_star(f, k, glow):
    for p in STAR_GLOW:
        f.set(*p, gen.scale(STAR, glow))
    for p in STAR_PX:
        f.set(*p, gen.scale(STAR, k))
    f.set(13, 1, gen.scale(STAR_CORE, k))


def draw_gifts(f):
    for rows, x, y, pal in GIFTS:
        f.sprite(rows, x, y, pal=pal)


def build():
    frames = []
    n = len(LIGHTS)
    for t in range(N):
        f = gen.Frame()
        draw_tree(f)
        for i, (x, y) in enumerate(LIGHTS):
            v = bump(t * 2 / N - i / n)            # каждый огонёк дважды за петлю, все в разное время
            f.set(x, y, gen.scale(LIGHTS_C[i % len(LIGHTS_C)], 0.4 + 0.6 * v))
        s = 0.5 - 0.5 * math.cos(2 * math.pi * t * 2 / N)
        draw_star(f, 0.78 + 0.22 * s, 0.35 + 0.35 * s)
        draw_gifts(f)
        frames.append(f)
    gen.save("tree_lights", frames, MS)


if __name__ == "__main__":
    build()
