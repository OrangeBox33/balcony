#!/usr/bin/env python3
"""День и ночь: солнце встаёт из левого нижнего угла, человечек просыпается и
делает зарядку; солнце садится, выходит луна, человечек ложится спать — «Z z z»."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
GROUND = (40, 95, 70)       # приглушённая земля, днём и ночью одна и та же

# человечек (лицом к зрителю), ширина 7
MAN = {
    "stand": [
        "..kkk..",
        "..sss..",
        "..sss..",
        "...s...",
        ".rrrrr.",
        "s.rrr.s",
        "s.rrr.s",
        "..bbb..",
        "..b.b..",
        "..b.b..",
        ".xx.xx.",
    ],
    # руки вверх, ноги врозь (прыжок «звёздочка»)
    "jack": [
        "s.kkk.s",
        "s.sss.s",
        ".rsssr.",
        ".r.s.r.",
        "..rrr..",
        "..rrr..",
        "..rrr..",
        "..bbb..",
        ".b...b.",
        "b.....b",
        "x.....x",
    ],
    # потягивается: руки вверх, ноги вместе
    "stretch": [
        "s.kkk.s",
        "s.sss.s",
        ".rsssr.",
        ".r.s.r.",
        "..rrr..",
        "..rrr..",
        "..rrr..",
        "..bbb..",
        "..b.b..",
        "..b.b..",
        ".xx.xx.",
    ],
    # сидит в постели
    "sit": [
        "..kkk..",
        "..sss..",
        "..sss..",
        "...s...",
        "..rrrr.",
        "..rrr.s",
    ],
}

PILLOW = (230, 230, 240)
BLANKET = (0, 90, 255)
BED = (150, 70, 10)


def zglyph(big):
    return ["####", "..#.", ".#..", "####"] if big else ["###", ".#.", "#..", "###"]


BED_X = 19


def draw_bed(f, state, t):
    """state: 'lie' — спит под одеялом, 'sit' — сидит, 'empty' — кровать пустая."""
    x0 = BED_X
    for x in range(x0, W):
        f.set(x, 12, BED)
    f.set(x0, 13, BED)
    f.set(W - 1, 13, BED)
    for y in (8, 9, 10, 11):
        f.set(x0, y, BED)     # спинка у изголовья
    f.set(x0 + 1, 11, PILLOW)
    f.set(x0 + 2, 11, PILLOW)
    f.set(x0 + 1, 10, PILLOW)
    if state == "lie":
        # голова на подушке, тело под одеялом
        f.set(x0 + 2, 9, gen.PAL["k"])
        f.set(x0 + 3, 9, gen.PAL["k"])
        f.set(x0 + 2, 10, gen.PAL["s"])
        f.set(x0 + 3, 10, gen.PAL["s"])
        for x in range(x0 + 4, W):
            f.set(x, 11, BLANKET)
            f.set(x, 10, BLANKET)
        if (t // 6) % 2:      # дыхание: одеяло чуть поднимается
            for x in range(x0 + 5, x0 + 8):
                f.set(x, 9, BLANKET)
    elif state == "sit":
        for x in range(x0 + 4, W):
            f.set(x, 11, BLANKET)
    else:
        for x in range(x0 + 3, W):
            f.set(x, 11, BLANKET)


def draw_sun(f, cx, cy, t, col=(255, 200, 0)):
    for y in range(H):
        for x in range(W):
            if (x - cx) ** 2 + (y - cy) ** 2 <= 6.5:
                f.set(x, y, col)
    ray = (255, 230, 80) if col[1] > 120 else (255, 90, 0)
    rot = (t // 3) % 2
    for k in range(8):
        a = math.pi / 4 * k + rot * math.pi / 8
        for r in (3.6, 4.6):
            f.set(round(cx + math.cos(a) * r), round(cy + math.sin(a) * r), ray)


def draw_moon(f, cx, cy):
    for y in range(H):
        for x in range(W):
            if (x - cx) ** 2 + (y - cy) ** 2 <= 11 and (x - cx - 1.8) ** 2 + (y - cy + 0.6) ** 2 > 7.5:
                f.set(x, y, (230, 230, 150))


def arc(p):
    """p: 0 — за левым нижним углом, 1 — чуть правее левого верхнего угла."""
    th = p * math.pi / 2
    return 7 - 9 * math.cos(th), 17 - 14 * math.sin(th)


def ease(p):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))


def build():
    rnd = random.Random(4)
    stars = [(x, y, rnd.randint(0, 9)) for x, y in
             [(25, 1), (27, 4), (13, 7), (11, 10), (16, 10), (3, 10), (26, 7), (17, 3)]]
    frames, ms = [], []
    zs = []   # (x, y, born) — буквы Z

    def frame(sky, body=None, bed="empty", mx=11, my=2, night=False):
        f = gen.Frame()
        t = len(frames)
        if night:
            for sx, sy, ph in stars:
                if (t // 3 + ph) % 7:
                    f.set(sx, sy, (150, 150, 200))
        # земля
        for x in range(W):
            f.set(x, H - 1, GROUND)
        kind, sx, sy = sky
        if kind == "sun":
            draw_sun(f, sx, sy, t)
        elif kind == "sunset":
            draw_sun(f, sx, sy, t, col=(255, 90, 0))
        elif kind == "moon":
            draw_moon(f, sx, sy)
        draw_bed(f, bed, t)
        if body:
            rows = MAN[body]
            y = 5 if body == "sit" else H - 1 - len(rows) - (1 if body == "jack" else 0)
            f.sprite(rows, mx, y, pal={"r": (255, 30, 30)})
        if bed == "lie" and night:
            # Z z z: вылетают от головы и уплывают вверх-влево, вырастая
            if t % 12 == 0:
                zs.append(t)
            for born in zs:
                age = t - born
                if 0 <= age < 24:
                    big = age >= 9
                    g = zglyph(big)
                    zx = BED_X + 1 - age // 3
                    zy = 8 - age // 3 - len(g) + 1
                    c = (170, 220, 255) if age < 20 else (110, 150, 200)
                    f.sprite([r.replace("#", "Z") for r in g], zx, zy, pal={"Z": c})
        frames.append(f)
        ms.append(100)

    # ---- утро: солнце встаёт, человечек ещё спит
    N_RISE = 16
    for i in range(N_RISE):
        p = ease(i / (N_RISE - 1))
        frame(("sun",) + arc(p), bed="lie", night=False)
    # просыпается: садится, встаёт рядом с кроватью, потягивается
    sun = ("sun",) + arc(1.0)
    for _ in range(4):
        frame(sun, bed="sit", body="sit", mx=BED_X)
    for _ in range(3):
        frame(sun, bed="empty", body="stand", mx=11)
    for _ in range(4):
        frame(sun, bed="empty", body="stretch", mx=11)
    for _ in range(2):
        frame(sun, bed="empty", body="stand", mx=11)
    # зарядка: пара прыжков «звёздочка» — главное тут смена дня и ночи
    for k in range(2):
        for _ in range(3):
            frame(sun, bed="empty", body="jack", mx=11)
        for _ in range(3):
            frame(sun, bed="empty", body="stand", mx=11)
    for _ in range(3):
        frame(sun, bed="empty", body="stand", mx=11)
    # ---- вечер: солнце краснеет и укатывается вниз, человечек ложится
    N_SET = 14
    for i in range(N_SET):
        p = 1 - ease(i / (N_SET - 1))
        kind = "sun" if i < 3 else "sunset"
        if i < 5:
            frame((kind,) + arc(p), bed="empty", body="stretch", mx=11)
        elif i < 9:
            frame((kind,) + arc(p), bed="sit", body="sit", mx=BED_X)
        else:
            frame((kind,) + arc(p), bed="lie")
    # ---- ночь: луна выезжает, Z z z
    N_MOON = 14
    for i in range(N_MOON):
        frame(("moon",) + arc(ease(i / (N_MOON - 1))), bed="lie", night=True)
    moon = ("moon",) + arc(1.0)
    for _ in range(16):
        frame(moon, bed="lie", night=True)
    for i in range(N_MOON):
        frame(("moon",) + arc(1 - ease(i / (N_MOON - 1))), bed="lie", night=i < N_MOON - 4)
    frame(("none", 0, 0), bed="lie")
    gen.save("day_night", frames, ms)


if __name__ == "__main__":
    build()
