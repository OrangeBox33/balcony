#!/usr/bin/env python3
"""Пикачу бьёт молнией лампочку, и она загорается."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

WHITE = (255, 255, 255)
PIKA = {
    "y": (255, 200, 0),
    "K": (120, 60, 0),     # «чёрные» кончики ушей: чёрное на диодах не видно, берём тёмно-коричневый
    "r": (255, 0, 0),      # щёки
        "m": (255, 60, 90),    # открытый рот
}

# лицом к зрителю; глаза — «дырки» (выключенные диоды)
PIKACHU = [
    ".KK.......KK.",
    "..KK.....KK..",
    "..yy.....yy..",
    "...yy...yy...",
    "...yyyyyyy...",
    "..yyyyyyyyy..",
    "..yy.yyy.yy..",
    "..yy.yyy.yy..",
    "..rryyyyyrr..",
    "...yyyyyyy...",
    "..yyyyyyyyy..",
    "...yy...yy...",
]
# радость: рот открыт, лапки вверх
PIKACHU_JOY = [
    ".KK.......KK.",
    "..KK.....KK..",
    "..yy.....yy..",
    "...yy...yy...",
    "y..yyyyyyy..y",
    "y.yyyyyyyyy.y",
    ".yyy.yyy.yyy.",
    "..yy.yyy.yy..",
    "..rryymyyrr..",
    "...yyyyyyy...",
    "...yyyyyyy...",
    "..yy.....yy..",
]
CHEEKS = [(2, 8), (3, 8), (9, 8), (10, 8)]   # в координатах спрайта

BX, BY = 20, 2   # левый верх лампочки
GLASS = [
    "..###..",
    ".#...#.",
    "#.....#",
    "#.....#",
    "#.....#",
    ".#...#.",
    "..#.#..",
]
BASE = [
    "..xxx..",
    "..XXX..",
    "..xxx..",
    "...X...",
]
FILAMENT = [(2, 4), (3, 3), (4, 4)]
STEMS = [(2, 5), (4, 5)]
CX, CY = BX + 3, BY + 3   # центр колбы


def glass_cells():
    out, inner = [], []
    for dy, row in enumerate(GLASS):
        xs = [i for i, c in enumerate(row) if c == "#"]
        out += [(x, dy) for x in xs]
        if len(xs) >= 2:
            inner += [(x, dy) for x in range(xs[0] + 1, xs[-1])]
    return out, inner


OUTLINE, INNER = glass_cells()


def mix(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def draw_bulb(f, light, t):
    """light: 0 — выключена, 1 — горит; между — разгорается/гаснет."""
    off_glass = (110, 120, 160)
    k = min(1.0, light)
    for x, y in OUTLINE:
        f.set(BX + x, BY + y, mix(off_glass, (255, 255, 210), k))
    if light > 0:
        for x, y in INNER:
            f.set(BX + x, BY + y, mix((40, 30, 0), (255, 230, 110), k))
    lit = light > 0.3
    for x, y in FILAMENT:
        f.set(BX + x, BY + y, WHITE if lit else (160, 80, 0))
    for x, y in STEMS:
        f.set(BX + x, BY + y, WHITE if lit else (120, 120, 130))
    f.sprite(BASE, BX, BY + len(GLASS), pal={"x": (160, 160, 170), "X": (100, 100, 110)})
    if light >= 1:
        # лучи сияния: короткие черточки по кругу, «дышат»
        long = (t // 3) % 2 == 0
        col = (255, 220, 60)
        for ang in (180, 140, 220, 100, 60, 20, 0, 320):
            ca, sa = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
            for r in ((5.2, 6.2) if long else (5.2,)):
                f.set(round(CX + ca * r), round(CY + sa * r), col)


def line(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def polyline(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        for c in line(a, b):
            if c not in out:
                out.append(c)
    return out


# зигзаг молнии от щеки Пикачу до колбы: большой размах, чтобы читался как ⚡
BOLT_PATHS = [
    polyline([(12, 10), (14, 4), (16, 9), (18, 4), (19, 5)]),
    polyline([(12, 10), (13, 5), (15, 10), (17, 4), (19, 6)]),
]


def draw_bolt(f, path, length):
    pts = path[:length]
    for x, y in pts:   # жёлтая «тень» справа — толщина 2 пикселя
        if f.px[y][min(x + 1, gen.W - 1)] == gen.BLACK:
            f.set(x + 1, y, (255, 230, 0))
    for x, y in pts:
        f.set(x, y, WHITE)


def build():
    frames, ms = [], []
    PX, PY = 0, 2

    def frame(pose="idle", dy=0, charge=False, bolt=None, light=0.0, flash=False):
        f = gen.Frame()
        t = len(frames)
        rows = PIKACHU_JOY if pose == "joy" else PIKACHU
        f.sprite(rows, PX, PY + dy, pal=PIKA)
        if charge:
            # щёки искрят: вспыхивают белым, вокруг проскакивают искры
            for i, (x, y) in enumerate(CHEEKS):
                if (t + i // 2) % 2 == 0:
                    f.set(PX + x, PY + dy + y, WHITE)
            sparks = [[(1, 10), (12, 7), (12, 10)], [(0, 8), (12, 9), (11, 6)]][t % 2]
            for x, y in sparks:
                f.set(PX + x, PY + dy + y, (255, 255, 160))
        draw_bulb(f, light, t)
        if bolt is not None:
            draw_bolt(f, *bolt)
        if flash:
            for x, y in OUTLINE + INNER:
                f.set(BX + x, BY + y, WHITE)
        frames.append(f)

    def hold(n, dur, **kw):
        for _ in range(n):
            frame(**kw)
            ms.append(dur)

    # 1. спокойно, лампочка тёмная
    hold(8, 120)
    # 2. зарядка: щёки искрят
    hold(10, 90, charge=True)
    # 3. разряд: молния растёт к лампочке
    for n in (4, 9, 14):
        frame(charge=True, bolt=(BOLT_PATHS[0], n))
        ms.append(60)
    # 4. удар: вспышка, мерцающая молния, колба разгорается
    for i in range(8):
        frame(charge=True, bolt=(BOLT_PATHS[i % 2], 99), light=min(1.0, 0.3 + i * 0.12), flash=(i in (0, 2)))
        ms.append(70)
    # 5. лампочка горит, Пикачу радостно прыгает
    for i in range(18):
        frame(pose="joy", dy=[0, -1, -2, -2, -1, 0][i % 6], light=1.0)
        ms.append(90)
    hold(14, 110, pose="joy", light=1.0)
    # 6. гаснет
    for k in (0.7, 0.45, 0.2):
        frame(light=k)
        ms.append(130)
    hold(6, 120)
    gen.save("pikachu_bulb", frames, ms)


if __name__ == "__main__":
    build()
