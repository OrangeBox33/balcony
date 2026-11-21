#!/usr/bin/env python3
"""Северное сияние: над заснеженными холмами с парой ёлочек колышутся ленты сияния —
зелёная и бирюзовая с фиолетовым краем, как занавеска на ветру. Звёзды тихо мигают.
Все движения — синусы по фазе t/N с целыми частотами, петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 180                 # 10,8 с
MS = 60
TAU = 2 * math.pi

SNOW_TOP = (225, 232, 255)
SNOW_BODY = (140, 150, 200)
FIR = {"G": (25, 115, 50), "g": (40, 150, 65), "w": (225, 235, 255), "n": (130, 75, 30)}
FIR_A = [
    "..w..",
    ".wgw.",
    ".Ggg.",
    "wGggw",
    "GGggg",
    "..n..",
]
FIR_B = [
    ".w.",
    "wgw",
    "Ggg",
    "Ggg",
    ".n.",
]

# ленты: (база нижнего края, высота занавески, цвета снизу вверх (кромка, тело, верх),
#         волны кромки [(амплитуда, длина волны, оборотов за петлю, фаза)],
#         яркость вдоль ленты (длина волны, оборотов, фаза, порог: >0 — лента рвётся на куски))
BANDS = [
    (7.4, 5.0, ((150, 255, 170), (30, 235, 100), (150, 40, 225)),
     [(1.0, 30, 1, 0.0), (0.45, 12, -2, 1.3)], (21, -1, 0.4, -0.6)),
    (3.2, 2.6, ((140, 255, 240), (0, 200, 200), (140, 50, 235)),
     [(0.8, 26, -1, 2.0), (0.4, 9, 2, 0.2)], (28, 1, 2.2, 0.05)),
]


def hill(x):
    return 11.2 + 0.9 * math.sin(x * 0.28 + 0.9) + 0.45 * math.sin(x * 0.75 + 2.4)


def top_row(x):
    return math.ceil(hill(x + 0.5))


def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def aurora(x, y, t):
    """Цвет неба в точке (без звёзд): ленты сияния."""
    out = [0.0, 0.0, 0.0]
    ph = t / N
    for base, L, (c_edge, c_mid, c_top), waves, (lam, m, p, cut) in BANDS:
        edge = base + sum(a * math.sin(TAU * (x / wl + k * ph) + q) for a, wl, k, q in waves)
        d = edge - y                       # высота над нижним краем
        if d < -0.5 or d > L:
            continue
        along = math.sin(TAU * (x / lam + m * ph) + p)
        along = (along - cut) / (1 - cut)
        if along <= 0:
            continue
        along = 0.35 + 0.65 * along
        # вертикальные лучи — «складки занавески», бегут вдоль ленты
        rays = 0.5 + 0.5 * math.sin(TAU * (x / 3.6 + 2 * ph) + 1.6 * math.sin(TAU * (x / 14 - ph)))
        if d < 0.9:
            v, c = along, c_edge
        else:
            k = (d - 0.9) / (L - 0.9)
            v = along * (1 - 0.55 * k) * (0.35 + 0.65 * rays)
            c = mix(c_mid, c_top, min(1, k * 1.25) ** 1.5)
        if v < 0.3:
            continue
        bright = 0.35 + 0.65 * v
        for i in range(3):          # max, а не сумма: на перекрытии нет белой «каши»
            out[i] = max(out[i], c[i] * bright)
    if out == [0.0, 0.0, 0.0]:
        return None
    # квантуем, чтобы цветов было немного
    return tuple(min(255, int(round(v / 24) * 24)) for v in out)


def build():
    rnd = random.Random(42)
    stars = []
    while len(stars) < 13:
        sx, sy = rnd.randrange(W), rnd.randrange(0, 9)
        if sy >= top_row(sx) - 1 or any(abs(sx - a) + abs(sy - b) < 3 for a, b, *_ in stars):
            continue
        stars.append((sx, sy, rnd.uniform(0, TAU), rnd.choice((2, 3, 4, 5))))

    frames = []
    for t in range(N):
        f = gen.Frame()
        for sx, sy, ph, k in stars:
            v = 0.5 + 0.5 * math.sin(TAU * k * t / N + ph)
            if v > 0.25:
                # яркость звезды ступенями — меньше разных цветов в GIF
                f.set(sx, sy, gen.scale((210, 210, 255), round((0.5 + 0.5 * v) * 8) / 8))
        for y in range(H):
            for x in range(W):
                c = aurora(x, y, t)
                if c and max(c) >= 80:
                    f.set(x, y, c)
        # ёлочки на холмах
        for rows, x0 in ((FIR_A, 4), (FIR_B, 21)):
            c = x0 + len(rows[0]) // 2
            f.sprite(rows, x0, top_row(c) - len(rows) + 1, pal=FIR)
        for x in range(W):
            ty = top_row(x)
            for y in range(ty, H):
                f.set(x, y, SNOW_TOP if y == ty else SNOW_BODY)
        frames.append(f)
    gen.save("aurora", frames, MS)


if __name__ == "__main__":
    build()
