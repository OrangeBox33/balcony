#!/usr/bin/env python3
"""Сани над городом: внизу домики с жёлтыми окнами, на небе луна и звёзды.
Слева направо пролетают сани с Дедом Морозом и оленями, за ними тянется хвост искорок.
Из трубы идёт дымок. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 130
MS = 60
GROUND = 13
rng = random.Random(21)

SNOW = (200, 205, 235)
WIN = (255, 190, 50)
MOON = (255, 235, 150)
STAR = (190, 190, 240)
SMOKE = (120, 120, 140)

# домики: (x, верх, строки); W — снег на крыше, h — стена, y — окно, d — дверь
HOUSES = [
    (0, 9, [
        ".WWWW.",
        "rrrrrr",
        ".hyhy.",
        ".hhdh.",
    ], (90, 60, 150)),
    (7, 8, [
        ".WWWWWW.",
        "rrrrrrrr",
        ".hyhhyh.",
        ".hhhhhh.",
        ".hyhdhh.",
    ], (50, 95, 160)),
    (16, 9, [
        ".WWW.",
        "rrrrr",
        ".yhy.",
        ".hdh.",
    ], (140, 55, 60)),
    (21, 8, [
        ".WWWWW.",
        "rrrrrrr",
        ".hyhyh.",
        ".hhhhh.",
        ".hyhdh.",
    ], (50, 120, 115)),
]
ROOF = (150, 40, 25)
CHIMNEY = (12, 7)            # труба на втором домике (x, y)

STARS = [(2, 1), (6, 3), (10, 0), (13, 2), (17, 4), (25, 0), (8, 5), (27, 4), (4, 6), (15, 0)]
STAR_PH = [rng.random() for _ in STARS]
MOON_C = (22.0, 2.4)

# сани лицом вправо: r — шуба/шапка, s — лицо, W — борода, b — мешок, R — сани, g — полозья
SLEIGH = [
    "...rr....",
    ".bbsWW...",
    ".bbrWr..R",
    "RRRRRRRR.",
    ".gggggggg",
]
SLEIGH_PAL = {"r": (230, 0, 20), "s": (255, 135, 80), "W": (255, 255, 255), "b": (40, 90, 255),
              "R": (180, 20, 10), "g": (255, 190, 40)}
# олень лицом вправо, две фазы галопа
DEER = [
    [
        "....a.a",
        ".....a.",
        ".....nn",
        "wnnnnn.",
        ".nnnnn.",
        ".n...n.",
    ],
    [
        "....a.a",
        ".....a.",
        ".....nn",
        "wnnnnn.",
        ".nnnnn.",
        "n.....n",
    ],
]
DEER_PAL = {"n": (180, 95, 35), "a": (235, 190, 110), "w": (255, 255, 255)}
REIN = (255, 190, 40)
NOSE = (255, 0, 0)

SPEED = 0.44                 # пикселей за кадр
X0 = -28                     # сани целиком за левым краем
SPARK_COLORS = [(255, 210, 90), (255, 255, 220), (255, 170, 40)]


def sleigh_pos(t):
    x = X0 + t * SPEED
    y = 3.0 - 1.6 * (t / N) + 0.6 * math.sin(2 * math.pi * t / 43)
    return x, y


# искры: родились за санями, медленно оседают и гаснут
SPARKS = []
for t in range(N):
    x, y = sleigh_pos(t)
    for _ in range(2 if t % 2 else 1):
        SPARKS.append({
            "t0": t,
            "x": x + rng.uniform(-0.5, 0.5),
            "y": y + rng.uniform(2.5, 4.5),
            "vx": rng.uniform(-0.12, 0.02),
            "vy": rng.uniform(0.0, 0.07),
            "life": rng.randint(12, 20),
            "c": rng.choice(SPARK_COLORS),
            "tw": rng.random(),
        })


def draw_town(f, t):
    for x in range(W):
        f.set(x, GROUND, SNOW)
    for hx, hy, rows, wall in HOUSES:
        f.sprite(rows, hx, hy, pal={"W": SNOW, "r": ROOF, "h": wall, "y": WIN, "d": (130, 70, 20)})
    cx, cy = CHIMNEY
    f.set(cx, cy, ROOF)
    f.set(cx, cy - 1, SNOW)
    # дымок: три клубочка поднимаются и рассеиваются, по кругу
    for k in range(3):
        p = ((t / N) * 3 + k / 3) % 1
        sx = cx + 0.6 * math.sin(p * 5 + k) + p * 1.5
        sy = cy - 2 - p * 6
        if sy >= 0:
            f.set(round(sx), round(sy), gen.scale(SMOKE, 1 - 0.3 * p))


def draw_sky(f, t):
    for (sx, sy), ph in zip(STARS, STAR_PH):
        k = 0.55 + 0.45 * math.sin(2 * math.pi * (t * 3 / N + ph))
        f.set(sx, sy, gen.scale(STAR, 0.5 + 0.5 * k))
    mx, my = MOON_C
    for y in range(0, 6):
        for x in range(18, 27):
            d1 = (x - mx) ** 2 + (y - my) ** 2
            d2 = (x - mx - 1.3) ** 2 + (y - my + 0.6) ** 2
            if d1 <= 6.5 and d2 > 3.6:
                f.set(x, y, MOON)


def draw_sleigh(f, t):
    x, y = sleigh_pos(t)
    xi, yi = round(x), round(y)
    f.sprite(SLEIGH, xi, yi, pal=SLEIGH_PAL)
    step = (t // 3) % 2
    for k, dx in enumerate((11, 20)):
        dy = -1 if k == 0 else -2         # вожак чуть выше — упряжка тянет вверх
        f.sprite(DEER[(step + k) % 2], xi + dx, yi + dy, pal=DEER_PAL)
    # поводья: от передка саней к первому оленю и от него к вожаку
    for px, py in ((9, 2), (10, 1), (18, 1), (19, 0)):
        f.set(xi + px, yi + py, REIN)
    f.set(xi + 27, yi, NOSE)                # красный нос у вожака


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        draw_sky(f, t)
        draw_town(f, t)
        for s in SPARKS:
            for tt in (t, t + N):            # искры, родившиеся в конце петли, догорают в её начале
                age = tt - s["t0"]
                if 0 <= age < s["life"]:
                    px = s["x"] + s["vx"] * age
                    py = s["y"] + s["vy"] * age
                    k = 1 - age / s["life"]
                    k *= 0.7 + 0.3 * math.sin(2 * math.pi * (age / 5 + s["tw"]))
                    if py < GROUND:
                        f.add(round(px), round(py), gen.scale(s["c"], 0.35 + 0.65 * k))
        draw_sleigh(f, t)
        frames.append(f)
    gen.save("sleigh_city", frames, MS)


if __name__ == "__main__":
    build()
